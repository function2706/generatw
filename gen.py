import tkinter as tk
from PIL import Image, ImageTk
from typing import Dict
import io, os, base64, requests, json, re, time, pyperclip, copy

url = "http://127.0.0.1:7860"

chara_tbl = {
    "博麗 霊夢": "hakurei reimu",
    "る～こと": "ruukoto,green hair,short hair,blue eyes,light blue maid apron,red bowtie,tareme",
    "カナ アナベラル": "kana anaberal",
    "魅魔": "mima \(touhou\)",
    "サニーミルク": "sunny milk",
    "ルナチャイルド": "luna child",
    "スターサファイア": "star sapphire",
    "北白河 ちゆり": "kitashirakawa chiyuri,naval uniform,blue neckerchief,sailor hat,crop top,shorts",
    "岡崎 夢美": "okazaki yumemi",
    "伊吹 萃香": "ibuki suika",
    "霧雨 魔理沙": "kirisame marisa",
    "ルーミア": "rumia",
    "大妖精": "daiyousei",
    "チルノ": "cirno",
    "十六夜 咲夜": "izayoi sakuya",
    "レミリア スカーレット": "remilia scarlet",
    "アリス マーガトロイド": "alice margatroid",
    "リリー ホワイト": "lily white",
    "リリー ブラック": "lily black",
    "リリカ プリズムリバー": "lyrica prismriver",
    "メルラン プリズムリバー": "merlin prismriver",
    "ルナサ プリズムリバー": "lunasa prismriver",
    "魂魄 妖夢": "konpaku youmu",
    "橙": "chen",
    "八雲 藍": "yakumo ran",
    "八雲 紫": "yakumo yukari",
    "リグル ナイトバグ": "wriggle nightbug",
    "ミスティア ローレライ": "mystia lorelei",
    "射命丸 文": "shameimaru aya",
    "四季 映姫": "shiki eiki",
    "東風谷 早苗": "kochiya sanae",
    "八坂 神奈子": "yasaka kanako",
    "洩矢 諏訪子": "moriya suwako",
    "比那名居 天子": "hinanawi tenshi",
    "永江 衣玖": "nagae iku",
    "火焔猫 燐": "kaenbyou rin",
    "霊烏路 空": "reiuji utsuho",
    "古明地 こいし": "komeiji koishi",
    "ナズーリン": "nazrin",
    "多々良 小傘": "tatara kogasa",
    "封獣 ぬえ": "houjuu nue",
    "姫海棠 はたて": "himekaidou hatate",
    "茨木 華扇": "ibaraki kasen",
    "ふわふわエレン": "ellen \(touhou\)",
    "朝倉 理香子": "asakura rikako,purple hair,long hair,purple eyes,round eyewear,white hair band,white hair ribbon,lab coat,yellow bowtie",
    "明羅": "meira \(touhou\),purple hair,long hair,ponytail,parted bangs,white ribbon",
    "里香": "rika \(touhou\),brown hair,twin braids,red ribbon,brown eyes,white shirt,long sleeves,red short necktie",
    "ルイズ": "louise \(touhou\),blonde hair,parted bangs,twintails,sidelocks,purple ribbon,white hat,white shirt,purple neckerchief,yellow eyes",
    "古明地 さとり": "komeiji satori",
    "フランドール": "flandre scarlet",
    "河城 にとり": "kawashiro nitori",
    "鈴仙・優曇華院・イナバ": "reisen udongein inaba",
    "因幡 てゐ": "inaba tewi",
    "パチュリー・ノーレッジ": "patchouli knowledge",
    "聖 白蓮": "hijiri byakuren",
    "豊聡耳神子": "toyosatomimi no miko",
    "秦こころ": "hata no kokoro",
    "紅美鈴": "hong meiling",
    "小悪魔": "koakuma",
    "水橋 パルスィ": "mizuhashi parsee",
    "藤原 妹紅": "fujiwara no mokou",
    "蓬莱山 輝夜": "houraisan kaguya",
    "今泉影狼": "imaizumi kagerou",
    "星熊 勇儀": "hoshiguma yuugi",
    "犬走 椛": "inubashiri momiji",
    "西行寺 幽々子": "saigyouji yuyuko",
    "上白沢 慧音": "kamishirasawa keine",
    "風見 幽香": "kazami yuuka",
    "二ッ岩 マミゾウ": "futatsuiwa mamizou",
    "本居 小鈴": "motoori kosuzu",
    "少名 針妙丸": "sukuna shinmyoumaru",
    "八意 永琳": "yagokoro eirin",
    "赤 蛮奇": "sekibanki",
    "レティ・ホワイトロック": "letty whiterock",
    "メディスン・メランコリー": "medicine melancholy",
    "小野塚 小町": "onozuka komachi",
    "秋 静葉": "aki shizuha",
    "秋 穣子": "aki minoriko",
    "鍵山 雛": "kagiyama hina",
    "稗田 阿求": "hieda no akyuu",
    "宇佐見 蓮子": "usami renko",
    "マエリベリー・ハーン": "maribel hearn",
    "キスメ": "kisume",
    "黒谷 ヤマメ": "kurodani yamame",
    "雲居 一輪": "kumoi ichirin",
    "村紗 水蜜": "murasa minamitsu",
    "寅丸 星": "toramaru shou",
    "幽谷 響子": "kasodani kyouko",
    "宮古 芳香": "miyako yoshika",
    "霍 青娥": "kaku seiga",
    "蘇我 屠自古": "soga no tojiko,ghost tail",
    "物部 布都": "mononobe no futo",
    "わかさぎ姫": "wakasagihime",
    "九十九 弁々": "tsukumo benben",
    "九十九 八橋": "tsukumo yatsuhashi",
    "堀川 雷鼓": "horikawa raiko",
    "鬼人 正邪": "kijin seija",
    "綿月 依姫": "watatsuki no yorihime",
    "綿月 豊姫": "watatsuki no toyohime",
    "レイセン": "reisen \(touhou bougetsushou\)",
    "朱鷺子": "tokiko \(touhou\)",
    "神綺": "shinki \(touhou\)",
    "夢子": "yumeko \(touhou\),yellow eyes,",
    "ユキ": "yuki \(touhou\),blonde hair,middle hair,yellow eyes,black hat,black clothes,white shirt,short sleeves,black skirt",
    "マイ": "mai \(touhou\),blue hair,blue eyes,short hair,light pink hair ribbon,white wings,light pink dress,",
    "宇佐見 菫子": "usami sumireko",
    "清蘭": "seiran \(touhou\)",
    "鈴瑚": "ringo \(touhou\)",
    "ドレミー・スイート": "doremy sweet",
    "稀神 サグメ": "kishin sagume",
    "クラウンピース": "clownpiece",
    "純狐": "junko \(touhou\)",
    "ヘカーティア・ラピスラズリ": "hecatia lapislazuli",
    "くるみ": "kurumi \(touhou\),blonde hair,long hair,yellow eyes,white ribbon,big bat wings",
    "エリー": "elly \(touhou\)",
    "夢月": "mugetsu \(touhou\)",
    "幻月": "gengetsu \(touhou\),white wings",
    "エタニティラルバ": "eternity larva",
    "坂田 ネムノ": "sakata nemuno,sharp teeth",
    "高麗野 あうん": "komano aunn",
    "矢田寺 成美": "yatadera narumi",
    "丁礼田 舞": "teireida mai",
    "爾子田 里乃": "nishida satono",
    "摩多羅 隠岐奈": "matara okina",
    "依神 女苑": "yorigami jo'on,tsurime",
    "依神 紫苑": "yorigami shion",
    "戎 瓔花": "ebisu eika",
    "牛崎 潤美": "ushizaki urumi",
    "庭渡 久侘歌": "niwatari kutaka",
    "吉弔 八千慧": "kicchou yachie",
    "杖刀偶 磨弓": "joutouguu mayumi",
    "埴安神 袿姫": "haniyasushin keiki",
    "驪駒 早鬼": "kurokoma saki",
    "奥野田 美宵": "okunoda miyoi",
    "豪徳寺 ミケ": "goutokuji mike",
    "山城 たかね,": "yamashiro takane",
    "駒草 山如": "komakusa sannyo",
    "玉造 魅須丸": "tamatsukuri misumaru",
    "菅牧 典": "kudamaki tsukasa",
    "飯綱丸 龍": "iizunamaru megumu",
    "天弓 千亦": "tenkyuu chimata",
    "姫虫 百々世": "himemushi momoyo",
    "饕餮 尤魔": "toutetsu yuuma,sharp teeth",
    "小兎姫": "kotohime \(touhou\),yellow ribbon",
    "エリス": "elis \(touhou\),yellow hair,long hair,red ribbon,red star on face,red hair flower,bat wings",
    "サリエル": "sariel \(touhou\),red eyes,white wings",
    "サラ": "sara \(touhou\),pink hair,side ponytail,short hair,red eyes,red frilled dress,white shirt,short sleeves",
    "オレンジ": "orange \(touhou\),orange hair,orange eyes,long hair,yellow shirt,yellow shorts,green skirt",
    "矜羯羅": "konngara \(touhou\)",
    "ユウゲンマガン": "yuugenmagan,blonde hair,ponytail,yellow eyes,white shirt,light yellow hakama",
    "キクリ": "kikuri \(touhou\),blonde hair,blue eyes,wavy hair,long hair,parted bangs",
    "孫 美天": "son biten",
    "三頭 慧ノ子": "mitsugashira enoko",
    "天火人 ちやり": "tenkajin chiyari",
    "豫母都 日狭美": "yomotsu hisami,flower over eyes",
    "日白 残無": "nippaku zanmu",
    "宮出口 瑞霊": "miyadeguchi mizuchi,blue hair,blue eyes,ponytail,crossed bangs,hair between eyes"
}

# Global
root = tk.Tk()
root.title("eragen")
label = tk.Label(root)
label.pack()

def get_metastats(text: str, data: Dict[str, str]) -> Dict[str, str]:
    data["metastats"] = {}
    meta_stats = data["metastats"]

    # 季節
    season_match = re.search(r"(\S+)の月", text)
    if season_match:
        meta_stats["season"] = season_match.group(1)
    else:
        return data

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


def get_charastats(text: str, data: Dict[str, str]) -> Dict[str, str]:
    data["character"] = {}
    chara_data = data["character"]

    # キャラ名
    name_match = re.search(r"■(.+?)\(", text)
    if name_match:
        chara_data["name"] = name_match.group(1)
    else:
        return data

    affection_match = re.search(r"\(好感度:\s*([A-Z])\s*(\d+)\s*信頼度:\s*([A-Z])\s*(\d+)\)", text)
    if affection_match:
        chara_data["affection"] = {"rank": affection_match.group(1), "value": int(affection_match.group(2))}
        chara_data["trust"] = {"rank": affection_match.group(3), "value": int(affection_match.group(4))}
    
    heat_match = re.search(r"発情中", text)
    if heat_match:
        chara_data["heat"] = "1"

    equip_match = re.findall(r"装備:([^\s]+)\s*?\[(.+?)\]", text)
    if equip_match:
        chara_data["equip"] = {}
        for category, item in equip_match:
            if "？" in item:
                item = "unknown"
            chara_data["equip"][category] = item

    return data


def update_image(path):
    img = Image.open(path)
    tk_img = ImageTk.PhotoImage(img)
    label.configure(image=tk_img)
    label.image = tk_img  # 参照保持が必要


def do_restapi(data: Dict[str, str]):
    name = data["character"]["name"]
    pos_prompt = chara_tbl.get(name, "")
    if pos_prompt == "":
        # 主人公を含むリスト内に存在しないキャラクターは生成しない
        return
    pos_prompt += ",best quality,masterpiece,absurdres,1girl,solo"

    payload = {}
    payload["prompt"] = pos_prompt
    payload["steps"] = 25

    response = requests.post(f"{url}/sdapi/v1/txt2img", json=payload)
    image_data = response.json()["images"][0]

    # 画像保存
    image = Image.open(io.BytesIO(base64.b64decode(image_data)))
    image.save("output.png")

    update_image("output.png")


def monitor_clipboard():
    global last_text, data, last_data

    text = pyperclip.paste()
    if text != last_text:
        data = get_metastats(text, data)
        if re.search(r"■(.+?)\(", text):
            data = get_charastats(text, data)
            if data != last_data:
                print("data:", json.dumps(data, ensure_ascii=False, indent=2))
                do_restapi(data)
        last_text = text
        last_data = copy.deepcopy(data)

    # 500ms後に再度呼び出す
    root.after(500, monitor_clipboard)

try:
    last_text = ""
    data = {}
    last_data = {}

    # Tkinterのイベントループ開始
    root.after(100, monitor_clipboard)  # 監視を開始
    root.mainloop()
except KeyboardInterrupt:
    print("\n終了します。")
