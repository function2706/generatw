import json
import re
from collections import defaultdict
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


@dataclass(frozen=True)
class Consts:
    lowest_priority = -1


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
class TokenSet:
    """
    token1,(token2:1.2),token3 -> [(token1, 1.0), (token2, 1.2), (token3, 1.0)]
    """

    tokens: list[Token] = field(default_factory=list)

    @classmethod
    def make(cls, text: str | None):
        if text is None or not text:
            return cls(tokens=[])

        text_str = str(text)
        parts = [p.strip() for p in text_str.split(",") if p.strip()]
        return cls(tokens=[Token.make(p) for p in parts])

    def toprompt(self) -> str:
        return ",".join(token.to_prompt() for token in self.tokens)


@dataclass
class PromptBlueprint:
    token: Token = None
    priority: int = 0
    is_stable: bool = False


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

    matches: list[str] = field(default_factory=list)
    positive: TokenSet = field(default_factory=TokenSet)
    negative: TokenSet = field(default_factory=TokenSet)

    @classmethod
    def make(cls, key: str, val: str | dict | list, is_maps: bool = True):
        key_str = str(key)
        if key_str == KeyName.default:
            matches = []
            if isinstance(val, str):
                positive = TokenSet.make(val)
                negative = TokenSet()
            elif isinstance(val, dict):
                positive = TokenSet.make(val.get(KeyName.positive))
                negative = TokenSet.make(val.get(KeyName.negative))
            else:
                raise ValueError
        elif is_maps:
            matches = [key_str]
            if isinstance(val, str):
                # {'xxx': 'pos1,(pos2:1.2)'} 型
                positive = TokenSet.make(val)
                negative = TokenSet()
            elif isinstance(val, dict):
                positive = TokenSet.make(val.get(KeyName.positive))
                negative = TokenSet.make(val.get(KeyName.negative))
            else:
                raise ValueError
        else:
            positive = TokenSet.make(key_str)
            if isinstance(val, list):
                # {'pos1,(pos2:1.2)': ['con1', 'con2']} 型
                matches = [str(i) for i in val]
                negative = TokenSet()
            elif isinstance(val, dict):
                # {'pos1,(pos2:1.2)': {'conditions': ['con1', 'con2'], 'negative': 'neg1'}} 型
                matches = [str(i) for i in val.get(KeyName.conditions, [])]
                negative = TokenSet.make(val.get(KeyName.negative))
            else:
                raise ValueError

        return cls(matches=matches, positive=positive, negative=negative)

    def toprompt(
        self, priority: int, is_stable: bool, match: str = None
    ) -> tuple[list[PromptBlueprint], list[PromptBlueprint]]:
        if self.matches and match and match not in self.matches:
            # default = matches が空, もしくは match 未指定の場合はここに入らない
            return [], []

        positive: list[PromptBlueprint] = []
        negative: list[PromptBlueprint] = []

        for token in self.positive.tokens:
            positive.append(PromptBlueprint(token=token, priority=priority, is_stable=is_stable))
        for token in self.negative.tokens:
            negative.append(PromptBlueprint(token=token, priority=priority, is_stable=is_stable))
        return positive, negative


@dataclass
class Field:
    """
    capturegrp, priority, is_stable は指定がなければ 0, lowest_priority(最低優先度), False(Volatile)

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
    priority: int = Consts.lowest_priority
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

    def toprompt(self, text: str) -> tuple[list[PromptBlueprint], list[PromptBlueprint]]:
        positive: list[PromptBlueprint] = []
        negative: list[PromptBlueprint] = []

        try:
            match_itrs = re.finditer(self.pattern, text)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {self.pattern}") from e

        for match_itr in match_itrs:
            try:
                match = match_itr.group(self.capturegrp)
            except Exception:
                # キャプチャグループ不正は無視
                continue

            for rule in self.rules:
                pos, neg = rule.toprompt(
                    match=match, priority=self.priority, is_stable=self.is_stable
                )
                positive += pos
                negative += neg

            if not positive and not negative:
                # default
                pos, neg = self.default.toprompt(priority=self.priority, is_stable=self.is_stable)
                positive += pos
                negative += neg

        return positive, negative


@dataclass
class Screen:
    @dataclass
    class Ignition:
        patterns: list[str] = None
        is_all: bool = False

    ignition: Ignition = field(default_factory=Ignition)
    fields: list[Field] = field(default_factory=list)
    common_positive: TokenSet = field(default_factory=TokenSet)
    common_negative: TokenSet = field(default_factory=TokenSet)

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
                type, patterns = next(iter(val.items()))
                if isinstance(patterns, str):
                    pattern_str = patterns
                    patterns = []
                    patterns.append(pattern_str)
                obj.ignition = cls.Ignition(
                    patterns=[str(x) for x in patterns],
                    is_all=True if type == ValName.all else False,
                )
            elif key == KeyName.POSITIVE and isinstance(val, str):
                obj.common_positive = TokenSet.make(val)
            elif key == KeyName.NEGATIVE and isinstance(val, str):
                obj.common_negative = TokenSet.make(val)
            else:
                obj.collect_fields(val)
        return obj

    def sort(self) -> None:
        # バケット: 値 -> 出現 index のリスト
        buckets = defaultdict(list)
        for idx, fld in enumerate(self.fields):
            buckets[fld.priority].append(idx)

        # lowest_priority は最後に回すため除外してソート
        keys = sorted(k for k in buckets.keys() if k != Consts.lowest_priority)
        # 結果配列（初期値は元の値をコピー）
        result = list(self.fields)

        crnt_priority = 1  # 連番カウンタ
        for k in keys:
            # 元の値が 1,2,3,... の場合のみ連番を振る
            if k != Consts.lowest_priority:
                for idx in buckets[k]:
                    result[idx].priority = crnt_priority
                    crnt_priority += 1

        if Consts.lowest_priority in buckets:
            # 最後に lowest_priority を処理
            for idx in buckets[Consts.lowest_priority]:
                result[idx].priority = crnt_priority
                crnt_priority += 1

        self.fields = result

    def check_ignition(self, text: str) -> bool:
        if self.ignition.is_all:
            return all(re.search(p, text) for p in self.ignition.patterns)
        else:
            return any(re.search(p, text) for p in self.ignition.patterns)

    def toprompt(self, text: str) -> tuple[list[PromptBlueprint], list[PromptBlueprint]]:
        if not self.check_ignition(text):
            return [], []

        positive: list[PromptBlueprint] = []
        negative: list[PromptBlueprint] = []
        for fld in self.fields:
            pos, neg = fld.toprompt(text)
            positive += pos
            negative += neg

        return positive, negative


@dataclass
class Prompter:
    screens: list[Screen] = field(default_factory=list)
    continuing_tokens: list[PromptBlueprint] = field(default_factory=list)

    @classmethod
    def make(cls, yamlpath: Path):
        obj = cls()
        with open(yamlpath, "r", encoding="utf-8") as f:
            yaml_dict: dict = yaml.safe_load(f)
        for _, val in yaml_dict.items():
            obj.screens.append(Screen.make(val))
        obj.sort()
        return obj

    def sort(self) -> None:
        for screen in self.screens:
            screen.sort()

    def toprompt(self, text: str):
        positive: list[PromptBlueprint] = []
        negative: list[PromptBlueprint] = []
        for screen in self.screens:
            pos, neg = screen.toprompt(text)
            positive += pos
            negative += neg

        for blueprint in positive:
            print(json.dumps(asdict(blueprint), indent=2))
        for blueprint in negative:
            print(json.dumps(asdict(blueprint), indent=2))
        return ""


prompter = Prompter.make("src/debug/parse_test/test.yaml")
prompter.toprompt("today: 2026/02/05, Name1 (vibe: Vibe) sunny")
# for screen in prompter.screens:
# print(json.dumps(asdict(screen), indent=2))
