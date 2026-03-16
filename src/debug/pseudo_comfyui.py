import argparse
import asyncio
import datetime
import json
import random
import uuid
from io import BytesIO
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

app = FastAPI(title="Mock ComfyUI sdapi/v1")
app.state.cooldown = 0

PROMPTS: dict[str, Any] = {}
IMAGES: dict[str, bytes] = {}
WS_CLIENTS: dict[str, WebSocket] = {}
RUNNING_TASKS: dict[str, asyncio.Task] = {}


@app.post("/prompt")
async def prompt(req: dict[str, Any]):
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
    RUNNING_TASKS.setdefault(client_id, {})[prompt_id] = task

    task.add_done_callback(lambda t: RUNNING_TASKS.pop(prompt_id, None))

    return {"prompt_id": prompt_id}


@app.post("/interrupt")
async def interrupt():
    for tasks in RUNNING_TASKS.values():
        for task in tasks.values():
            task.cancel()
    return {"message": "ok"}


def find_nodes(data: dict, class_type: str):
    """
    条件に一致する (key, value) をリストで返す
    """
    return [
        (key, value)
        for key, value in data.items()
        if isinstance(value, dict) and value.get("class_type") == class_type
    ]


def gen_images(width: int, height: int, batch_size: int, top_seed: int, prompt) -> list[dict]:
    seeds = [top_seed + i for i in range(batch_size)]
    images: list[dict] = []

    for idx, s in enumerate(seeds):
        rng = random.Random(s)
        color = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
        img = Image.new("RGB", (width, height), color=color)
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except OSError:
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

    return images


def upscale(path: str, new_width: int, new_height: int, prompt) -> list[dict]:
    img = Image.open(path)
    w, h = img.size
    resized = img.resize((new_width, new_height), Image.LANCZOS)

    meta = PngImagePlugin.PngInfo()
    meta.add_text("prompt", json.dumps(prompt))
    buffer = BytesIO()
    resized.save(buffer, format="PNG", pnginfo=meta)
    buffer.seek(0)
    filename = f"{uuid.uuid4()}.png"
    IMAGES[filename] = buffer.getvalue()
    return [{"filename": filename, "subfolder": "", "type": "output"}]


async def simulate_generation(prompt_id: str):
    """ComfyUI の WebSocket イベントを模倣する"""
    try:
        prompt = PROMPTS[prompt_id]["prompt"]
        client_id = PROMPTS[prompt_id]["client_id"]

        def get_ws():
            return WS_CLIENTS.get(client_id)

        # WebSocket接続を待機（最大5秒）
        ws = None
        for _ in range(50):  # 5秒間待機（0.1秒 × 50回）
            ws = WS_CLIENTS.get(client_id)
            if ws is not None:
                break
            await asyncio.sleep(0.1)

        if ws is None:
            print("[WARNING] WebSocket not found after 5s, continuing without WS notifications")

        ksampler_nodes = find_nodes(prompt, "KSampler")
        empty_latent_nodes = find_nodes(prompt, "EmptyLatentImage")
        preview_nodes = find_nodes(prompt, "PreviewImage")
        load_image_nodes = find_nodes(prompt, "UnlimitLoadImage")
        latent_upscale_nodes = find_nodes(prompt, "LatentUpscale")

        if not ksampler_nodes or not preview_nodes:
            print("[ERROR] Missing required nodes in workflow")
            return

        ksampler_id, ksampler = ksampler_nodes[0]
        preview_image_id, _ = preview_nodes[0]

        seed = ksampler["inputs"]["seed"]
        steps = ksampler["inputs"]["steps"]
        cooldown = float(getattr(app.state, "cooldown", 0)) / steps

        # プログレスバーの送信
        for step in range(1, steps + 1):
            await asyncio.sleep(cooldown)
            ws = get_ws()
            if ws:
                try:
                    await ws.send_json({"type": "progress", "data": {"value": step, "max": steps}})
                except Exception as e:
                    print(f"[WARNING] Failed to send progress (client disconnected): {e}")
                    ws = None

        ws = get_ws()
        if ws:
            try:
                await ws.send_json(
                    {"type": "executing", "data": {"node": ksampler_id, "prompt_id": prompt_id}}
                )
            except Exception as e:
                print(f"[WARNING] Failed to send executing message: {e}")
                ws = None

        await asyncio.sleep(0.3)

        # 画像生成 or 拡大
        if empty_latent_nodes:
            _, empty_latent_image = empty_latent_nodes[0]
            batch_size = empty_latent_image["inputs"]["batch_size"]
            width = empty_latent_image["inputs"]["width"] & -8
            height = empty_latent_image["inputs"]["height"] & -8
            images = gen_images(width, height, batch_size, seed, prompt)
        elif load_image_nodes and latent_upscale_nodes:
            _, load_image = load_image_nodes[0]
            _, latent_upscale = latent_upscale_nodes[0]
            path = load_image["inputs"]["path"]
            width = latent_upscale["inputs"]["width"]
            height = latent_upscale["inputs"]["height"]
            images = upscale(path, width, height, prompt)
        else:
            print("[ERROR] Missing required nodes in workflow on generating or upscaling")
            return

        # PreviewImage ノードの出力として複数画像を返す
        PROMPTS[prompt_id]["outputs"] = {preview_image_id: {"images": images}}

        ws = get_ws()
        if ws:
            try:
                await ws.send_json(
                    {
                        "type": "executed",
                        "data": {
                            "node": preview_image_id,
                            "output": PROMPTS[prompt_id]["outputs"][preview_image_id],
                        },
                    }
                )
            except Exception as e:
                print(f"[WARNING] Failed to send executed message: {e}")
                ws = None

        # 全行程終了（node=-1 で完了を示す。Noneはクライアント側で int() エラーになるため）
        if ws:
            try:
                await ws.send_json(
                    {"type": "executing", "data": {"node": -1, "prompt_id": prompt_id}}
                )
            except Exception as e:
                print(f"[WARNING] Failed to send completion message: {e}")

        PROMPTS[prompt_id]["status"] = "success"
    except asyncio.CancelledError:
        PROMPTS[prompt_id]["status"] = "interrupted"
        client_id = PROMPTS[prompt_id]["client_id"]
        raise

    except Exception as e:
        print(f"[ERROR] Unexpected error in simulate_generation: {e}")
        import traceback

        traceback.print_exc()
        PROMPTS[prompt_id]["status"] = "error"


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
            try:
                await asyncio.wait_for(ws.receive_text(), timeout=1.0)
            except TimeoutError:
                continue
    except WebSocketDisconnect:
        print(f"[DEBUG] WebSocket disconnected: {client_id}")
    except Exception as e:
        print(f"[ERROR] WebSocket error for client {client_id}: {e}")
    finally:
        if client_id in WS_CLIENTS:
            del WS_CLIENTS[client_id]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="pseudo_comfyui.py",
        description="ComfyUI Pseudo Server",
        epilog="ex: pseudo_comfyui.py -s 127.0.0.1 -p 8188 -c 5",
    )
    parser.add_argument("-s", "--server", default="127.0.0.1", help="ComfyUI IP Addr")
    parser.add_argument("-p", "--port", type=int, default=8188, help="ComfyUI Port")
    parser.add_argument("-c", "--cooldown", type=int, default=0, help="Cooldown Time")
    args = parser.parse_args()
    app.state.cooldown = args.cooldown

    print(f"Starting uvicorn on {args.server}:{args.port}")
    uvicorn.run(app, host=args.server, port=args.port)
