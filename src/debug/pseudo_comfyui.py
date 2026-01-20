import asyncio
import json
import uuid
from io import BytesIO
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from PIL import Image, PngImagePlugin

app = FastAPI()

# メモリ上の疑似データ
PROMPTS: Dict[str, Any] = {}
IMAGES: Dict[str, bytes] = {}
WS_CLIENTS: Dict[str, WebSocket] = {}


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

    # 非同期で生成処理
    asyncio.create_task(simulate_generation(prompt_id))

    return {"prompt_id": prompt_id}


async def simulate_generation(prompt_id: str):
    """ComfyUI の WebSocket イベントを模倣する"""
    prompt = PROMPTS[prompt_id]["prompt"]
    client_id = PROMPTS[prompt_id]["client_id"]
    ws = WS_CLIENTS.get(client_id)

    # ---- progress イベント ----
    for step in range(1, 21):
        await asyncio.sleep(0.05)
        if ws:
            await ws.send_json({"type": "progress", "data": {"value": step, "max": 20}})

    # ---- executing ノード通知 ----
    if ws:
        await ws.send_json({"type": "executing", "data": {"node": "5", "prompt_id": prompt_id}})

    await asyncio.sleep(0.3)

    # ---- executed（画像生成完了） ----
    img = Image.new("RGB", (512, 768), (0, 0, 0))

    meta = PngImagePlugin.PngInfo()
    meta.add_text("prompt", json.dumps(prompt))

    buffer = BytesIO()
    img.save(buffer, format="PNG", pnginfo=meta)
    buffer.seek(0)

    filename = f"{uuid.uuid4()}.png"
    IMAGES[filename] = buffer.getvalue()

    PROMPTS[prompt_id]["outputs"] = {
        "7": {"images": [{"filename": filename, "subfolder": "", "type": "output"}]}
    }

    if ws:
        await ws.send_json(
            {
                "type": "executed",
                "data": {"node": "7", "output": PROMPTS[prompt_id]["outputs"]["7"]},
            }
        )

    # ---- 全行程終了（node=None） ----
    if ws:
        await ws.send_json({"type": "executing", "data": {"node": None, "prompt_id": prompt_id}})

    PROMPTS[prompt_id]["status"] = "success"


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
