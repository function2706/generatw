"""
クリップボード監視, GUI 管理, 画像生成管理を実施するモジュールの The World 版クラス
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from types import MappingProxyType
from typing import Any, Dict, Mapping

from functions import search_regex
from picmaker_base import PicMakerBase, PMConsts


class Season(Enum):
    spring = auto()
    summer = auto()
    autumn = auto()
    winter = auto()
    none = auto()


class Weather(Enum):
    sunny = auto()
    cloudy = auto()
    rainy = auto()
    snowy = auto()
    foggy = auto()
    none = auto()


class Vibe(Enum):
    normal = auto()
    good = auto()
    bad = auto()
    none = auto()


@dataclass
class Character:
    name: str = ""
    vibe: Vibe = Vibe.none
    affection: int = -1
    trust: int = -1
    frustration: int = -1
    angry: int = -1
    in_heat: bool = -1
    mood: int = -1
    corruption: int = -1
    upper: str = ""
    upper_state: str = ""
    lower: str = ""
    lower_state: str = ""

    @classmethod
    def make(cls, s: str):
        def make_name() -> str:
            match = search_regex(s, r"^(.+?)\s*(?:（[^）]+）)?\s*\(好感度")
            return "" if match is None else match

        def make_vibe() -> Vibe:
            match = search_regex(s, r"^.+?\s*(?:（([^）]+)）)?\s*\(好感度")
            if match is None:
                return Vibe.none
            elif match == "ご機嫌":
                return Vibe.good
            elif match == "フキゲン":
                return Vibe.bad
            else:
                return Vibe.normal

        def make_affection() -> int:
            match = search_regex(s, r"好感度:\s*[a-zA-Z]+\s*(\d+)")
            return -1 if match is None else int(match)

        def make_trust() -> int:
            match = search_regex(s, r"信頼度:\s*[a-zA-Z]+\s*(\d+)")
            return -1 if match is None else int(match)

        def make_frustration() -> int:
            match = search_regex(s, r"欲求不満度:\s*(\d+)％")
            return -1 if match is None else int(match)

        def make_angry() -> int:
            match = search_regex(s, r"怒り:\s*(！*)|怒", 0)
            if match is None:
                return -1
            elif match == "怒":
                return 6
            else:
                return len(match.replace("怒り:", "").strip())

        def make_in_heat() -> bool:
            return False if search_regex(s, r"発情中", 0) is None else True

        def make_mood() -> int:
            match = search_regex(s, r"ムード:\s*(OverDrive!!|❤*)")
            return -1 if match is None else 6 if match == "OverDrive!!" else len(match)

        def make_corruption() -> int:
            match = search_regex(s, r"理性:\s*(LimitBreak!!|★*)")
            return -1 if match is None else 6 if match == "LimitBreak!!" else 5 - len(match)

        def make_upper() -> str:
            match = search_regex(s, r"【上半身】\s*([^\s]*)")
            return "" if match is None else match.strip()

        def make_upper_state() -> str:
            match = search_regex(s, r"【上半身】\s*[^\s]*\s*([^【]*)")
            return "" if match is None else match.strip()

        def make_lower() -> str:
            match = search_regex(s, r"【下半身】\s*([^\s]*)")
            return "" if match is None else match.strip()

        def make_lower_state() -> str:
            match = search_regex(s, r"【下半身】\s*[^\s]*\s*([^【=<]*)")
            return "" if match is None else match.strip()

        return cls(
            name=make_name(),
            vibe=make_vibe(),
            affection=make_affection(),
            trust=make_trust(),
            frustration=make_frustration(),
            angry=make_angry(),
            in_heat=make_in_heat(),
            mood=make_mood(),
            corruption=make_corruption(),
            upper=make_upper(),
            upper_state=make_upper_state(),
            lower=make_lower(),
            lower_state=make_lower_state(),
        )


@dataclass
class Meta:
    season: Season = Season.none
    hour: int = -1
    minute: int = -1
    address: str = ""
    cleanliness: str = ""
    weather: Weather = Weather.none
    rainbow: bool = False
    temperature: float = 0

    @classmethod
    def make(cls, s: str):
        def make_season() -> Season:
            match = search_regex(s, r"([春夏秋冬])の月")
            if match is None:
                return Season.none
            elif match == "春":
                return Season.spring
            elif match == "夏":
                return Season.summer
            elif match == "秋":
                return Season.autumn
            elif match == "冬":
                return Season.winter
            else:
                return Season.none

        def make_hour() -> int:
            match = search_regex(s, r"(\d+)時")
            return -1 if match is None else int(match)

        def make_minute() -> int:
            match = search_regex(s, r"(\d+)分")
            return -1 if match is None else int(match)

        def make_address() -> str:
            match = search_regex(s, r"(\S+)\s+清潔度:")
            if match is not None:
                return match
            match = search_regex(s, r"(\S+)\s+\(到着")
            if match is not None:
                return match
            match = search_regex(s, r"\S+\s+-\s(\S+)\s-")
            if match is not None:
                return match
            match = search_regex(s, r"\]\s*([^\s\[\-、=]+)\s*\[")
            if match is not None:
                return match
            return ""

        def make_cleanliness() -> str:
            match = search_regex(s, r"清潔度:(\S+)")
            return "" if match is None else match

        def make_weather() -> Weather:
            match = search_regex(
                s,
                r"(晴れ|快晴|薄曇|曇り|雨|大雨|霧雨|霧|雪|吹雪|細雪|霧雪|みぞれ|あられ)",
            )
            if match is None:
                return Weather.none
            elif "晴" in match:
                return Weather.sunny
            elif "曇" in match:
                return Weather.cloudy
            elif "雨" in match:
                return Weather.rainy
            elif "霧" in match:
                return Weather.foggy
            else:
                return Weather.rainy

        def make_rainbow() -> bool:
            return False

        def make_temperature() -> float:
            match = search_regex(s, r"気温(\S+)℃")
            return -1 if match is None else float(match)

        return cls(
            season=make_season(),
            hour=make_hour(),
            minute=make_minute(),
            address=make_address(),
            cleanliness=make_cleanliness(),
            weather=make_weather(),
            rainbow=make_rainbow(),
            temperature=make_temperature(),
        )


@dataclass
class TWStats:
    character: Character = field(default_factory=Character)
    meta: Meta = field(default_factory=Meta)

    def refresh(self, s: str):
        if search_regex(s, r"[春夏秋冬]の月", 0):
            self.character = Character.make(s)
            self.meta = Meta.make(s)

    def todict(self) -> Dict[str, Any]:
        return asdict(self)


# eratohoTW
class PicMakerTW(PicMakerBase[TWStats]):
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
        super().__init__(TWStats())

    def make_dummy_stats(self, name: str = None) -> TWStats:
        dummy_stats = TWStats()
        dummy_stats.character.name = (
            name
            if name is not None
            else PMConsts.charaname_substr_debug + str(random.randint(1, 8))
        )
        dummy_stats.character.vibe = Vibe.normal
        dummy_stats.character.affection = 100
        dummy_stats.character.trust = 100
        dummy_stats.character.frustration = 10
        dummy_stats.character.angry = 3
        dummy_stats.character.in_heat = True
        dummy_stats.character.mood = 3
        dummy_stats.character.corruption = 3
        dummy_stats.character.upper = "シャツ"
        dummy_stats.character.upper_state = ""
        dummy_stats.character.lower = "パンツ"
        dummy_stats.character.lower_state = ""

        dummy_stats.meta.season = Season.spring
        dummy_stats.meta.hour = 12
        dummy_stats.meta.minute = 34
        dummy_stats.meta.address = "居間"
        dummy_stats.meta.cleanliness = "最高"
        dummy_stats.meta.weather = Weather.sunny
        dummy_stats.meta.rainbow = False
        dummy_stats.meta.temperature = 25.0
        return dummy_stats

    def is_stats_enough_for_prompt(self) -> bool:
        return self.crnt_stats.character.name != ""

    def make_pos_prompt(self) -> str:
        pos_prompt = self.chara_tbl.get(self.crnt_stats.character.name, "")
        if pos_prompt == "":
            return ""
        pos_prompt += ",best quality,masterpiece,absurdres,1girl,solo"
        return pos_prompt

    def make_neg_prompt(self) -> str:
        if PMConsts.charaname_substr_debug in self.crnt_stats.character.name:
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
