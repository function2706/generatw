"""
クリップボード監視, GUI 管理, 画像生成管理を実施するモジュールの Reverse 版クラス
"""

from __future__ import annotations

import random
import re
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from types import MappingProxyType
from typing import Any, Dict, List, Mapping

from functions import search_regex
from picmaker_base import PicMakerBase, PMConsts


class State(Enum):
    normal = auto()
    exhausted = auto()  # 疲弊
    debilitated = auto()  # 衰弱
    lethargic = auto()  # 無気力
    dazed = auto()  # 朦朧
    lustful = auto()  # 情欲
    angry = auto()  # 怒り
    bored = auto()  # 退屈
    depressed = auto()  # 鬱屈
    none = auto()


class Opearation(Enum):
    communication_ask_about_her = auto()
    communication_sexual_talk = auto()
    communication_comfort = auto()
    communication_threaten = auto()
    communication_order_undress = auto()
    communication_require_agreement = auto()
    communication_declare_punishment = auto()
    communication_bellow = auto()
    communication_laugh_creepily = auto()

    caress_caress = auto()
    caress_breasts = auto()
    caress_pussy_oral = auto()
    caress_anal = auto()
    caress_anal_oral = auto()
    caress_kiss = auto()
    caress_sumata = auto()
    caress_paizuri = auto()
    caress_footjob = auto()
    caress_vagina = auto()
    caress_push = auto()
    caress_push_down = auto()

    none = auto()


@dataclass
class Character:
    name: str = ""
    state: State = State.none
    equips: List[str] = field(default_factory=list)
    posture: str = ""
    tools: List[str] = field(default_factory=list)

    @classmethod
    def make(cls, s: str):
        def make_name() -> str:
            match = search_regex(s, r"^\s*(\S+)\s\[LV")
            return "" if match is None else match

        def make_state() -> State:
            name = search_regex(s, r"^\s*(\S+)\s\[LV")
            match = search_regex(s, rf"^\s*{re.escape(name)}の状態:\[(\S+)\]")
            if match is None:
                return State.none
            elif match == "疲弊":
                return State.exhausted
            elif match == "衰弱":
                return State.debilitated
            elif match == "無気力":
                return State.lethargic
            elif match == "朦朧":
                return State.dazed
            elif match == "情欲":
                return State.lustful
            elif match == "怒り":
                return State.angry
            elif match == "退屈":
                return State.bored
            elif match == "鬱屈":
                return State.depressed
            else:
                return State.normal

        def make_equips() -> List[str]:
            name = search_regex(s, r"^\s*(\S+)\s\[LV")
            match = search_regex(s, rf"^\s*{re.escape(name)}の衣装：\s*(?:\[[^\[\]\n]+\])+", 0)
            if match is None:
                return []
            equips: List[str] = []
            items = re.findall(r"\[([^\[\]\n]+)\]", match)
            for item in items:
                equips.append(item)
            return equips

        def make_posture() -> str:
            name = search_regex(s, r"^\s*(\S+)\s\[LV")
            match = search_regex(s, rf"^\s*現在の姿勢：\S*\[{re.escape(name)}：(\S+)\]")
            return "" if match is None else match

        def make_tools() -> List[str]:
            match = search_regex(s, r"^\s*使用中\s*(?:\[[^\[\]\n]+\])+", 0)
            if match is None:
                return []
            tools: List[str] = []
            items = re.findall(r"\[([^\[\]\n]+)\]", match)
            for item in items:
                tools.append(item)
            return tools

        return cls(
            name=make_name(),
            state=make_state(),
            equips=make_equips(),
            posture=make_posture(),
            tools=make_tools(),
        )


@dataclass
class Action:
    action: Opearation = Opearation.none

    @classmethod
    def make(cls, s: str):
        def make_action() -> Opearation:
            return Opearation.none

        return cls(action=make_action())


@dataclass
class ReverseStats:
    character: Character = field(default_factory=Character)
    action: Action = field(default_factory=Action)

    def refresh(self, s: str) -> None:
        if search_regex(s, r"^\s*\S+\s\[LV", 0):
            self.character = Character.make(s)
        if search_regex(s, r"hogehoge", 0):
            # T.B.D.
            self.action = Action.make(s)

    def todict(self) -> Dict[str, Any]:
        return asdict(self)


class PicMakerReverse(PicMakerBase[ReverseStats]):
    """
    クリップボード監視, GUI 管理, 画像生成管理を実施するクラス for Reverse
    """

    @property
    def chara_tbl(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "霊夢": "hakurei reimu",
                "魔理沙": "kirisame marisa",
                "ルーミア": "rumia",
                "大妖精": "daiyousei",
                "チルノ": "cirno",
                "紅美鈴": "hong meiling",
                "小悪魔": "koakuma",
                "パチュリー": "patchouli knowledge",
                "咲夜": "izayoi sakuya",
                "レミリア": "remilia scarlet",
                "フランドール": "flandre scarlet",
                "レティ": "letty whiterock",
                "橙": "chen",
                "アリス": "alice margatroid",
                "リリーホワイト": "lily white",
                "リリカ": "lyrica prismriver",
                "メルラン": "merlin prismriver",
                "ルナサ": "lunasa prismriver",
                "妖夢": "konpaku youmu",
                "幽々子": "saigyouji yuyuko",
                "藍": "yakumo ran",
                "紫": "yakumo yukari",
                "萃香": "ibuki suika",
                "リグル": "wriggle nightbug",
                "ミスティア": "mystia lorelei",
                "慧音": "kamishirasawa keine",
                "てゐ": "inaba tewi",
                "鈴仙": "reisen udongein inaba",
                "永琳": "yagokoro eirin",
                "輝夜": "houraisan kaguya",
                "妹紅": "fujiwara no mokou",
                "文": "shameimaru aya",
                "メディスン": "medicine melancholy",
                "幽香": "kazami yuuka",
                "小町": "onozuka komachi",
                "映姫": "shiki eiki",
                "静葉": "aki shizuha",
                "穣子": "aki minoriko",
                "雛": "kagiyama hina",
                "にとり": "kawashiro nitori",
                "椛": "inubashiri momiji",
                "早苗": "kochiya sanae",
                "神奈子": "yasaka kanako",
                "諏訪子": "moriya suwako",
                "サニーミルク": "sunny milk",
                "ルナチャイルド": "luna child",
                "スターサファイア": "star sapphire",
                "阿求": "hieda no akyuu",
                "蓮子": "usami renko",
                "マエリベリー": "maribel hearn",
                "衣玖": "nagae iku",
                "天子": "hinanawi tenshi",
                "豊姫": "watatsuki no toyohime",
                "依姫": "watatsuki no yorihime",
                "レイセン": "reisen \(touhou bougetsushou\)",
                "キスメ": "kisume",
                "ヤマメ": "kurodani yamame",
                "パルスィ": "mizuhashi parsee",
                "勇儀": "hoshiguma yuugi",
                "さとり": "komeiji satori",
                "燐": "kaenbyou rin",
                "空": "reiuji utsuho",
                "こいし": "komeiji koishi",
                "ナズーリン": "nazrin",
                "小傘": "tatara kogasa",
                "一輪": "kumoi ichirin",
                "水蜜": "murasa minamitsu",
                "星": "toramaru shou",
                "白蓮": "hijiri byakuren",
                "ぬえ": "houjuu nue",
                "はたて": "himekaidou hatate",
                "華扇": "ibaraki kasen",
                "響子": "kasodani kyouko",
                "芳香": "miyako yoshika",
                "青娥": "kaku seiga",
                "屠自古": "soga no tojiko,ghost tail",
                "布都": "mononobe no futo",
                "神子": "toyosatomimi no miko",
                "マミゾウ": "futatsuiwa mamizou",
                "小鈴": "motoori kosuzu",
                "こころ": "hata no kokoro",
                "わかさぎ姫": "wakasagihime",
                "赤蛮奇": "sekibanki",
                "影狼": "imaizumi kagerou",
                "弁々": "tsukumo benben",
                "八橋": "tsukumo yatsuhashi",
                "正邪": "kijin seija",
                "針妙丸": "sukuna shinmyoumaru",
                "雷鼓": "horikawa raiko",
                "菫子": "usami sumireko",
                "清蘭": "seiran \(touhou\)",
                "鈴瑚": "ringo \(touhou\)",
                "ドレミー": "doremy sweet",
                "サグメ": "kishin sagume",
                "クラウンピース": "clownpiece",
                "純狐": "junko \(touhou\)",
                "ヘカーティア": "hecatia lapislazuli",
                "エタニティラルバ": "eternity larva",
                "ネムノ": "sakata nemuno,sharp teeth",
                "あうん": "komano aunn",
                "成美": "yatadera narumi",
                "舞": "teireida mai",
                "里乃": "nishida satono",
                "隠岐奈": "matara okina",
                "女苑": "yorigami jo'on,tsurime",
                "紫苑": "yorigami shion",
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
        super().__init__(ReverseStats())

    def make_dummy_stats(self, name: str = None) -> ReverseStats:
        dummy_stats = ReverseStats()
        dummy_stats.character.name = (
            name
            if name is not None
            else PMConsts.charaname_substr_debug + str(random.randint(1, 8))
        )
        dummy_stats.character.state = State.normal
        dummy_stats.character.equips = ["シャツ", "パンツ"]
        dummy_stats.character.posture = "直立"
        dummy_stats.character.tools = ["腕時計", "イヤホン"]
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
            return "R debug"

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
