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
            raise ValueError

        token, weight_str = m.groups()
        try:
            weight = float(weight_str) if weight_str is not None else 1.0
        except ValueError:
            weight = 1.0

        return cls(token=token, weight=weight)


@dataclass
class TokenSet:
    """
    token1,(token2:1.2),token3 -> [(token1, 1.0), (token2, 1.2), (token3, 1.0)]
    """

    tokens: list[Token] = field(default_factory=list)

    @classmethod
    def make(cls, text: str | None):
        if text is None or not text:
            return cls()

        text_str = str(text)
        parts = [p.strip() for p in text_str.split(",") if p.strip()]
        return cls(tokens=[Token.make(p) for p in parts])


@dataclass
class TokenBlueprint:
    """
    プロンプト化のためのトークンデータ
    """

    token: Token = field(default_factory=Token)
    priority: int = 0
    is_stable: bool = False

    def to_promptstr(self) -> str:
        return (
            f"({self.token.token}:{self.token.weight})"
            if self.token.weight != 1.0
            else self.token.token
        )


@dataclass
class PromptBlueprint:
    """
    プロンプト化のためのトークンの集合とその処理を司るクラス
    """

    tokens: list[TokenBlueprint] = field(default_factory=list)

    def append(self, token: Token, priority: int, is_stable: bool):
        self.tokens.append(TokenBlueprint(token=token, priority=priority, is_stable=is_stable))
        self.sort()

    def __iadd__(self, other):
        if not isinstance(other, PromptBlueprint):
            raise TypeError
        self.tokens += other.tokens
        self.sort()
        return self

    def sort(self) -> None:
        self.tokens = sorted(self.tokens, key=lambda t: t.priority)

    # 優先度解決, 多重プロンプト解決, 文字列化

    def to_promptstr(self) -> str:
        tokenstrs = []
        for token in self.tokens:
            tokenstrs.append(token.to_promptstr())
        return ",".join(filter(None, tokenstrs))


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

    matches: set[str] = field(default_factory=set)
    positive: TokenSet = field(default_factory=TokenSet)
    negative: TokenSet = field(default_factory=TokenSet)

    @classmethod
    def make(cls, key: str, val: str | dict | list, is_maps: bool = True):
        key_str = str(key)
        if key_str == KeyName.default:
            matches = set()
            if isinstance(val, str):
                positive = TokenSet.make(val)
                negative = TokenSet()
            elif isinstance(val, dict):
                positive = TokenSet.make(val.get(KeyName.positive))
                negative = TokenSet.make(val.get(KeyName.negative))
            else:
                raise ValueError
        elif is_maps:
            matches = {key_str}
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
                matches = {str(i) for i in val}
                negative = TokenSet()
            elif isinstance(val, dict):
                # {'pos1,(pos2:1.2)': {'conditions': ['con1', 'con2'], 'negative': 'neg1'}} 型
                matches = {str(i) for i in val.get(KeyName.conditions, [])}
                negative = TokenSet.make(val.get(KeyName.negative))
            else:
                raise ValueError

        return cls(matches=matches, positive=positive, negative=negative)

    def toprompt(
        self, priority: int, is_stable: bool, match: str = None
    ) -> tuple[PromptBlueprint, PromptBlueprint]:
        if self.matches and match and match not in self.matches:
            # default = matches が空, もしくは match 未指定の場合はここに入らない
            return PromptBlueprint(), PromptBlueprint()

        positive = PromptBlueprint()
        negative = PromptBlueprint()

        for token in self.positive.tokens:
            positive.append(token=token, priority=priority, is_stable=is_stable)
        for token in self.negative.tokens:
            negative.append(token=token, priority=priority, is_stable=is_stable)
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
    default: Rule | None = None

    re_cache: re.Pattern[str] = field(default=None, init=False, repr=False, compare=False)

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

    def toprompt(self, text: str) -> tuple[PromptBlueprint, PromptBlueprint]:
        positive = PromptBlueprint()
        negative = PromptBlueprint()

        try:
            if self.re_cache is None:
                self.re_cache = re.compile(self.pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {self.pattern}") from e

        for match_itr in self.re_cache.finditer(text):
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

        if self.default and not positive.tokens and not negative.tokens:
            # default
            pos, neg = self.default.toprompt(priority=self.priority, is_stable=self.is_stable)
            positive += pos
            negative += neg

        return positive, negative


@dataclass
class Screen:
    @dataclass
    class Ignition:
        patterns: list[str] = field(default_factory=list)
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
        if not self.ignition.patterns:
            return False

        if self.ignition.is_all:
            return all(re.search(p, text) for p in self.ignition.patterns)
        else:
            return any(re.search(p, text) for p in self.ignition.patterns)

    def toprompt(self, text: str) -> tuple[PromptBlueprint, PromptBlueprint]:
        if not self.check_ignition(text):
            return PromptBlueprint(), PromptBlueprint()

        positive = PromptBlueprint()
        negative = PromptBlueprint()
        for fld in self.fields:
            pos, neg = fld.toprompt(text)
            positive += pos
            negative += neg

        # 共通プロンプトは常に最後尾
        for token in self.common_positive.tokens:
            positive.append(token=token, priority=len(positive.tokens) + 1, is_stable=False)
        for token in self.common_negative.tokens:
            negative.append(token=token, priority=len(negative.tokens) + 1, is_stable=False)

        return positive, negative


@dataclass
class Prompter:
    screens: list[Screen] = field(default_factory=list)
    continuing_tokens: PromptBlueprint = field(default_factory=PromptBlueprint)

    @classmethod
    def make(cls, yamlpath: Path):
        obj = cls()
        with open(yamlpath, "r", encoding="utf-8") as f:
            yaml_dict: dict = yaml.safe_load(f)
        for _, val in yaml_dict.items():
            obj.screens.append(Screen.make(val))
        obj.renumber_priorities()
        return obj

    def renumber_priorities(self) -> None:
        for screen in self.screens:
            screen.sort()

    def toprompt(self, text: str) -> tuple[str, str]:
        positive = PromptBlueprint()
        negative = PromptBlueprint()
        for screen in self.screens:
            pos, neg = screen.toprompt(text)
            positive += pos
            negative += neg

        print("pos----------------------------------")
        for token in positive.tokens:
            print(json.dumps(asdict(token), indent=2))
        print("neg----------------------------------")
        for token in negative.tokens:
            print(json.dumps(asdict(token), indent=2))
        return positive.to_promptstr(), negative.to_promptstr()


def json_default(obj: Any) -> str:
    if isinstance(obj, set):
        lst = []
        for e in obj:
            lst.append(e)
        return lst


prompter = Prompter.make("src/debug/parse_test/test.yaml")
pos, neg = prompter.toprompt("today: 2026/02/05, Name2 (vibe: )foobarBarFugahogeHogeBazbaz")
# for s=creen in prompter.screens:
#    print(json.dumps(asdict(screen), indent=2, default=json_default))
print("POS:", pos)
print("NEG:", neg)
