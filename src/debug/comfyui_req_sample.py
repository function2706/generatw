import io
import json
import random
import uuid

import requests
import websocket
from PIL import Image

COMFY_URL = "127.0.0.1:8188"
client_id = str(uuid.uuid4())


# ワークフロー定義
def get_workflow(pos, neg):
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "Illustrious\\waiNSFWIllustrious_v150.safetensors"},
        },
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": pos, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["1", 1]}},
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 512, "height": 768, "batch_size": 1},
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
                "seed": random.randint(0, 2**31 - 1),
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2s_ancestral",
                "scheduler": "karras",
                "denoise": 1.0,
            },
        },
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "PreviewImage", "inputs": {"images": ["6", 0]}},  # PreviewImageを使用
    }


def generate_and_show():
    ws = websocket.WebSocket()
    ws.connect(f"ws://{COMFY_URL}/ws?clientId={client_id}")

    pos = "remilia scarlet, smirk, masterpiece, best quality"
    neg = "bad quality, worst quality"

    workflow = get_workflow(pos, neg)

    print("Generating image...")
    res = requests.post(
        f"http://{COMFY_URL}/prompt", json={"prompt": workflow, "client_id": client_id}
    ).json()
    prompt_id = res["prompt_id"]

    final_images = []

    try:
        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                # ★ 進捗状況の取得
                if message["type"] == "progress":
                    value = message["data"]["value"]
                    max_steps = message["data"]["max"]
                    percent = (value / max_steps) * 100
                    print(f"\rProgress: {percent:3.0f}% | Step: {value}/{max_steps}", end="")

                # 各ノードの実行開始時（どのノードが動いているか表示）
                if message["type"] == "executing":
                    node_id = message["data"]["node"]
                    if node_id:
                        # 実行中のノードIDを表示（任意）
                        # print(f"\nExecuting node: {node_id}")
                        pass
                    elif message["data"]["prompt_id"] == prompt_id:
                        print("\nDone!")
                        break
                # ノードの実行完了通知を監視
                if message["type"] == "executed":
                    if "images" in message["data"]["output"]:
                        # 完了したノードから画像情報を抽出
                        for img_info in message["data"]["output"]["images"]:
                            final_images.append(img_info)

                # 全行程の終了
                if message["type"] == "executing" and message["data"]["node"] is None:
                    break
    finally:
        ws.close()

    # 取得した画像情報を元に、API経由でバイナリを直接取得（ファイル保存はされない）
    # 取得した画像情報を元に、API経由でバイナリを直接取得
    if final_images:
        for img_info in final_images:
            filename = img_info["filename"]
            subfolder = img_info["subfolder"]
            folder_type = img_info["type"]

            view_url = f"http://{COMFY_URL}/view?filename={filename}&subfolder={subfolder}&type={folder_type}"
            img_res = requests.get(view_url)

            if img_res.status_code == 200:
                # バイナリから画像を開く
                img = Image.open(io.BytesIO(img_res.content))

                # --- PNGメタデータからの抽出 ---
                # ComfyUIは "prompt" キーに全設定をJSON文字列で埋め込んでいる
                metadata_raw = img.info.get("prompt")

                if metadata_raw:
                    metadata = json.loads(metadata_raw)
                    print(json.dumps(metadata, indent=2))
                    print("\n--- Metadata from PNG Chunk ---")

                    # 各ノードの情報を取得（ワークフローに合わせてIDを指定）
                    pos_text = metadata.get("2", {}).get("inputs", {}).get("text", "N/A")
                    seed_val = metadata.get("5", {}).get("inputs", {}).get("seed", "N/A")

                    print(f"Prompt: {pos_text}")
                    print(f"Seed: {seed_val}")
                    print("-------------------------------\n")
                else:
                    print("No metadata found in PNG.")

                img.show()
                print(f"Successfully displayed: {filename}")
    else:
        print("No image data received.")


if __name__ == "__main__":
    generate_and_show()
