import io
import json
import random
import time
import uuid

import requests
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
        "7": {"class_type": "PreviewImage", "inputs": {"images": ["6", 0]}},
    }


def wait_for_history(prompt_id, timeout=120):
    """history に prompt_id が現れるまで待つ"""
    start = time.time()
    while True:
        history = requests.get(f"http://{COMFY_URL}/history/{prompt_id}").json()
        if prompt_id in history:
            return history[prompt_id]

        if time.time() - start > timeout:
            raise TimeoutError("Timeout waiting for history result")

        time.sleep(0.5)


def generate_and_show():
    pos = "remilia scarlet, smirk, masterpiece, best quality"
    neg = "bad quality, worst quality"

    workflow = get_workflow(pos, neg)

    print("Sending prompt...")
    res = requests.post(
        f"http://{COMFY_URL}/prompt",
        json={"prompt": workflow, "client_id": client_id},
    ).json()

    prompt_id = res["prompt_id"]
    print(f"Prompt ID: {prompt_id}")

    print("Waiting for result (via /history)...")
    result = wait_for_history(prompt_id)

    outputs = result.get("outputs", {})
    final_images = []

    # 画像ノードの出力を収集
    for _, out in outputs.items():
        if "images" in out:
            final_images.extend(out["images"])

    if not final_images:
        print("No images found in history.")
        return

    # 画像を取得して表示
    for img_info in final_images:
        filename = img_info["filename"]
        subfolder = img_info["subfolder"]
        folder_type = img_info["type"]

        view_url = (
            f"http://{COMFY_URL}/view?filename={filename}&subfolder={subfolder}&type={folder_type}"
        )

        img_res = requests.get(view_url)
        img = Image.open(io.BytesIO(img_res.content))

        # PNG メタデータ抽出
        metadata_raw = img.info.get("prompt")
        if metadata_raw:
            metadata = json.loads(metadata_raw)
            print(json.dumps(metadata, indent=2))

            pos_text = metadata.get("2", {}).get("inputs", {}).get("text", "N/A")
            seed_val = metadata.get("5", {}).get("inputs", {}).get("seed", "N/A")

            print("\n--- Metadata from PNG Chunk ---")
            print(f"Prompt: {pos_text}")
            print(f"Seed: {seed_val}")
            print("-------------------------------\n")

        img.show()
        print(f"Displayed: {filename}")


if __name__ == "__main__":
    generate_and_show()
