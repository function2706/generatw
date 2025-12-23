from __future__ import annotations

import copy
import re
from types import MappingProxyType
from typing import Any, Mapping

from picmaker_base import Dict, PicMakerBase


# eratohoTW
class PicMakerReverse(PicMakerBase):
    @property
    # キャラクタプロンプトテーブル
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
                "テスト": "test",
            }
        )

    # コンストラクタ
    def __init__(self, is_verbose: bool):
        super().__init__(is_verbose)

    # モードに即したダミーデータをステータスにセットする
    def set_dummy_stats(self) -> None:
        self.crnt_stats = {}

        self.crnt_stats["character"] = {}
        chara_data = self.crnt_stats["character"]
        chara_data["name"] = "テスト"
        chara_data["status"] = "普通"
        chara_data["equip"] = ["シャツ", "パンツ"]
        chara_data["posture"] = "直立"
        chara_data["tool"] = ["腕時計", "イヤホン"]

    # クリップボード文字列からキャラクタステータスを取得する
    def get_charastats(self, stats: Dict[str, Any]) -> None:
        stats["character"] = {}
        chara_data = stats["character"]
        # キャラ名
        name_match = re.search(r"^\s*(\S+)\s\[LV", self.crnt_clipboard, re.MULTILINE)
        if name_match:
            chara_data["name"] = name_match.group(1)
        name = chara_data["name"]
        # 状態
        status_match = re.search(
            rf"^\s*{re.escape(name)}の状態:\[(\S+)\]", self.crnt_clipboard, re.MULTILINE
        )
        if status_match:
            chara_data["status"] = status_match.group(1)
        # 衣装
        equip_block_match = re.search(
            rf"^\s*{re.escape(name)}の衣装：\s*(?:\[[^\[\]\n]+\])+",
            self.crnt_clipboard,
            re.MULTILINE,
        )
        if equip_block_match:
            chara_data["equip"] = []
            equip_list = chara_data["equip"]
            equip_block = equip_block_match.group(0)
            items = re.findall(r"\[([^\[\]\n]+)\]", equip_block)
            for item in items:
                equip_list.append(item)
        # 姿勢
        posture_match = re.search(
            rf"^\s*現在の姿勢：\S*\[{re.escape(name)}：(\S+)\]", self.crnt_clipboard, re.MULTILINE
        )
        if posture_match:
            chara_data["posture"] = posture_match.group(1)
        # 使用中
        tool_block_match = re.search(
            r"^\s*使用中\s*(?:\[[^\[\]\n]+\])+", self.crnt_clipboard, re.MULTILINE
        )
        if tool_block_match:
            chara_data["tool"] = []
            tool_list = chara_data["tool"]
            tool_block = tool_block_match.group(0)
            items = re.findall(r"\[([^\[\]\n]+)\]", tool_block)
            for item in items:
                tool_list.append(item)

    # クリップボード文字列からキャラクタステータスを取得する
    # 変更が加わる箇所以外は更新されない
    def parse_clipboard(self) -> Dict[str, Any]:
        new_stats = copy.deepcopy(self.crnt_stats)
        if re.search(r"^\s*(\S+)\s\[LV", self.crnt_clipboard, re.MULTILINE):
            self.get_charastats(new_stats)

        return new_stats

    # ステータスがプロンプト生成において十分な情報を有しているか
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

    # ステータスからポジティブプロンプトを生成する
    def make_pos_prompt(self) -> str:
        name = self.crnt_stats["character"]["name"]
        pos_prompt = self.chara_tbl.get(name, "")
        if pos_prompt == "":
            return ""
        pos_prompt += ",best quality,masterpiece,absurdres,1girl,solo"
        return pos_prompt

    # ステータスからネガティブプロンプトを生成する
    def make_neg_prompt(self) -> str:
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
