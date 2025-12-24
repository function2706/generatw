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
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

app = FastAPI(title="Mock A1111 sdapi/v1/txt2img")
app.state.cooldown = 0


class Txt2ImgRequest(BaseModel):
    prompt: Optional[str] = ""
    negative_prompt: Optional[str] = ""
    styles: Optional[List[str]] = None

    seed: Optional[int] = -1
    subseed: Optional[int] = -1
    subseed_strength: Optional[float] = 0.0
    seed_resize_from_h: Optional[int] = -1
    seed_resize_from_w: Optional[int] = -1

    sampler_name: Optional[str] = None
    sampler_index: Optional[str] = None
    scheduler: Optional[str] = None

    batch_size: Optional[int] = Field(default=1, ge=1)
    n_iter: Optional[int] = Field(default=1, ge=1)

    steps: Optional[int] = 20
    cfg_scale: Optional[float] = 7.0
    width: Optional[int] = Field(default=512, ge=1)
    height: Optional[int] = Field(default=512, ge=1)

    restore_faces: Optional[bool] = False
    tiling: Optional[bool] = False

    eta: Optional[float] = None
    s_min_uncond: Optional[float] = 0.0
    s_churn: Optional[float] = 0.0
    s_tmax: Optional[float] = None
    s_tmin: Optional[float] = 0.0
    s_noise: Optional[float] = 1.0

    override_settings: Optional[Dict] = None
    override_settings_restore_afterwards: Optional[bool] = True

    script_args: Optional[List] = None
    script_name: Optional[str] = None

    send_images: Optional[bool] = True
    save_images: Optional[bool] = False

    alwayson_scripts: Optional[Dict] = None


def dumps_info(obj) -> str:
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


@app.post("/sdapi/v1/txt2img")
async def txt2img(req: Txt2ImgRequest):
    cooldown = getattr(app.state, "cooldown", 0)
    if cooldown > 0:
        await asyncio.sleep(cooldown)

    MAX_SIDE = 8192
    width = max(1, min(req.width, MAX_SIDE))
    height = max(1, min(req.height, MAX_SIDE))
    batch_size = max(1, req.batch_size or 1)
    n_iter = max(1, req.n_iter or 1)

    total_images = batch_size * n_iter

    # シード列の決定：seed=-1 なら各画像ごとランダム、>=0 なら連番
    seeds: List[int] = []
    if req.seed is None or req.seed < 0:
        rng_sys = random.SystemRandom()
        seeds = [rng_sys.randint(0, 2**31 - 1) for _ in range(total_images)]
    else:
        seeds = [req.seed + i for i in range(total_images)]

    # 画像生成（単色 + 時刻等）
    images_b64: List[str] = []
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

    infotexts: List[str] = []
    all_prompts: List[str] = []
    all_negative_prompts: List[str] = []
    all_seeds: List[int] = []

    for i in range(total_images):
        seed_val = seeds[i]
        infotexts.append(make_infotext(req, prompt, neg, seed_val, width, height))
        all_prompts.append(prompt)
        all_negative_prompts.append(neg)
        all_seeds.append(seed_val)

    extra_generation_params = {
        "Schedule type": req.scheduler,
    }
    info_obj = {
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

    return {
        "images": images_b64,
        "parameters": parameters,
        "info": dumps_info(info_obj),
    }


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
                continue
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
