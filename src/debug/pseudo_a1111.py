import argparse
import asyncio
import base64
import datetime
import errno
import io
import json
import random
import socket
import time

import uvicorn
from fastapi import FastAPI
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

app = FastAPI(title="Mock A1111 sdapi/v1")
app.state.cooldown = 0
app.state.interrupted = False

# progress 用状態
app.state.active = False
app.state.started_at = 0.0
app.state.sampling_step = 0
app.state.sampling_steps = 0
app.state.job = ""
app.state.job_no = 0
app.state.job_count = 1
app.state.current_image = None

# =========================
# Request Models
# =========================


class Txt2ImgRequest(BaseModel):
    prompt: str | None = ""
    negative_prompt: str | None = ""
    styles: list[str] | None = None

    seed: int | None = -1
    subseed: int | None = -1
    subseed_strength: float | None = 0.0
    seed_resize_from_h: int | None = -1
    seed_resize_from_w: int | None = -1

    sampler_name: str | None = None
    sampler_index: str | None = None
    scheduler: str | None = None

    batch_size: int | None = Field(default=1, ge=1)
    n_iter: int | None = Field(default=1, ge=1)

    steps: int | None = 20
    cfg_scale: float | None = 7.0
    width: int | None = Field(default=512, ge=1)
    height: int | None = Field(default=512, ge=1)

    restore_faces: bool | None = False
    tiling: bool | None = False

    eta: float | None = None
    s_min_uncond: float | None = 0.0
    s_churn: float | None = 0.0
    s_tmax: float | None = None
    s_tmin: float | None = 0.0
    s_noise: float | None = 1.0

    override_settings: dict | None = None
    override_settings_restore_afterwards: bool | None = True

    script_args: list | None = None
    script_name: str | None = None

    send_images: bool | None = True
    save_images: bool | None = False

    alwayson_scripts: dict | None = None


class Img2ImgRequest(Txt2ImgRequest):
    init_images: list[str]
    denoising_strength: float | None = Field(default=0.75, ge=0.0, le=1.0)
    resize_mode: int | None = 0
    mask: str | None = None
    inpainting_fill: int | None = 0
    inpaint_full_res: bool | None = True
    inpaint_full_res_padding: int | None = 32


# =========================
# Utilities
# =========================


def dump_infos(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


def make_infotext(
    req: Txt2ImgRequest, prompt: str, neg: str, seed_val: int, width: int, height: int
) -> str:
    sampler = req.sampler_name or req.sampler_index or ""
    line = (
        f"{prompt}\n"
        f"Negative prompt: {neg}\n"
        f"Steps: {req.steps}, Sampler: {sampler}, CFG scale: {req.cfg_scale}, "
        f"Seed: {seed_val}, Size: {width}x{height}"
    )
    if req.scheduler:
        line += f", Scheduler: {req.scheduler}"
    return line


async def interruptible_sleep(seconds: float):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if app.state.interrupted:
            return False
        await asyncio.sleep(0.1)
    return True


# =========================
# API Endpoints
# =========================


@app.post("/sdapi/v1/interrupt")
async def interrupt():
    app.state.interrupted = True
    return {"status": "interrupted"}


@app.get("/sdapi/v1/progress")
async def progress():
    if not app.state.active:
        return {
            "progress": 0.0,
            "eta_relative": 0.0,
            "state": {
                "skipped": False,
                "interrupted": app.state.interrupted,
                "job": "",
                "job_no": 0,
                "job_count": 0,
                "sampling_step": 0,
                "sampling_steps": 0,
            },
            "current_image": None,
        }

    step = app.state.sampling_step
    steps = max(1, app.state.sampling_steps)
    progress = step / steps

    elapsed = time.time() - app.state.started_at
    eta = elapsed * (1.0 - progress) / progress if progress > 0 else 0.0

    return {
        "progress": progress,
        "eta_relative": eta,
        "state": {
            "skipped": False,
            "interrupted": app.state.interrupted,
            "job": app.state.job,
            "job_no": app.state.job_no,
            "job_count": app.state.job_count,
            "sampling_step": step,
            "sampling_steps": steps,
        },
        "current_image": app.state.current_image,
    }


@app.post("/sdapi/v1/txt2img")
async def txt2img(req: Txt2ImgRequest):
    app.state.active = True
    app.state.interrupted = False
    app.state.started_at = time.time()
    app.state.sampling_step = 0
    app.state.sampling_steps = req.steps or 20
    app.state.job = "txt2img"

    MAX_SIDE = 8192
    width = max(1, min(req.width, MAX_SIDE))
    height = max(1, min(req.height, MAX_SIDE))
    batch_size = max(1, req.batch_size or 1)
    n_iter = max(1, req.n_iter or 1)

    total_images = batch_size * n_iter

    # シード列の決定：seed=-1 なら各画像ごとランダム、>=0 なら連番
    seeds: list[int] = []
    if req.seed is None or req.seed < 0:
        rng_sys = random.SystemRandom()
        seeds = [rng_sys.randint(0, 2**31 - 1) for _ in range(total_images)]
    else:
        seeds = [req.seed + i for i in range(total_images)]

    # sampling loop (once per job)
    for step in range(app.state.sampling_steps):
        if app.state.interrupted:
            app.state.active = False
            return {"images": [], "info": "{}"}

        app.state.sampling_step = step + 1
        cooldown = float(getattr(app.state, "cooldown", 0)) / app.state.sampling_steps
        await asyncio.sleep(cooldown)

    # 画像生成（単色 + 時刻等）
    images_b64: list[str] = []
    for idx, s in enumerate(seeds):
        rng = random.Random(s)
        color = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
        img = Image.new("RGB", (width, height), color=color)

        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except IOError:
            font = ImageFont.load_default()
        draw = ImageDraw.Draw(img)
        text = f"{idx=}, seed={s}, time={datetime.datetime.now().strftime('%H:%M:%S')}"
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((10 + dx, 10 + dy), text, fill=(0, 0, 0), font=font)
        draw.text((10, 10), text, fill=(255, 255, 255), font=font)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        b64 = base64.b64encode(png_bytes).decode("ascii")
        images_b64.append(b64)

    prompt = req.prompt or ""
    neg = req.negative_prompt or ""

    infotexts: list[str] = []
    all_prompts: list[str] = []
    all_negative_prompts: list[str] = []
    all_seeds: list[int] = []

    for i in range(total_images):
        seed_val = seeds[i]
        infotexts.append(make_infotext(req, prompt, neg, seed_val, width, height))
        all_prompts.append(prompt)
        all_negative_prompts.append(neg)
        all_seeds.append(seed_val)

    extra_generation_params = {
        "Schedule type": req.scheduler,
    }
    infos = {
        "prompts": prompt,
        "all_prompts": all_prompts,
        "negative_prompt": neg,
        "all_negative_prompts": all_negative_prompts,
        "seed": seeds[0],
        "all_seeds": all_seeds,
        "subseed": seeds[0],
        "all_subseeds": all_seeds,
        "subseed_strength": 0,
        "width": width,
        "height": height,
        "sampler_name": req.sampler_name or req.sampler_index,
        "cfg_scale": req.cfg_scale,
        "steps": req.steps,
        "n_iter": n_iter,
        "batch_size": batch_size,
        "sd_model_name": "Foobar_Hogefuga",
        "sd_model_hash": "12345abcde",
        "extra_generation_params": extra_generation_params,
        "index_of_first_image": 0,
        "infotexts": infotexts,
        "job_timestamp": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        "clip_skip": 2,
        "version": "v1.10.1",
    }

    # parameters は A1111 と同名キーで返す
    parameters = req.model_dump()

    app.state.active = False

    return {
        "images": images_b64,
        "parameters": parameters,
        "info": dump_infos(infos),
    }


@app.post("/sdapi/v1/img2img")
async def img2img(req: Img2ImgRequest):
    app.state.active = True
    app.state.interrupted = False
    app.state.started_at = time.time()
    app.state.sampling_step = 0
    app.state.sampling_steps = req.steps or 20
    app.state.job = "img2img"

    try:
        init_bytes = base64.b64decode(req.init_images[0])
        base_img = Image.open(io.BytesIO(init_bytes)).convert("RGB")
    except Exception as e:
        return {"error": f"invalid init_images: {e}"}

    width, height = base_img.size
    batch_size = max(1, req.batch_size or 1)
    n_iter = max(1, req.n_iter or 1)
    total_images = batch_size * n_iter

    if req.seed is None or req.seed < 0:
        rng_sys = random.SystemRandom()
        seeds = [rng_sys.randint(0, 2**31 - 1) for _ in range(total_images)]
    else:
        seeds = [req.seed + i for i in range(total_images)]

    images_b64: list[str] = []

    # sampling loop (once per job)
    for step in range(app.state.sampling_steps):
        if app.state.interrupted:
            app.state.active = False
            return {"images": [], "info": "{}"}

        app.state.sampling_step = step + 1
        cooldown = float(getattr(app.state, "cooldown", 0)) / app.state.sampling_steps
        await asyncio.sleep(cooldown)

    for idx, s in enumerate(seeds):
        img = base_img.copy()
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except IOError:
            font = ImageFont.load_default()

        draw.text(
            (10, 10),
            f"img2img idx={idx}\nseed={s}\ndenoise={req.denoising_strength}",
            fill=(255, 255, 255),
            font=font,
        )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        images_b64.append(base64.b64encode(buf.getvalue()).decode("ascii"))

    prompt = req.prompt or ""
    neg = req.negative_prompt or ""

    infotexts: list[str] = []
    all_prompts: list[str] = []
    all_negative_prompts: list[str] = []

    for i in range(total_images):
        seed_val = seeds[i]
        infotexts.append(
            make_infotext(req, prompt, neg, seed_val, width, height)
            + f", Denoising strength: {req.denoising_strength}"
        )
        all_prompts.append(prompt)
        all_negative_prompts.append(neg)

    extra_generation_params = {
        "Schedule type": req.scheduler,
    }
    infos = {
        "prompt": prompt,
        "all_prompts": all_prompts,
        "negative_prompt": neg,
        "all_negative_prompts": all_negative_prompts,
        "seed": seeds[0],
        "all_seeds": seeds,
        "subseed": seeds[0],
        "all_subseeds": seeds,
        "subseed_strength": 0,
        "width": width,
        "height": height,
        "denoising_strength": req.denoising_strength,
        "sampler_name": req.sampler_name or req.sampler_index,
        "cfg_scale": req.cfg_scale,
        "steps": req.steps,
        "n_iter": n_iter,
        "batch_size": batch_size,
        "sd_model_name": "Foobar_Hogefuga",
        "sd_model_hash": "12345abcde",
        "extra_generation_params": extra_generation_params,
        "index_of_first_image": 0,
        "infotexts": infotexts,
        "job_timestamp": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        "clip_skip": 2,
        "version": "v1.10.1",
    }

    app.state.active = False

    return {
        "images": images_b64,
        "parameters": req.model_dump(),
        "info": dump_infos(infos),
    }


# =========================
# Server bootstrap
# =========================


def find_available_port(host, port):
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                return s.getsockname()[1]
        except OSError as e:
            if e.errno in (errno.EADDRINUSE, 10013, 10048):
                print(f"Port {port} is in use. Trying another port...")
                port = 0
                time.sleep(0.1)
            else:
                raise


def run_uvicorn_until_success(app, host="127.0.0.1", initial_port=None):
    port = find_available_port(host, initial_port or 0)
    print(f"Starting uvicorn on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="pseudo_a1111.py",
        description="A1111 Pseudo Server",
        epilog="ex: pseudo_a1111.py -s 127.0.0.1 -p 7860 -c 5",
    )
    parser.add_argument("-s", "--server", default="127.0.0.1", help="A1111 IP Addr")
    parser.add_argument("-p", "--port", type=int, default=7860, help="A1111 Port")
    parser.add_argument("-c", "--cooldown", type=int, default=0, help="Cooldown Time")
    args = parser.parse_args()
    app.state.cooldown = args.cooldown
    run_uvicorn_until_success(app, args.server, args.port)
