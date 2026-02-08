import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, TypeAlias

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


SourcePath: TypeAlias = list[str]


@dataclass
class TokenBlueprint:
    """
    プロンプト化のためのトークンデータ
    """

    token: Token = field(default_factory=Token)
    priority: int = 0
    is_stable: bool = False
    source_path: SourcePath = field(default_factory=SourcePath)
    period: int = 0

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

    def append(self, other: Any, sort: bool = False) -> None:
        """
        tokens に要素を追加し, 共通する SourcePath のものは削除する
        """
        if isinstance(other, TokenBlueprint):
            self.tokens = [
                t
                for t in self.tokens
                if not (other.source_path == t.source_path and other.period > t.period)
            ]

            self.tokens.append(other)
        elif isinstance(other, PromptBlueprint):
            for token in other.tokens:
                self.append(token)
        else:
            raise TypeError

        self.dedupe()
        if sort:
            self.sort()

    def sort(self) -> None:
        self.tokens = sorted(self.tokens, key=lambda t: (t.period, t.priority))

    def dedupe(self) -> None:
        best: dict[str, TokenBlueprint] = {}

        for token in self.tokens:
            key = token.token.token
            if key not in best:
                best[key] = token
                continue

            crnt = best[key]
            # weight が大きい方を優先
            if token.token.weight > crnt.token.weight:
                best[key] = token
                continue

            # weight が同じなら priority が小さい方を優先
            if token.token.weight == crnt.token.weight and token.priority < crnt.priority:
                best[key] = token

        self.tokens = list(best.values())

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
        self,
        priority: int,
        is_stable: bool,
        source_path: SourcePath,
        period: int,
        match: str = None,
    ) -> tuple[PromptBlueprint, PromptBlueprint]:
        if self.matches and match and match not in self.matches:
            # default = matches が空, もしくは match 未指定の場合はここに入らない
            return PromptBlueprint(), PromptBlueprint()

        positive = PromptBlueprint()
        negative = PromptBlueprint()

        for token in self.positive.tokens:
            positive.append(
                TokenBlueprint(
                    token=token,
                    priority=priority,
                    is_stable=is_stable,
                    source_path=source_path,
                    period=period,
                ),
                sort=True,
            )
        for token in self.negative.tokens:
            negative.append(
                TokenBlueprint(
                    token=token,
                    priority=priority,
                    is_stable=is_stable,
                    source_path=source_path,
                    period=period,
                ),
                sort=True,
            )
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

    source_path: SourcePath = field(default_factory=list)

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

    def toprompt(self, text: str, period: int) -> tuple[PromptBlueprint, PromptBlueprint]:
        positive = PromptBlueprint()
        negative = PromptBlueprint()

        try:
            if self.re_cache is None:
                self.re_cache = re.compile(self.pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {self.pattern}") from e

        matched_once = False
        for match_itr in self.re_cache.finditer(text):
            matched_once = True
            try:
                match = match_itr.group(self.capturegrp)
            except Exception:
                # キャプチャグループ不正は無視
                continue

            for rule in self.rules:
                pos, neg = rule.toprompt(
                    match=match,
                    priority=self.priority,
                    is_stable=self.is_stable,
                    source_path=self.source_path,
                    period=period,
                )
                positive.append(pos, sort=True)
                negative.append(neg, sort=True)

        if matched_once and self.default and not positive.tokens and not negative.tokens:
            # default
            pos, neg = self.default.toprompt(
                priority=self.priority,
                is_stable=self.is_stable,
                source_path=self.source_path,
                period=period,
            )
            positive.append(pos, sort=True)
            negative.append(neg, sort=True)

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

    def collect_fields(self, node: dict, source_path: SourcePath) -> None:
        if not isinstance(node, dict):
            # str や list は無視
            return

        if KeyName.pattern in node and (KeyName.maps in node or KeyName.ranges in node):
            # 'pattern' キーが存在することを正しい Field の条件とする
            field = Field.make(node)
            field.source_path = source_path.copy()
            self.fields.append(field)
            return

        for k, v in node.items():
            source_path.append(k)
            self.collect_fields(v, source_path)
            source_path.pop()

    @classmethod
    def make(cls, screen_name: str, screen: dict[str, dict[str, Any]]):
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
                source_path: SourcePath = [screen_name, key]
                obj.collect_fields(val, source_path)
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

    def toprompt(self, text: str, period: int) -> tuple[PromptBlueprint, PromptBlueprint]:
        if not self.check_ignition(text):
            return PromptBlueprint(), PromptBlueprint()

        positive = PromptBlueprint()
        negative = PromptBlueprint()
        for fld in self.fields:
            pos, neg = fld.toprompt(text, period=period)
            positive.append(pos, sort=True)
            negative.append(neg, sort=True)

        # 共通プロンプトは常に最後尾
        for token in self.common_positive.tokens:
            positive.append(
                TokenBlueprint(
                    token=token,
                    priority=max(positive.tokens, key=lambda x: x.priority).priority + 1
                    if positive.tokens
                    else 1,
                    is_stable=False,
                    period=period,
                ),
                sort=True,
            )
        for token in self.common_negative.tokens:
            negative.append(
                TokenBlueprint(
                    token=token,
                    priority=max(negative.tokens, key=lambda x: x.priority).priority + 1
                    if negative.tokens
                    else 1,
                    is_stable=False,
                    period=period,
                ),
                sort=True,
            )

        return positive, negative


@dataclass
class Prompter:
    screens: list[Screen] = field(default_factory=list)
    continuing_positive: PromptBlueprint = field(default_factory=PromptBlueprint)
    continuing_negative: PromptBlueprint = field(default_factory=PromptBlueprint)
    period: int = 0

    @classmethod
    def make(cls, yamlpath: Path):
        obj = cls()
        with open(yamlpath, "r", encoding="utf-8") as f:
            yaml_dict: dict = yaml.safe_load(f)
        for key, val in yaml_dict.items():
            obj.screens.append(Screen.make(key, val))
        obj.renumber_priorities()
        return obj

    def renumber_priorities(self) -> None:
        for screen in self.screens:
            screen.sort()

    def toprompt(self, text: str) -> tuple[str, str]:
        positive = PromptBlueprint()
        negative = PromptBlueprint()

        # 継続分を最初に記録
        positive.append(self.continuing_positive, sort=True)
        negative.append(self.continuing_negative, sort=True)

        for screen in self.screens:
            pos, neg = screen.toprompt(text, self.period)
            positive.append(pos, sort=True)
            negative.append(neg, sort=True)

        # 継続分を記録, ただし同じルール元パスのものは更新
        for token in positive.tokens:
            if token.is_stable:
                self.continuing_positive.append(token, sort=True)
        for token in negative.tokens:
            if token.is_stable:
                self.continuing_negative.append(token, sort=True)

        self.period += 1

        return positive.to_promptstr(), negative.to_promptstr()


def json_default(obj: Any) -> str:
    if isinstance(obj, set):
        lst = []
        for e in obj:
            lst.append(e)
        return lst


prompter = Prompter.make("src/debug/parse_test/yamls/testcase1.yaml")
pos, neg = prompter.toprompt("today Name2")
print("POS:", pos)
print("NEG:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase2.yaml")
pos, neg = prompter.toprompt("go id:10")
print("POS:", pos)
print("NEG:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase3.yaml")
pos, neg = prompter.toprompt("go v:B")
print("POS:", pos)
print("NEG:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase3.yaml")
pos, neg = prompter.toprompt("go nothing")
print("POS:", pos)
print("NEG:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase4.yaml")
pos, neg = prompter.toprompt("go x")
print("POS:", pos)
print("NEG:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase5.yaml")
pos, neg = prompter.toprompt("go v:A")
print("POS:", pos)
print("NEG:", neg)
pos, neg = prompter.toprompt("go v:B")
print("POS:", pos)
print("NEG:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase5.yaml")
pos, neg = prompter.toprompt("hello v:A")
print("POS:", pos)
print("NEG:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase6.yaml")
pos, neg = prompter.toprompt("go 8")
print("POS:", pos)
print("NEG:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase7.yaml")
pos, neg = prompter.toprompt("go x")
print("POS:", pos)
print("NEG:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase8.yaml")
pos, neg = prompter.toprompt("go x")
print("POS:", pos)
print("NEG:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/test2.yaml")
pos, neg = prompter.toprompt("start name:alice boost month:04 tag:a tag:b miss:bad side")
print("POS:", pos)
print("NEG:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/test3.yaml")
pos, neg = prompter.toprompt("today name:alice m:03 vibe:happy")
print("POS:", pos)
print("NEG:", neg)
pos, neg = prompter.toprompt("today m:03")
print("POS:", pos)
print("NEG:", neg)
pos, neg = prompter.toprompt("today name:bob boost m:12")
print("POS:", pos)
print("NEG:", neg)
pos, neg = prompter.toprompt("hello name:alice")
print("POS:", pos)
print("NEG:", neg)
pos, neg = prompter.toprompt("sub go mood:good")
print("POS:", pos)
print("NEG:", neg)
pos, neg = prompter.toprompt("sub go")
print("POS:", pos)
print("NEG:", neg)
pos, neg = prompter.toprompt("sub go mood:bad")
print("POS:", pos)
print("NEG:", neg)
