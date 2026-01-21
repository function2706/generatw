import asyncio
import datetime
import json
import random
import uuid
from io import BytesIO
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

app = FastAPI(title="Mock ComfyUI sdapi/v1")

PROMPTS: Dict[str, Any] = {}
IMAGES: Dict[str, bytes] = {}
WS_CLIENTS: Dict[str, WebSocket] = {}
RUNNING_TASKS: Dict[str, asyncio.Task] = {}


@app.post("/prompt")
async def prompt(req: Dict[str, Any]):
    prompt = req.get("prompt", {})
    client_id = req.get("client_id")
    prompt_id = str(uuid.uuid4())

    PROMPTS[prompt_id] = {
        "prompt": prompt,
        "client_id": client_id,
        "status": "running",
        "outputs": {},
    }

    task = asyncio.create_task(simulate_generation(prompt_id))
    RUNNING_TASKS[prompt_id] = task

    task.add_done_callback(lambda t: RUNNING_TASKS.pop(prompt_id, None))

    return {"prompt_id": prompt_id}


@app.post("/interrupt")
async def interrupt():
    if not RUNNING_TASKS:
        return {"message": "No active tasks to interrupt"}

    for _, task in RUNNING_TASKS.items():
        if not task.done():
            task.cancel()

    return {"message": "Interrupted all tasks"}


def find_nodes(data: dict, class_type: str):
    """
    条件に一致する (key, value) をリストで返す
    """
    return [
        (key, value)
        for key, value in data.items()
        if isinstance(value, dict) and value.get("class_type") == class_type
    ]


async def simulate_generation(prompt_id: str):
    """ComfyUI の WebSocket イベントを模倣する"""
    try:
        prompt = PROMPTS[prompt_id]["prompt"]
        client_id = PROMPTS[prompt_id]["client_id"]
        ws = WS_CLIENTS.get(client_id)

        ksampler_id, ksampler = find_nodes(prompt, "KSampler")[0]
        _, empty_latent_image = find_nodes(prompt, "EmptyLatentImage")[0]
        preview_image_id, _ = find_nodes(prompt, "PreviewImage")[0]

        seed = ksampler["inputs"]["seed"]
        steps = ksampler["inputs"]["steps"]
        for step in range(1, steps + 1):
            await asyncio.sleep(0.1)
            if ws:
                await ws.send_json({"type": "progress", "data": {"value": step, "max": 20}})

        if ws:
            await ws.send_json(
                {"type": "executing", "data": {"node": ksampler_id, "prompt_id": prompt_id}}
            )

        await asyncio.sleep(0.3)

        seeds: list[int] = []
        batch_size = empty_latent_image["inputs"]["batch_size"]
        width = empty_latent_image["inputs"]["width"]
        height = empty_latent_image["inputs"]["height"]
        seeds = [seed + i for i in range(batch_size)]
        images = []
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

            meta = PngImagePlugin.PngInfo()
            meta.add_text("prompt", json.dumps(prompt))

            buffer = BytesIO()
            img.save(buffer, format="PNG", pnginfo=meta)
            buffer.seek(0)

            filename = f"{uuid.uuid4()}.png"
            IMAGES[filename] = buffer.getvalue()

            images.append({"filename": filename, "subfolder": "", "type": "output"})

        # PreviewImage ノードの出力として複数画像を返す
        PROMPTS[prompt_id]["outputs"] = {preview_image_id: {"images": images}}

        if ws:
            await ws.send_json(
                {
                    "type": "executed",
                    "data": {
                        "node": preview_image_id,
                        "output": PROMPTS[prompt_id]["outputs"][preview_image_id],
                    },
                }
            )

        # ---- 全行程終了（node=None） ----
        if ws:
            await ws.send_json(
                {"type": "executing", "data": {"node": None, "prompt_id": prompt_id}}
            )

        PROMPTS[prompt_id]["status"] = "success"
    except asyncio.CancelledError:
        # 5. 中断された時の処理
        print(f"Task {prompt_id} was interrupted.")
        PROMPTS[prompt_id]["status"] = "interrupted"

        # 必要に応じて中断したことをWSクライアントに通知
        ws = WS_CLIENTS.get(client_id)
        if ws:
            await ws.send_json(
                {"type": "executing", "data": {"node": None, "prompt_id": prompt_id}}
            )
        raise


@app.get("/history/{prompt_id}")
async def history(prompt_id: str):
    if prompt_id in PROMPTS and PROMPTS[prompt_id]["status"] == "success":
        return {
            prompt_id: {
                "prompt": PROMPTS[prompt_id]["prompt"],
                "outputs": PROMPTS[prompt_id]["outputs"],
                "status": {"status_str": "success", "completed": True, "messages": []},
            }
        }
    return {}


@app.get("/view")
async def view(filename: str, subfolder: str = "", type: str = "output"):
    if filename in IMAGES:
        return StreamingResponse(BytesIO(IMAGES[filename]), media_type="image/png")
    return "Not Found"


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    # clientId を取得
    query = ws.scope.get("query_string", b"").decode()
    params = dict(q.split("=") for q in query.split("&") if "=" in q)
    client_id = params.get("clientId")

    if client_id:
        WS_CLIENTS[client_id] = ws

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if client_id in WS_CLIENTS:
            del WS_CLIENTS[client_id]


if __name__ == "__main__":
    print("Fake ComfyUI server running at http://127.0.0.1:8188")
    uvicorn.run(app, host="127.0.0.1", port=8188)
