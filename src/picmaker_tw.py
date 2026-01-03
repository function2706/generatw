"""
クリップボード監視, GUI 管理, 画像生成管理を実施するモジュールの The World 版クラス
"""

from __future__ import annotations

import copy
import re
from types import MappingProxyType
from typing import Any, Dict, Mapping

from picmaker_base import PicMakerBase, PMConsts


# eratohoTW
class PicMakerTW(PicMakerBase):
    """
    クリップボード監視, GUI 管理, 画像生成管理を実施するクラス for The World
    """

    @property
    def chara_tbl(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "博麗 霊夢": "hakurei reimu",
                "る～こと": (
                    "ruukoto,green hair,short hair,blue eyes,"
                    "light blue maid apron,red bowtie,tareme"
                ),
                "カナ アナベラル": "kana anaberal",
                "魅魔": "mima \(touhou\)",
                "サニーミルク": "sunny milk",
                "ルナチャイルド": "luna child",
                "スターサファイア": "star sapphire",
                "北白河 ちゆり": (
                    "kitashirakawa chiyuri,naval uniform,"
                    "blue neckerchief,sailor hat,crop top,shorts"
                ),
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
                "朝倉 理香子": (
                    "asakura rikako,purple hair,long hair,purple eyes,"
                    "round eyewear,white hair band,white hair ribbon,lab coat,yellow bowtie"
                ),
                "明羅": "meira \(touhou\),purple hair,long hair,ponytail,parted bangs,white ribbon",
                "里香": (
                    "rika \(touhou\),brown hair,"
                    "twin braids,red ribbon,brown eyes,white shirt,long sleeves,red short necktie"
                ),
                "ルイズ": (
                    "louise \(touhou\),blonde hair,parted bangs,twintails,sidelocks,"
                    "purple ribbon,white hat,white shirt,purple neckerchief,yellow eyes"
                ),
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
                "ユキ": (
                    "yuki \(touhou\),blonde hair,middle hair,yellow eyes,"
                    "black hat,black clothes,white shirt,short sleeves,black skirt"
                ),
                "マイ": (
                    "mai \(touhou\),blue hair,blue eyes,short hair,"
                    "light pink hair ribbon,white wings,light pink dress,"
                ),
                "宇佐見 菫子": "usami sumireko",
                "清蘭": "seiran \(touhou\)",
                "鈴瑚": "ringo \(touhou\)",
                "ドレミー・スイート": "doremy sweet",
                "稀神 サグメ": "kishin sagume",
                "クラウンピース": "clownpiece",
                "純狐": "junko \(touhou\)",
                "ヘカーティア・ラピスラズリ": "hecatia lapislazuli",
                "くるみ": (
                    "kurumi \(touhou\),blonde hair,long hair,yellow eyes,white ribbon,big bat wings"
                ),
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
                "エリス": (
                    "elis \(touhou\),yellow hair,long hair,red ribbon,"
                    "red star on face,red hair flower,bat wings"
                ),
                "サリエル": "sariel \(touhou\),red eyes,white wings",
                "サラ": (
                    "sara \(touhou\),pink hair,side ponytail,"
                    "short hair,red eyes,red frilled dress,white shirt,short sleeves"
                ),
                "オレンジ": (
                    "orange \(touhou\),orange hair,orange eyes,"
                    "long hair,yellow shirt,yellow shorts,green skirt"
                ),
                "矜羯羅": "konngara \(touhou\)",
                "ユウゲンマガン": (
                    "yuugenmagan,blonde hair,ponytail,yellow eyes,white shirt,light yellow hakama"
                ),
                "キクリ": (
                    "kikuri \(touhou\),blonde hair,blue eyes,wavy hair,long hair,parted bangs"
                ),
                "孫 美天": "son biten",
                "三頭 慧ノ子": "mitsugashira enoko",
                "天火人 ちやり": "tenkajin chiyari",
                "豫母都 日狭美": "yomotsu hisami,flower over eyes",
                "日白 残無": "nippaku zanmu",
                "宮出口 瑞霊": (
                    "miyadeguchi mizuchi,blue hair,blue eyes,ponytail,"
                    "crossed bangs,hair between eyes"
                ),
                PMConsts.charaname_substr_debug + "1": "human girl",
                PMConsts.charaname_substr_debug + "2": "dog girl",
                PMConsts.charaname_substr_debug + "3": "cat girl",
                PMConsts.charaname_substr_debug + "4": "rabbit girl",
                PMConsts.charaname_substr_debug + "5": "mouse girl",
                PMConsts.charaname_substr_debug + "6": "sheep girl",
                PMConsts.charaname_substr_debug + "7": "fox girl",
                PMConsts.charaname_substr_debug + "8": "elf girl",
            }
        )

    def __init__(self):
        super().__init__()

    def get_dummy_stats(self) -> Dict[str, Any]:
        stats = {}

        stats["metastats"] = {}
        meta_stats = stats["metastats"]
        meta_stats["season"] = "春"
        meta_stats["time"] = {"hour": "12", "minute": "34"}
        meta_stats["place"] = {"address": "デバッグルーム", "cleanliness": "清潔"}
        meta_stats["weather"] = "☀"
        meta_stats["temperature"] = "25"

        stats["character"] = {}
        chara_data = stats["character"]
        chara_data["name"] = self.crnt_clipboard
        chara_data["affection"] = {"rank": "C", "value": "100"}
        chara_data["trust"] = {"rank": "C", "value": "100"}
        chara_data["heat"] = "1"
        chara_data["equip"] = {}
        chara_data["equip"]["上半身"] = "シャツ"
        chara_data["equip"]["下半身"] = "パンツ"
        return stats

    def get_metastats(self, stats: Dict[str, Any]) -> None:
        """
        指定のステータスからメタステータスを取得する

        Args:
            stats (Dict[str, Any]): ステータス
        """
        stats["metastats"] = {}
        meta_stats = stats["metastats"]
        # 季節
        season_match = re.search(r"(\S+)の月", self.crnt_clipboard)
        if season_match:
            meta_stats["season"] = season_match.group(1)
        # 時間
        time_match = re.search(r"\)(\S+)時(\S+)分", self.crnt_clipboard)
        if time_match:
            meta_stats["time"] = {"hour": time_match.group(1), "minute": time_match.group(2)}
        # 場所
        place_match = re.search(r"(\S+)\s+清潔度:(\S+)", self.crnt_clipboard)
        if place_match:
            meta_stats["place"] = {
                "address": place_match.group(1),
                "cleanliness": place_match.group(2),
            }
        # 天気
        weather_match = re.search(r"(☀|☁|☂|☃)", self.crnt_clipboard)
        if weather_match:
            meta_stats["weather"] = weather_match.group(1)
        # 気温
        temperature_match = re.search(r"気温(\S+)℃", self.crnt_clipboard)
        if temperature_match:
            meta_stats["temperature"] = temperature_match.group(1)

    def get_charastats(self, stats: Dict[str, Any]) -> None:
        """
        指定のステータスからキャラクターステータスを取得する

        Args:
            stats (Dict[str, Any]): ステータス
        """
        stats["character"] = {}
        chara_data = stats["character"]
        # キャラ名
        name_match = re.search(r"■(.+?)\(", self.crnt_clipboard)
        if name_match:
            chara_data["name"] = name_match.group(1)
        # 好感度 / 信頼度
        affection_match = re.search(
            r"\(好感度:\s*([A-Z])\s*(\d+)\s*信頼度:\s*([A-Z])\s*(\d+)\)", self.crnt_clipboard
        )
        if affection_match:
            chara_data["affection"] = {
                "rank": affection_match.group(1),
                "value": int(affection_match.group(2)),
            }
            chara_data["trust"] = {
                "rank": affection_match.group(3),
                "value": int(affection_match.group(4)),
            }
        # 発情
        heat_match = re.search(r"発情中", self.crnt_clipboard)
        if heat_match:
            chara_data["heat"] = "1"
        # 装備
        equip_match = re.findall(r"装備:([^\s]+)\s*?\[(.+?)\]", self.crnt_clipboard)
        if equip_match:
            chara_data["equip"] = {}
            for category, item in equip_match:
                if "？" in item:
                    item = "unknown"
                chara_data["equip"][category] = item

    def parse_clipboard(self) -> Dict[str, Any]:
        """
        クリップボード文字列が行動画面であればメタステータスを,\n
        キャラクタ画面であればキャラクタステータスを取得する\n
        変更が加わる箇所以外は更新されない

        Returns:
            Dict[str, Any]: ステータス
        """
        if PMConsts.charaname_substr_debug in self.crnt_clipboard:
            return self.get_dummy_stats()

        new_stats = copy.deepcopy(self.crnt_stats)
        if re.search(r"(\S+)の月", self.crnt_clipboard):
            self.get_metastats(new_stats)
        elif re.search(r"■(.+?)\(", self.crnt_clipboard):
            self.get_charastats(new_stats)

        return new_stats

    def is_stats_enough_for_prompt(self) -> bool:
        stats = self.crnt_stats
        if not isinstance(stats, Dict) or not stats:
            return False
        character = stats.get("character")
        if not isinstance(character, Dict) or not character:
            return False
        name = character.get("name")
        if not isinstance(name, str) or not name:
            return False

        return True

    def make_pos_prompt(self) -> str:
        name = self.crnt_stats["character"]["name"]
        pos_prompt = self.chara_tbl.get(name, "")
        if pos_prompt == "":
            return ""
        pos_prompt += ",best quality,masterpiece,absurdres,1girl,solo"
        return pos_prompt

    def make_neg_prompt(self) -> str:
        if PMConsts.charaname_substr_debug in self.crnt_stats["character"]["name"]:
            # デバッグステータス
            return "TW debug"

        neg_prompt = (
            "motion lines,speed lines,3d,((shiny skin)),bad quality,"
            "worst quality,worst detail,text,logo,cropped,deformed,blurry,((cropped face)),"
            "((amputee)),((bad anatomy)),multiple heads,extra faces,"
            "(extra limbs),(missing limb),(missing limbs),"
            "bad arm,(multiple arms),(extra arms),(missing arm),bad leg,"
            "(multiple legs),(extra legs),(missing leg),"
            "((bad hands)),multiple hands,extra hands,missing hand,"
            "(extra digits:1.5),(fewer digits:1.5),(missing digits:1.5),"
            "((bad feet)),((multiple feet)),((extra feet)),missing foot,"
            "(extra toes:2),(fewer toes:2),(missing toes:2)"
        )
        return neg_prompt
