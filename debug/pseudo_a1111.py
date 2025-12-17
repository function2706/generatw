
# filename: mock_a1111_txt2img.py
# -*- coding: utf-8 -*-
from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field
from PIL import Image
import io
import base64
import random
import uvicorn
import json
import datetime

app = FastAPI(title="Mock A1111 sdapi/v1/txt2img")

# A1111 に寄せたリクエストモデル（主要フィールドのみ）
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
    sampler_index: Optional[str] = None  # 一部クライアントは index を使う
    scheduler: Optional[str] = None

    batch_size: Optional[int] = Field(default=1, ge=1)  # 1回のバッチ内枚数
    n_iter: Optional[int] = Field(default=1, ge=1)      # バッチの繰り返し回数

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

    override_settings: Optional[dict] = None
    override_settings_restore_afterwards: Optional[bool] = True

    script_args: Optional[List] = None
    script_name: Optional[str] = None

    send_images: Optional[bool] = True
    save_images: Optional[bool] = False

    alwayson_scripts: Optional[dict] = None

def dumps_info(obj) -> str:
    # A1111 は info を JSON 文字列で返す
    return json.dumps(obj, ensure_ascii=False)

def make_infotext(
    req: Txt2ImgRequest, prompt: str, neg: str, seed_val: int, width: int, height: int
) -> str:
    # 実機 PNG Info の1行目に近いレイアウト（最小限）
    # 例: "<prompt>\nNegative prompt: <neg>\nSteps: <steps>, Sampler: <sampler>, CFG scale: <cfg>, Seed: <seed>, Size: <W>x<H>, Model hash: <...>, Model: <...>"
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
def txt2img(req: Txt2ImgRequest):
    # サイズ安全化（上限は適当に設定）
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

    # 画像生成（単色）
    images_b64: List[str] = []
    for s in seeds:
        rng = random.Random(s)
        color = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
        img = Image.new("RGB", (width, height), color=color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        b64 = base64.b64encode(png_bytes).decode("ascii")
        images_b64.append(b64)

    # info（JSON 文字列）構築：A1111 の項目名に合わせる
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

    # A1111 互換フィールド（最低限 + よくある拡張）
    info_obj = {
        "infotexts": infotexts,
        "all_prompts": all_prompts,
        "all_negative_prompts": all_negative_prompts,
        "all_seeds": all_seeds,

        # 参考までに付加（UIの progress/state と合わせやすい）
        "job_timestamp": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        "batch_size": batch_size,
        "n_iter": n_iter,
        "width": width,
        "height": height,
        "steps": req.steps,
        "sampler_name": req.sampler_name or req.sampler_index,
        "scheduler": req.scheduler,
        "cfg_scale": req.cfg_scale,
    }

    # parameters は A1111 と同名キーで返す
    parameters = req.dict()

    return {
        "images": images_b64,
        "parameters": parameters,
        "info": dumps_info(info_obj),
    }

if __name__ == "__main__":
    # 127.0.0.1:7860 で待受（A1111 と同じ既定ポート）
    uvicorn.run(app, host="127.0.0.1", port=7860)
