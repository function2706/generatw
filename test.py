import requests
from PIL import Image
import base64
import io
import os

url = "http://127.0.0.1:7860"
payload = {
    "prompt": "puppy dog",
    "steps": 5
}

response = requests.post(f"{url}/sdapi/v1/txt2img", json=payload)
image_data = response.json()["images"][0]

# 画像保存
image = Image.open(io.BytesIO(base64.b64decode(image_data)))
image.save("output.png")
os.startfile("output.png")
