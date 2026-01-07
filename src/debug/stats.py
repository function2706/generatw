import json
import re
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List

import pyperclip


def json_default(o):
    if isinstance(o, Enum):
        return o.name
    raise TypeError(f"{o.__class__.__name__} is not JSON serializable")


def dump_json(data: Dict, label: str) -> None:
    """
    指定の Dict を json 形式でダンプする

    Args:
        data (Dict): ダンプ対象
        label (str): 表示するラベル("label": {...})
    """
    print(f'"{label}":')
    print(json.dumps(data, ensure_ascii=False, indent=2, default=json_default))


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


def search_regex(s: str, regex: str, gridx: int = 1) -> str:
    m = re.search(regex, s, flags=re.MULTILINE)
    if not m:
        print(f'No match with "{regex}".')
        return None
    return m.group(gridx)


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
class Stats:
    character: Character
    action: Action

    @classmethod
    def make(cls, s: str):
        character_lc = Character.make(s)
        action_lc = Action.make(s)
        return cls(character=character_lc, action=action_lc)

    def todict(self) -> Dict[str, Any]:
        return asdict(self)


clipboard = pyperclip.paste()

a = Stats.make(clipboard)
dump_json(a.todict(), "test")
# print(a.todict())
