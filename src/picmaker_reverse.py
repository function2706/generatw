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
                "霊夢": r"hakurei reimu",
                "魔理沙": r"kirisame marisa",
                "ルーミア": r"rumia",
                "大妖精": r"daiyousei",
                "チルノ": r"cirno",
                "紅美鈴": r"hong meiling",
                "小悪魔": r"koakuma",
                "パチュリー": r"patchouli knowledge",
                "咲夜": r"izayoi sakuya",
                "レミリア": r"remilia scarlet",
                "フランドール": r"flandre scarlet",
                "レティ": r"letty whiterock",
                "橙": r"chen",
                "アリス": r"alice margatroid",
                "リリーホワイト": r"lily white",
                "リリカ": r"lyrica prismriver",
                "メルラン": r"merlin prismriver",
                "ルナサ": r"lunasa prismriver",
                "妖夢": r"konpaku youmu",
                "幽々子": r"saigyouji yuyuko",
                "藍": r"yakumo ran",
                "紫": r"yakumo yukari",
                "萃香": r"ibuki suika",
                "リグル": r"wriggle nightbug",
                "ミスティア": r"mystia lorelei",
                "慧音": r"kamishirasawa keine",
                "てゐ": r"inaba tewi",
                "鈴仙": r"reisen udongein inaba",
                "永琳": r"yagokoro eirin",
                "輝夜": r"houraisan kaguya",
                "妹紅": r"fujiwara no mokou",
                "文": r"shameimaru aya",
                "メディスン": r"medicine melancholy",
                "幽香": r"kazami yuuka",
                "小町": r"onozuka komachi",
                "映姫": r"shiki eiki",
                "静葉": r"aki shizuha",
                "穣子": r"aki minoriko",
                "雛": r"kagiyama hina",
                "にとり": r"kawashiro nitori",
                "椛": r"inubashiri momiji",
                "早苗": r"kochiya sanae",
                "神奈子": r"yasaka kanako",
                "諏訪子": r"moriya suwako",
                "サニーミルク": r"sunny milk",
                "ルナチャイルド": r"luna child",
                "スターサファイア": r"star sapphire",
                "阿求": r"hieda no akyuu",
                "蓮子": r"usami renko",
                "マエリベリー": r"maribel hearn",
                "衣玖": r"nagae iku",
                "天子": r"hinanawi tenshi",
                "豊姫": r"watatsuki no toyohime",
                "依姫": r"watatsuki no yorihime",
                "レイセン": r"reisen \(touhou bougetsushou\)",
                "キスメ": r"kisume",
                "ヤマメ": r"kurodani yamame",
                "パルスィ": r"mizuhashi parsee",
                "勇儀": r"hoshiguma yuugi",
                "さとり": r"komeiji satori",
                "燐": r"kaenbyou rin",
                "空": r"reiuji utsuho",
                "こいし": r"komeiji koishi",
                "ナズーリン": r"nazrin",
                "小傘": r"tatara kogasa",
                "一輪": r"kumoi ichirin",
                "水蜜": r"murasa minamitsu",
                "星": r"toramaru shou",
                "白蓮": r"hijiri byakuren",
                "ぬえ": r"houjuu nue",
                "はたて": r"himekaidou hatate",
                "華扇": r"ibaraki kasen",
                "響子": r"kasodani kyouko",
                "芳香": r"miyako yoshika",
                "青娥": r"kaku seiga",
                "屠自古": r"soga no tojiko,ghost tail",
                "布都": r"mononobe no futo",
                "神子": r"toyosatomimi no miko",
                "マミゾウ": r"futatsuiwa mamizou",
                "小鈴": r"motoori kosuzu",
                "こころ": r"hata no kokoro",
                "わかさぎ姫": r"wakasagihime",
                "赤蛮奇": r"sekibanki",
                "影狼": r"imaizumi kagerou",
                "弁々": r"tsukumo benben",
                "八橋": r"tsukumo yatsuhashi",
                "正邪": r"kijin seija",
                "針妙丸": r"sukuna shinmyoumaru",
                "雷鼓": r"horikawa raiko",
                "菫子": r"usami sumireko",
                "清蘭": r"seiran \(touhou\)",
                "鈴瑚": r"ringo \(touhou\)",
                "ドレミー": r"doremy sweet",
                "サグメ": r"kishin sagume",
                "クラウンピース": r"clownpiece",
                "純狐": r"junko \(touhou\)",
                "ヘカーティア": r"hecatia lapislazuli",
                "エタニティラルバ": r"eternity larva",
                "ネムノ": r"sakata nemuno,sharp teeth",
                "あうん": r"komano aunn",
                "成美": r"yatadera narumi",
                "舞": r"teireida mai",
                "里乃": r"nishida satono",
                "隠岐奈": r"matara okina",
                "女苑": r"yorigami jo'on,tsurime",
                "紫苑": r"yorigami shion",
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
