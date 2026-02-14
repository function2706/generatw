"""
クリップボード監視, ステータス記録クラス (The World 版)
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from types import MappingProxyType
from typing import Any, Mapping

from common.functions import BottleMail, search_regex
from master.events import ParserEvent
from master.interfaces import MasterIF
from parser.parser import Consts, Parser


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

    def todict(self) -> dict[str, Any]:
        return asdict(self)


# eratohoTW
class TheWorldParser(Parser[TWStats]):
    """
    クリップボード監視, ステータス記録クラス (The World 版)
    """

    @property
    def chara_tbl(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "博麗 霊夢": r"hakurei reimu",
                "る～こと": (
                    r"ruukoto,green hair,short hair,blue eyes,"
                    r"light blue maid apron,red bowtie,tareme"
                ),
                "カナ アナベラル": r"kana anaberal",
                "魅魔": r"mima \(touhou\)",
                "サニーミルク": r"sunny milk",
                "ルナチャイルド": r"luna child",
                "スターサファイア": r"star sapphire",
                "北白河 ちゆり": (
                    r"kitashirakawa chiyuri,naval uniform,"
                    r"blue neckerchief,sailor hat,crop top,shorts"
                ),
                "岡崎 夢美": r"okazaki yumemi",
                "伊吹 萃香": r"ibuki suika",
                "霧雨 魔理沙": r"kirisame marisa",
                "ルーミア": r"rumia",
                "大妖精": r"daiyousei",
                "チルノ": r"cirno",
                "十六夜 咲夜": r"izayoi sakuya",
                "レミリア スカーレット": r"remilia scarlet",
                "アリス マーガトロイド": r"alice margatroid",
                "リリー ホワイト": r"lily white",
                "リリー ブラック": r"lily black",
                "リリカ プリズムリバー": r"lyrica prismriver",
                "メルラン プリズムリバー": r"merlin prismriver",
                "ルナサ プリズムリバー": r"lunasa prismriver",
                "魂魄 妖夢": r"konpaku youmu",
                "橙": r"chen",
                "八雲 藍": r"yakumo ran",
                "八雲 紫": r"yakumo yukari",
                "リグル ナイトバグ": r"wriggle nightbug",
                "ミスティア ローレライ": r"mystia lorelei",
                "射命丸 文": r"shameimaru aya",
                "四季 映姫": r"shiki eiki",
                "東風谷 早苗": r"kochiya sanae",
                "八坂 神奈子": r"yasaka kanako",
                "洩矢 諏訪子": r"moriya suwako",
                "比那名居 天子": r"hinanawi tenshi",
                "永江 衣玖": r"nagae iku",
                "火焔猫 燐": r"kaenbyou rin",
                "霊烏路 空": r"reiuji utsuho",
                "古明地 こいし": r"komeiji koishi",
                "ナズーリン": r"nazrin",
                "多々良 小傘": r"tatara kogasa",
                "封獣 ぬえ": r"houjuu nue",
                "姫海棠 はたて": r"himekaidou hatate",
                "茨木 華扇": r"ibaraki kasen",
                "ふわふわエレン": r"ellen \(touhou\)",
                "朝倉 理香子": (
                    r"asakura rikako,purple hair,long hair,purple eyes,"
                    r"round eyewear,white hair band,white hair ribbon,lab coat,yellow bowtie"
                ),
                "明羅": (
                    r"meira \(touhou\),purple hair,long hair,ponytail,parted bangs,white ribbon"
                ),
                "里香": (
                    r"rika \(touhou\),brown hair,"
                    r"twin braids,red ribbon,brown eyes,white shirt,long sleeves,red short necktie"
                ),
                "ルイズ": (
                    r"louise \(touhou\),blonde hair,parted bangs,twintails,sidelocks,"
                    r"purple ribbon,white hat,white shirt,purple neckerchief,yellow eyes"
                ),
                "古明地 さとり": r"komeiji satori",
                "フランドール": r"flandre scarlet",
                "河城 にとり": r"kawashiro nitori",
                "鈴仙・優曇華院・イナバ": r"reisen udongein inaba",
                "因幡 てゐ": r"inaba tewi",
                "パチュリー・ノーレッジ": r"patchouli knowledge",
                "聖 白蓮": r"hijiri byakuren",
                "豊聡耳神子": r"toyosatomimi no miko",
                "秦こころ": r"hata no kokoro",
                "紅美鈴": r"hong meiling",
                "小悪魔": r"koakuma",
                "水橋 パルスィ": r"mizuhashi parsee",
                "藤原 妹紅": r"fujiwara no mokou",
                "蓬莱山 輝夜": r"houraisan kaguya",
                "今泉影狼": r"imaizumi kagerou",
                "星熊 勇儀": r"hoshiguma yuugi",
                "犬走 椛": r"inubashiri momiji",
                "西行寺 幽々子": r"saigyouji yuyuko",
                "上白沢 慧音": r"kamishirasawa keine",
                "風見 幽香": r"kazami yuuka",
                "二ッ岩 マミゾウ": r"futatsuiwa mamizou",
                "本居 小鈴": r"motoori kosuzu",
                "少名 針妙丸": r"sukuna shinmyoumaru",
                "八意 永琳": r"yagokoro eirin",
                "赤 蛮奇": r"sekibanki",
                "レティ・ホワイトロック": r"letty whiterock",
                "メディスン・メランコリー": r"medicine melancholy",
                "小野塚 小町": r"onozuka komachi",
                "秋 静葉": r"aki shizuha",
                "秋 穣子": r"aki minoriko",
                "鍵山 雛": r"kagiyama hina",
                "稗田 阿求": r"hieda no akyuu",
                "宇佐見 蓮子": r"usami renko",
                "マエリベリー・ハーン": r"maribel hearn",
                "キスメ": r"kisume",
                "黒谷 ヤマメ": r"kurodani yamame",
                "雲居 一輪": r"kumoi ichirin",
                "村紗 水蜜": r"murasa minamitsu",
                "寅丸 星": r"toramaru shou",
                "幽谷 響子": r"kasodani kyouko",
                "宮古 芳香": r"miyako yoshika",
                "霍 青娥": r"kaku seiga",
                "蘇我 屠自古": r"soga no tojiko,ghost tail",
                "物部 布都": r"mononobe no futo",
                "わかさぎ姫": r"wakasagihime",
                "九十九 弁々": r"tsukumo benben",
                "九十九 八橋": r"tsukumo yatsuhashi",
                "堀川 雷鼓": r"horikawa raiko",
                "鬼人 正邪": r"kijin seija",
                "綿月 依姫": r"watatsuki no yorihime",
                "綿月 豊姫": r"watatsuki no toyohime",
                "レイセン": r"reisen \(touhou bougetsushou\)",
                "朱鷺子": r"tokiko \(touhou\)",
                "神綺": r"shinki \(touhou\)",
                "夢子": r"yumeko \(touhou\),yellow eyes,",
                "ユキ": (
                    r"yuki \(touhou\),blonde hair,middle hair,yellow eyes,"
                    r"black hat,black clothes,white shirt,short sleeves,black skirt"
                ),
                "マイ": (
                    r"mai \(touhou\),blue hair,blue eyes,short hair,"
                    r"light pink hair ribbon,white wings,light pink dress,"
                ),
                "宇佐見 菫子": r"usami sumireko",
                "清蘭": r"seiran \(touhou\)",
                "鈴瑚": r"ringo \(touhou\)",
                "ドレミー・スイート": r"doremy sweet",
                "稀神 サグメ": r"kishin sagume",
                "クラウンピース": r"clownpiece",
                "純狐": r"junko \(touhou\)",
                "ヘカーティア・ラピスラズリ": r"hecatia lapislazuli",
                "くるみ": (
                    r"kurumi \(touhou\),blonde hair,long hair,"
                    r"yellow eyes,white ribbon,big bat wings"
                ),
                "エリー": r"elly \(touhou\)",
                "夢月": r"mugetsu \(touhou\)",
                "幻月": r"gengetsu \(touhou\),white wings",
                "エタニティラルバ": r"eternity larva",
                "坂田 ネムノ": r"sakata nemuno,sharp teeth",
                "高麗野 あうん": r"komano aunn",
                "矢田寺 成美": r"yatadera narumi",
                "丁礼田 舞": r"teireida mai",
                "爾子田 里乃": r"nishida satono",
                "摩多羅 隠岐奈": r"matara okina",
                "依神 女苑": r"yorigami jo'on,tsurime",
                "依神 紫苑": r"yorigami shion",
                "戎 瓔花": r"ebisu eika",
                "牛崎 潤美": r"ushizaki urumi",
                "庭渡 久侘歌": r"niwatari kutaka",
                "吉弔 八千慧": r"kicchou yachie",
                "杖刀偶 磨弓": r"joutouguu mayumi",
                "埴安神 袿姫": r"haniyasushin keiki",
                "驪駒 早鬼": r"kurokoma saki",
                "奥野田 美宵": r"okunoda miyoi",
                "豪徳寺 ミケ": r"goutokuji mike",
                "山城 たかね,": r"yamashiro takane",
                "駒草 山如": r"komakusa sannyo",
                "玉造 魅須丸": r"tamatsukuri misumaru",
                "菅牧 典": r"kudamaki tsukasa",
                "飯綱丸 龍": r"iizunamaru megumu",
                "天弓 千亦": r"tenkyuu chimata",
                "姫虫 百々世": r"himemushi momoyo",
                "饕餮 尤魔": r"toutetsu yuuma,sharp teeth",
                "小兎姫": r"kotohime \(touhou\),yellow ribbon",
                "エリス": (
                    r"elis \(touhou\),yellow hair,long hair,red ribbon,"
                    r"red star on face,red hair flower,bat wings"
                ),
                "サリエル": r"sariel \(touhou\),red eyes,white wings",
                "サラ": (
                    r"sara \(touhou\),pink hair,side ponytail,"
                    r"short hair,red eyes,red frilled dress,white shirt,short sleeves"
                ),
                "オレンジ": (
                    r"orange \(touhou\),orange hair,orange eyes,"
                    r"long hair,yellow shirt,yellow shorts,green skirt"
                ),
                "矜羯羅": r"konngara \(touhou\)",
                "ユウゲンマガン": (
                    r"yuugenmagan,blonde hair,ponytail,yellow eyes,white shirt,light yellow hakama"
                ),
                "キクリ": (
                    r"kikuri \(touhou\),blonde hair,blue eyes,wavy hair,long hair,parted bangs"
                ),
                "孫 美天": r"son biten",
                "三頭 慧ノ子": r"mitsugashira enoko",
                "天火人 ちやり": r"tenkajin chiyari",
                "豫母都 日狭美": r"yomotsu hisami,flower over eyes",
                "日白 残無": r"nippaku zanmu",
                "宮出口 瑞霊": (
                    r"miyadeguchi mizuchi,blue hair,blue eyes,ponytail,"
                    r"crossed bangs,hair between eyes"
                ),
                Consts.charaname_substr_debug + "1": r"human girl",
                Consts.charaname_substr_debug + "2": r"dog girl",
                Consts.charaname_substr_debug + "3": r"cat girl",
                Consts.charaname_substr_debug + "4": r"rabbit girl",
                Consts.charaname_substr_debug + "5": r"mouse girl",
                Consts.charaname_substr_debug + "6": r"sheep girl",
                Consts.charaname_substr_debug + "7": r"fox girl",
                Consts.charaname_substr_debug + "8": r"elf girl",
            }
        )

    def __init__(
        self,
        master: MasterIF,
        to_master: BottleMail[ParserEvent],
    ):
        super().__init__(master, to_master, TWStats())

    def make_dummy_stats(self, name: str = None) -> TWStats:
        dummy_stats = TWStats()
        dummy_stats.character.name = (
            name if name is not None else Consts.charaname_substr_debug + str(random.randint(1, 8))
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
        return self.crnt_clipstats.character.name != ""

    def make_pos_prompt(self) -> str:
        pos_prompt = self.chara_tbl.get(self.crnt_clipstats.character.name, "")
        if pos_prompt == "":
            return ""
        pos_prompt += ",best quality,masterpiece,absurdres,1girl,solo"
        return pos_prompt

    def make_neg_prompt(self) -> str:
        if Consts.charaname_substr_debug in self.crnt_clipstats.character.name:
            # デバッグステータス
            return "TW debug"

        neg_prompt = (
            "(amputee),(bad anatomy),(extra limbs),(missing limb),multiple heads,"
            "worst quality,low quality,motion lines,speed lines,3d,((shiny skin)),worst detail,"
            "text,logo,cropped,deformed,blurry,"
            "extra digits,fewer digits,missing digits,bad hands,mutated hands,"
            "six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,"
            "extra feet,missing foot,bad leg,extra legs,missing leg,"
            "extra hands,missing hand,bad arm,extra arms,missing arm,"
        )
        return neg_prompt
