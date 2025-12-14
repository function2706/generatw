import tkinter as tk
from PIL import Image, ImageTk
from typing import Dict
from chara_tbl import chara_tbl
import io, base64, requests, json, re, pyperclip, copy, signal, sys

url = "http://127.0.0.1:7860"

# Global
root = tk.Tk()
root.title("eragen")
label = tk.Label(root)
label.pack()

# SIGINT ハンドラ
def sigint_handler(sig, frame):
    print("\n終了します。")
    root.destroy()
    sys.exit(0)

# text からメタステータスを取得し, 返す
def get_metastats(text: str, data: Dict[str, str]) -> Dict[str, str]:
    data["metastats"] = {}
    meta_stats = data["metastats"]

    # 季節
    season_match = re.search(r"(\S+)の月", text)
    if season_match:
        meta_stats["season"] = season_match.group(1)

    # 時間
    time_match = re.search(r"\)(\S+)時(\S+)分", text)
    if time_match:
        meta_stats["time"] = {"hour": time_match.group(1), "minute": time_match.group(2)}

    # 場所
    place_match = re.search(r"(\S+)\s+清潔度:(\S+)", text)
    if place_match:
        meta_stats["place"] = {"address": place_match.group(1), "cleanliness": place_match.group(2)}

    # 天気
    weather_match = re.search(r"(☀|☁|☂|☃)", text)
    if weather_match:
        meta_stats["weather"] = weather_match.group(1)

    # 気温
    temperature_match = re.search(r"気温(\S+)℃", text)
    if temperature_match:
        meta_stats["temperature"] = temperature_match.group(1)

    return data

# text からキャラクタステータスを取得し, 返す
def get_charastats(text: str, data: Dict[str, str]) -> Dict[str, str]:
    data["character"] = {}
    chara_data = data["character"]

    # キャラ名
    name_match = re.search(r"■(.+?)\(", text)
    if name_match:
        chara_data["name"] = name_match.group(1)

    # 好感度 / 信頼度
    affection_match = re.search(r"\(好感度:\s*([A-Z])\s*(\d+)\s*信頼度:\s*([A-Z])\s*(\d+)\)", text)
    if affection_match:
        chara_data["affection"] = {"rank": affection_match.group(1), "value": int(affection_match.group(2))}
        chara_data["trust"] = {"rank": affection_match.group(3), "value": int(affection_match.group(4))}

    # 発情
    heat_match = re.search(r"発情中", text)
    if heat_match:
        chara_data["heat"] = "1"

    # 装備
    equip_match = re.findall(r"装備:([^\s]+)\s*?\[(.+?)\]", text)
    if equip_match:
        chara_data["equip"] = {}
        for category, item in equip_match:
            if "？" in item:
                item = "unknown"
            chara_data["equip"][category] = item

    return data

# data(json) からポジティブプロンプトを生成する
def make_pos_prompt(data: Dict[str, str]) -> str:
    name = data["character"]["name"]
    pos_prompt = chara_tbl.get(name, "")
    if pos_prompt == "":
        return ""
    pos_prompt += ",best quality,masterpiece,absurdres,1girl,solo"
    return pos_prompt

# data(json) からネガティブプロンプトを生成する
def make_neg_prompt(data: Dict[str, str]) -> str:
    neg_prompt = "motion lines,speed lines,3d,((shiny skin)),bad quality,worst quality,worst detail,text,logo,cropped,deformed,blurry,((cropped face)),"\
             "((amputee)),((bad anatomy)),multiple heads,extra faces,(extra limbs),(missing limb),(missing limbs),"\
             "bad arm,(multiple arms),(extra arms),(missing arm),bad leg,(multiple legs),(extra legs),(missing leg),"\
             "((bad hands)),multiple hands,extra hands,missing hand,(extra digits:1.5),(fewer digits:1.5),(missing digits:1.5),"\
             "((bad feet)),((multiple feet)),((extra feet)),missing foot,(extra toes:2),(fewer toes:2),(missing toes:2)"
    return neg_prompt

# TKinter を指定の画像パスで更新する
def update_image(path):
    img = Image.open(path)
    tk_img = ImageTk.PhotoImage(img)
    label.configure(image=tk_img)
    label.image = tk_img  # 参照保持が必要

# data(json) を RestAPI でポストする
def do_restapi(data: Dict[str, str]):
    payload = {}
    pos_prompt = make_pos_prompt(data)
    if pos_prompt == "":
        return ""
    payload["prompt"] = pos_prompt
    payload["negative_prompt"] = make_neg_prompt(data)
    payload["steps"] = 30
    payload["sampler_name"] = "DPM++ 2S a "
    payload["scheduler"] = "Karras"
    payload["cfg_scale"] = 7.0
    payload["seed"] = -1
    payload["width"] = 512
    payload["height"] = 512

    # txt2img
    response = requests.post(f"{url}/sdapi/v1/txt2img", json=payload)
    image_data = response.json()["images"][0]

    # 画像保存
    image = Image.open(io.BytesIO(base64.b64decode(image_data)))
    image.save("output.png")

    update_image("output.png")

# クリップボードを監視し, 更新があった場合に行動画面であればメタステータスを, キャラクタ画面であればキャラクタステータスを取得する
# 後者の場合はさらに RestAPI でポストする
def monitor_clipboard():
    global last_text, data, last_data

    text = pyperclip.paste()
    if text != last_text:
        if re.search(r"(\S+)の月", text):
            data = get_metastats(text, data)
        elif re.search(r"■(.+?)\(", text):
            data = get_charastats(text, data)
            if data != last_data:
                do_restapi(data)
        print("-----------------------------------")
        print("data:", json.dumps(data, ensure_ascii=False, indent=2))
        last_text = text
        last_data = copy.deepcopy(data)

    # 500ms後に再度呼び出す
    root.after(500, monitor_clipboard)

# エントリポイント
try:
    last_text = ""
    data = {}
    last_data = {}

    signal.signal(signal.SIGINT, sigint_handler)

    # Tkinterのイベントループ開始
    root.after(100, monitor_clipboard)  # 監視を開始
    root.mainloop()
except KeyboardInterrupt:
    print("\n終了します。")
    root.destroy()
