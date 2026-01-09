import argparse
import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict

import requests


def dump(obj: Any):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def post(url: str, payload: Dict[str, Any]):
    print(f"\n=== POST {url} ===")
    print("--- request ---")
    dump(payload)

    r = requests.post(url, json=payload, timeout=30)
    print(f"\n--- response ({r.status_code}) ---")

    try:
        dump(r.json())
    except Exception:
        print(r.text)


def txt2img(base_url: str):
    payload = {
        "prompt": "debug test prompt",
        "negative_prompt": "low quality",
        "steps": 20,
        "width": 512,
        "height": 512,
        "batch_size": 1,
        "n_iter": 1,
        "seed": -1,
    }
    post(f"{base_url}/sdapi/v1/txt2img", payload)


def img2img(base_url: str, image_path: Path):
    img_bytes = image_path.read_bytes()
    img_b64 = base64.b64encode(img_bytes).decode("ascii")

    payload = {
        "prompt": "img2img debug",
        "negative_prompt": "",
        "init_images": [img_b64],
        "denoising_strength": 0.75,
        "steps": 20,
        "seed": -1,
    }
    post(f"{base_url}/sdapi/v1/img2img", payload)


def interrupt(base_url: str):
    post(f"{base_url}/sdapi/v1/interrupt", {})


def main():
    parser = argparse.ArgumentParser("pseudo_a1111_client")
    parser.add_argument("--url", default="http://127.0.0.1:7860")
    parser.add_argument("--mode", choices=["txt2img", "img2img", "interrupt"], required=True)
    parser.add_argument("--image", help="init image for img2img")
    args = parser.parse_args()

    if args.mode == "txt2img":
        txt2img(args.url)
    elif args.mode == "img2img":
        if not args.image:
            print("--image is required for img2img", file=sys.stderr)
            sys.exit(1)
        img2img(args.url, Path(args.image))
    elif args.mode == "interrupt":
        interrupt(args.url)


if __name__ == "__main__":
    main()
