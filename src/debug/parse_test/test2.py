import json
import re
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml


class KeyName(StrEnum):
    ignition = "ignition"
    pattern = "pattern"
    priority = "priority"
    capturegrp = "capturegrp"
    lifetime = "lifetime"
    ruletype = "ruletype"
    maps = "maps"
    ranges = "ranges"
    default = "default"
    table = "table"
    positive = "positive"
    negative = "negative"
    conditions = "conditions"
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


class ValName(StrEnum):
    stable = "stable"
    volatile = "volatile"
    any = "any"
    all = "all"


@dataclass
class Token:
    """
    '(foo:1.2)' -> (token='foo', weight=1.2)
    """

    token: str = ""
    weight: float = 0.0

    @classmethod
    def make(cls, original_token: str):
        m = re.fullmatch(r"\(?([\w\s\-.]+)(?::([0-9.]+))?\)?", original_token.strip())
        if not m:
            return cls()

        token, weight_str = m.groups()
        try:
            weight = float(weight_str) if weight_str is not None else 1.0
        except ValueError:
            weight = 1.0

        return cls(token=token, weight=weight)

    def to_prompt(self) -> str:
        return f"({self.token}:{self.weight})" if self.weight != 1.0 else self.token


@dataclass
class Rule:
    """
    maps:
        {'xxx': {'positive': 'pos1,(pos2:1.2)', 'negative': 'neg1'}}
          -> (['xxx'], [(pos1, 1.0), (pos2, 1.2)], [(neg1, 1.0)])
        {'xxx': {'positive': 'pos1,(pos2:1.2)'}} -> (['xxx'], [(pos1, 1.0), (pos2, 1.2)], [])
        {'xxx': {'negative': 'neg1'} -> (['xxx'], [], [(neg1, 1.0)])}
        {'xxx': 'pos1,(pos2:1.2)'} -> (['xxx'], [(pos1, 1.0), (pos2, 1.2)], [])
    ranges:
        {'pos1,(pos2:1.2)': {'conditions': ['con1', 'con2'], 'negative': 'neg1'}}
          -> (['con1', 'con2'], [(pos1, 1.0), (pos2, 1.2)], [(neg1, 1.0)])
        {'pos1,(pos2:1.2)': ['con1', 'con2']}
          -> (['con1', 'con2'], [(pos1, 1.0), (pos2, 1.2)], [])
    default:
        プロンプトのパース規則は maps と同じ, matchstr は空
    """

    matchstr: list[str] = field(default_factory=list[Token])
    positive: list[Token] = field(default_factory=list[Token])
    negative: list[Token] = field(default_factory=list[Token])

    @classmethod
    def make(cls, key: str, val: str | dict | list, is_maps: bool = True):
        def parse_list(s: str | None) -> list[Token]:
            if s is None or not s:
                return []

            s_str = str(s)
            parts = [p.strip() for p in s_str.split(",") if p.strip()]
            return [Token.make(p) for p in parts]

        key_str = str(key)
        if key_str == KeyName.default:
            matchstr = []
            if isinstance(val, str):
                positive = parse_list(val)
                negative = []
            elif isinstance(val, dict):
                positive = parse_list(val.get(KeyName.positive))
                negative = parse_list(val.get(KeyName.negative))
            else:
                raise ValueError
        elif is_maps:
            matchstr = [key_str]
            if isinstance(val, str):
                # {'xxx': 'pos1,(pos2:1.2)'} 型
                positive = parse_list(val)
                negative = []
            elif isinstance(val, dict):
                positive = parse_list(val.get(KeyName.positive))
                negative = parse_list(val.get(KeyName.negative))
            else:
                raise ValueError
        else:
            positive = parse_list(key_str)
            if isinstance(val, list):
                # {'pos1,(pos2:1.2)': ['con1', 'con2']} 型
                matchstr = [str(i) for i in val]
                negative = []
            elif isinstance(val, dict):
                # {'pos1,(pos2:1.2)': {'conditions': ['con1', 'con2'], 'negative': 'neg1'}} 型
                matchstr = [str(i) for i in val.get(KeyName.conditions, [])]
                negative = parse_list(val.get(KeyName.negative))
            else:
                raise ValueError

        return cls(matchstr=matchstr, positive=positive, negative=negative)


@dataclass
class Field:
    """
    capturegrp, priority, is_stable は指定がなければ 0, -1(最低優先度), False(Volatile)

    {'pattern': '(xxx|yyy)', 'capturegrp': 1, 'priority': 2, 'lifetime': 'stable',
     'maps': {'xxx': {'positive': 'pos1,(pos2:1.2)', 'negative': 'neg1'}, 'yyy': 'pos3,(pos4:1.5)'},
     'default': {'positive': 'defpos1,(defpos2:1.7)', 'negative': 'defneg1'}}
    -> ('(xxx|yyy)', 1, 2, True,
        [
          (['xxx'], [(pos1, 1.0), (pos2, 1.2)], [(neg1, 1.0)]),
          (['yyy'], [(pos3, 1.0), (pos4, 1.5)], [])
        ],
        ([], [(defpos1, 1.0), (defpos2, 1.7)], [(defneg1, 1.0)])
       )
    """

    pattern: str = ""
    capturegrp: int = 0
    priority: int = -1
    is_stable: bool = False
    rules: list[Rule] = field(default_factory=list)
    default: Rule = None

    @classmethod
    def make(cls, field: dict[str, dict]):
        obj = cls()

        if KeyName.pattern in field:
            obj.pattern = field.get(KeyName.pattern)
        else:
            raise ValueError

        if KeyName.capturegrp in field:
            obj.capturegrp = int(field.get(KeyName.capturegrp))

        if KeyName.priority in field:
            obj.priority = int(field.get(KeyName.priority))

        if KeyName.lifetime in field and field.get(KeyName.lifetime) == ValName.stable:
            obj.is_stable = True

        if KeyName.maps in field:
            for key, val in field.get(KeyName.maps).items():
                obj.rules.append(Rule.make(key=key, val=val, is_maps=True))
        elif KeyName.ranges in field:
            for key, val in field.get(KeyName.ranges).items():
                obj.rules.append(Rule.make(key=key, val=val, is_maps=False))
        else:
            raise ValueError

        if KeyName.default in field:
            val = field.get(KeyName.default)
            obj.default = Rule.make(KeyName.default, val)

        return obj


@dataclass
class Screen:
    @dataclass
    class Ignition:
        pattern: str = ""
        is_all: bool = False

    ignition: Ignition = field(default_factory=Ignition)
    fields: list[Field] = field(default_factory=list)
    common_positive: str = ""
    common_negative: str = ""

    def collect_fields(self, node: dict) -> None:
        if not isinstance(node, dict):
            # str や list は無視
            return

        if KeyName.pattern in node:
            # 'pattern' キーが存在することを正しい Field の条件とする
            self.fields.append(Field.make(node))
            return

        for v in node.values():
            self.collect_fields(v)

    @classmethod
    def make(cls, screen: dict[str, dict[str, Any]]):
        obj = cls()

        for key, val in screen.items():
            if key == KeyName.ignition and isinstance(val, dict):
                type, pattern = next(iter(val.items()))
                ignition = cls.Ignition(
                    pattern=pattern, is_all=True if type == ValName.all else False
                )
                obj.ignition = ignition
            elif key == KeyName.POSITIVE and isinstance(val, str):
                obj.common_positive = val
            elif key == KeyName.NEGATIVE and isinstance(val, str):
                obj.common_negative = val
            else:
                obj.collect_fields(val)
        return obj


class Prompter:
    def __init__(self, yamlpath: Path):
        self.screens: list[Screen] = []

        with open(yamlpath, "r", encoding="utf-8") as f:
            yaml_dict: dict = yaml.safe_load(f)
        for _, val in yaml_dict.items():
            self.screens.append(Screen.make(val))


prompter = Prompter("src/debug/parse_test/test.yaml")
for screen in prompter.screens:
    print(json.dumps(asdict(screen), indent=2))
