from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from enum import Enum, StrEnum, auto
from pathlib import Path
from typing import Any, Iterable

import yaml


class KeyName(StrEnum):
    """YAML設定ファイルで使用されるキー名の定数"""

    ignition = "ignition"
    any = "any"
    all = "all"
    pattern = "pattern"
    priority = "priority"
    capturegrp = "capturegrp"
    lifetime = "lifetime"
    stable = "stable"
    volatile = "volatile"
    ruletype = "ruletype"
    maps = "maps"
    ranges = "ranges"
    intervals = "intervals"
    add = "add"
    remove = "remove"
    with_k = "with"
    not_k = "not"
    default = "default"
    essential = "essential"
    global_k = "global"
    local = "local"
    positive = "positive"
    negative = "negative"
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


@dataclass(frozen=True)
class Consts:
    """システム全体で使用される定数"""

    lowest_priority = -1
    rule_path_root = "<root>"  # すべてのルールパスが有する原点


@dataclass
class Token:
    """
    重み付きトークンを表すクラス\n
    例: '(foo:1.2)' -> Token(token='foo', weight=1.2)

    Attributes:
        token (str): トークン文字列
        weight (float): トークンの重み
    """

    token: str = ""
    weight: float = 0.0

    @classmethod
    def make(cls, original_token: str):
        """
        文字列からTokenインスタンスを生成する

        Args:
            original_token (str): 元のトークン文字列('word' または '(word:1.2)' 形式)

        Returns:
            Token: 生成されたTokenインスタンス

        Raises:
            ValueError: トークンの形式が不正な場合
        """
        m = re.fullmatch(r"\(?([\w\s\-\(\)\\'.]+)(?::([0-9.]+))?\)?", original_token.strip())
        if not m:
            raise ValueError(
                f"Invalid token format: '{original_token}'. Expected 'word' or '(word:1.2)'."
            )

        token, weight_str = m.groups()
        try:
            weight = float(weight_str) if weight_str is not None else 1.0
        except ValueError:
            weight = 1.0

        return cls(token=token, weight=weight)


@dataclass
class TokenSet:
    """
    複数の重み付きトークンの集合を表すクラス\n
    例: 'token1,(token2:1.2),token3'
        -> [Token('token1', 1.0), Token('token2', 1.2), Token('token3', 1.0)]

    Attributes:
        tokens (list[Token]): トークンのリスト
    """

    tokens: list[Token] = field(default_factory=list)

    @classmethod
    def make(cls, text: str | None = None):
        """
        カンマ区切りの文字列からTokenSetインスタンスを生成する

        Args:
            text (str | None): カンマ区切りのトークン文字列

        Returns:
            TokenSet: 生成されたTokenSetインスタンス
        """
        if text is None or not text:
            return cls(tokens=[Token()])

        text_str = str(text)
        parts = [p.strip() for p in text_str.split(",") if p.strip()]
        return cls(tokens=[Token.make(p) for p in parts])


class RulePath(tuple[str, ...]):
    @property
    def id(self) -> str:
        return self[-1]


@dataclass
class TokenBlueprint:
    """
    プロンプト化のためのトークンデータ\n
    トークン本体に加えて, 優先度や安定性などのメタデータを保持する

    Attributes:
        token (Token): トークン本体
        priority (int): 優先度(小さいほど高優先)
        is_stable (bool): 安定フラグ(True の場合は次回以降も継続)
        rule_path (RulePath): ルールパス(YAML内の階層)
        period (int): 生成された世代番号
        condition (Condition): このトークンが採用された際の条件式
    """

    token: Token = field(default_factory=Token)
    priority: int = 0
    is_stable: bool = False
    rule_path: RulePath = RulePath((Consts.rule_path_root,))
    period: int = 0
    condition: Condition = None

    def evaluate(self, active_flags: set[str]) -> bool:
        return self.condition is None or self.condition.evaluate(active_flags)

    def to_promptstr(self) -> str:
        """
        プロンプト文字列に変換する

        Returns:
            str: プロンプト文字列('token' または '(token:weight)' 形式)
        """
        return (
            f"({self.token.token}:{self.token.weight})"
            if self.token.weight != 1.0
            else self.token.token
        )


@dataclass
class PromptBlueprint:
    """
    プロンプト化のためのトークンの集合とその処理を司るクラス\n
    複数のTokenBlueprintを管理し, 重複排除やソートを行う

    Attributes:
        tokens (list[TokenBlueprint]): トークンのリスト
    """

    tokens: list[TokenBlueprint] = field(default_factory=list)

    def append(self, other: Any) -> None:
        """
        tokens に要素を追加し, 共通する Rule ID のものは削除する\n
        より新しい period を持つトークンで既存のトークンを上書きする

        Args:
            other (TokenBlueprint | PromptBlueprint): 追加する要素

        Raises:
            TypeError: 引数の型が不正な場合
        """
        if isinstance(other, TokenBlueprint):
            # 既存のトークンから追加トークンと同じルール ID で古い世代のものを除く
            self.tokens = [
                t
                for t in self.tokens
                if not (other.rule_path.id == t.rule_path.id and other.period > t.period)
            ]

            self.tokens.append(other)
        elif isinstance(other, PromptBlueprint):
            for token in other.tokens:
                self.append(token)
        else:
            raise TypeError(
                f"Cannot append {type(other).__name__} to PromptBlueprint."
                " Expected TokenBlueprint or PromptBlueprint."
            )

    def sort(self) -> None:
        """トークンを period と priority でソートする"""
        self.tokens = sorted(self.tokens, key=lambda t: (t.period, t.priority))

    def dedupe(self) -> None:
        """
        重複するトークンを排除する\n
        同じトークン文字列が複数ある場合, より高い weight を持つものを優先し,\n
        weight が同じ場合はより小さい priority を持つものを優先する
        """
        best: dict[str, TokenBlueprint] = {}

        for token in self.tokens:
            if not token.token.token:
                # 空文字列(=period 更新時の相方のトークン削除用)は全て残したい
                continue

            key = token.token.token
            if key not in best:
                best[key] = token
                continue

            crnt = best[key]
            if (token.token.weight > crnt.token.weight) or (
                token.token.weight == crnt.token.weight and token.priority < crnt.priority
            ):
                best[key] = token

        self.tokens = list(best.values())

    def to_promptstr(self) -> str:
        """
        プロンプト文字列に変換する\n
        重複排除とソートを行った後, カンマ区切りの文字列を生成する

        Returns:
            str: カンマ区切りのプロンプト文字列
        """
        self.dedupe()
        self.sort()
        return ",".join(t.to_promptstr() for t in self.tokens if t.token.token)


class RuleType(Enum):
    maps = auto()
    ranges = auto()
    intervals = auto()
    default = auto()


@dataclass
class Condition:
    def evaluate(self, flags: set[str]) -> bool:
        raise NotImplementedError


@dataclass
class Atom(Condition):
    ATOM: str

    def evaluate(self, flags: set[str]) -> bool:
        return self.ATOM in flags


@dataclass
class NotCond(Condition):
    NOT: Condition

    def evaluate(self, flags: set[str]) -> bool:
        return not self.NOT.evaluate(flags)


@dataclass
class AnyCond(Condition):
    ANY: Iterable[Condition]

    def evaluate(self, flags: set[str]) -> bool:
        return any(t.evaluate(flags) for t in self.ANY)


@dataclass
class AllCond(Condition):
    ALL: Iterable[Condition]

    def evaluate(self, flags: set[str]) -> bool:
        return all(t.evaluate(flags) for t in self.ALL)


def parse_condition(obj: str | dict) -> Condition:
    if isinstance(obj, str):
        return Atom(obj)

    if isinstance(obj, dict):
        if "not" in obj:
            return NotCond(parse_condition(obj["not"]))
        if "any" in obj:
            return AnyCond([parse_condition(x) for x in obj["any"]])
        if "all" in obj:
            return AllCond([parse_condition(x) for x in obj["all"]])

    raise ValueError(f"Invalid condition: {obj}")


@dataclass
class SyringeNeedle:
    """
    Prompter から下層のクラスまでデータを注入するためのクラス\n
    Dynamic メンバは下層で編集されることに注意
    """

    @dataclass
    class Static:
        """
        YAML 正規化の際に固定化される静的データ

        Attributes:
            stable_rules (set[str]): stable なルールの一覧
            goal_global_essentials (set[str]): Screen を超越して不可欠なルールの一覧
        """

        priority_tbl: dict[str, int] = field(default_factory=dict)
        stable_rules: set[str] = field(default_factory=set)
        goal_global_essentials: set[str] = field(default_factory=set)

    @dataclass
    class Dynamic:
        """
        プロンプト化の際に動的に更新される動的データ

        Attributes:
            period (int): 現在の世代番号
            active_flags (set[str]): アクティブなフラグの集合
            achieved_essentials (set[str]): 達成済みの不可欠ルールの一覧
            empty_tokens_rule_ids (set[str]): 空トークン判定のルール ID
        """

        period: int = 0
        active_flags: set[str] = field(default_factory=set)
        achieved_essentials: set[str] = field(default_factory=set)
        empty_tokens_rule_ids: set[str] = field(default_factory=set)

    static: Static = field(default_factory=Static)
    dynamic: Dynamic = field(default_factory=Dynamic)


@dataclass
class Rule:
    """
    マッチ条件とプロンプトの対応関係を定義するクラス\n
    maps形式またはranges形式で定義される

    例:
        maps: {'xxx': {'positive': 'pos1,(pos2:1.2)', 'negative': 'neg1'}}\n
          -> Rule(matches={'xxx'}, positive=TokenSet([...]), negative=TokenSet([...]))\n
        ranges: {'pos1,(pos2:1.2)': ['con1', 'con2']}\n
          -> Rule(matches={'con1', 'con2'}, positive=TokenSet([...]), negative=TokenSet([]))
        interval: {'pos1,(pos2:1.2)': [min, max]}\n
          -> Rule(interval=(min, max), positive=TokenSet([...]), negative=TokenSet([]))

    Attributes:
        matches (set[str]): マッチ対象文字列の集合 (ranges の場合は複数要素となるため set)
        interval (tuple[float, float]): interval の場合の最大値と最小値
        positive (TokenSet): ポジティブプロンプトのトークン集合
        negative (TokenSet): ネガティブプロンプトのトークン集合
        flags_pm (list[set[str]]): マッチした際にセット/アンセットするフラグの集合(非順不同)
        condition (Condition): このルールが適用されるフラグ条件
    """

    matches: set[str] = field(default_factory=set)
    interval: tuple[float, float] = field(default_factory=tuple)
    positive: TokenSet = field(default_factory=TokenSet)
    negative: TokenSet = field(default_factory=TokenSet)
    flags_pm: list[dict[str, set[str]]] = field(default_factory=list)
    condition: Condition = None

    @classmethod
    def make(cls, key: str, val: str | dict | list, ruletype: RuleType):
        """
        YAML の定義から Rule インスタンスを生成する

        Args:
            key (str): ルールのキー
            val (str | dict | list): ルールの値
            ruletype (RuleType): maps / ranges / interval

        Returns:
            Rule: 生成されたRuleインスタンス

        Raises:
            ValueError: 定義形式が不正な場合
        """
        obj = cls()

        # with 節は初めにパース
        if isinstance(val, dict) and KeyName.with_k in val:
            obj.condition = parse_condition(val.get(KeyName.with_k))

        if isinstance(val, dict):
            for k, v in val.items():
                lst_v = [v] if isinstance(v, str) else v
                if k == KeyName.add:
                    obj.flags_pm.append({KeyName.add: set(lst_v)})
                elif k == KeyName.remove:
                    obj.flags_pm.append({KeyName.remove: set(lst_v)})

        key_str = str(key)
        if ruletype == RuleType.default:
            obj.matches = set()
            obj.interval = tuple()
            if isinstance(val, str):
                obj.positive = TokenSet.make(val)
                obj.negative = TokenSet.make()
            elif isinstance(val, dict):
                obj.positive = TokenSet.make(val.get(KeyName.positive))
                obj.negative = TokenSet.make(val.get(KeyName.negative))
            else:
                raise ValueError
        elif ruletype == RuleType.maps:
            obj.matches = {key_str}
            obj.interval = tuple()
            if isinstance(val, str):
                # {'xxx': 'pos1,(pos2:1.2)'} 型
                obj.positive = TokenSet.make(val)
                obj.negative = TokenSet.make()
            elif isinstance(val, dict):
                obj.positive = TokenSet.make(val.get(KeyName.positive))
                obj.negative = TokenSet.make(val.get(KeyName.negative))
            else:
                raise ValueError(
                    f"Rule '{key}' in 'maps' must be a string or dict, but {type(val).__name__}."
                )
        elif ruletype == RuleType.ranges:
            obj.interval = tuple()
            if isinstance(val, list):
                # {'pos1,(pos2:1.2)': ['con1', 'con2']} 型
                obj.matches = {str(i) for i in val}
                obj.positive = TokenSet.make(key_str)
                obj.negative = TokenSet.make()
            elif isinstance(val, dict):
                if isinstance(val.get(KeyName.positive), list):
                    # {'pos1,(pos2:1.2)': {'positive': ['con1', 'con2'], 'negative': 'neg1'}} 型
                    obj.matches = {str(i) for i in val.get(KeyName.positive, [])}
                    obj.positive = TokenSet.make(key_str)
                    obj.negative = TokenSet.make(val.get(KeyName.negative))
                elif isinstance(val.get(KeyName.negative), list):
                    # {'pos1,(pos2:1.2)': {'positive': 'pos1', 'negative': ['con1', 'con2'], }} 型
                    obj.matches = {str(i) for i in val.get(KeyName.negative, [])}
                    obj.positive = TokenSet.make(val.get(KeyName.positive))
                    obj.negative = TokenSet.make(key_str)
                else:
                    raise ValueError(
                        f"Rule '{key}' in 'ranges' must have 'positive' or 'negative' label."
                    )
            else:
                raise ValueError(
                    f"Rule '{key}' in 'ranges' must be a list or dict, but {type(val).__name__}."
                )
        elif ruletype == RuleType.intervals:

            def check_list(lst: list) -> tuple[float, float]:
                if len(lst) != 2:
                    raise ValueError(
                        f"'interval' list must be 2-length, this is {len(lst)}-length."
                    )
                try:
                    min = float(lst[0])
                    max = float(lst[1])
                except Exception as e:
                    raise TypeError(f"'{lst[0]}' or '{lst[1]}' is invalid value form.") from e
                if min > max:
                    raise ValueError(f"Invalid interval: min={lst[0]} > max={lst[1]}")
                return min, max

            obj.matches = set()
            if isinstance(val, list):
                # {'pos1,(pos2:1.2)': [min, max]} 型
                min, max = check_list(val)
                obj.positive = TokenSet.make(key_str)
                obj.negative = TokenSet.make()
            elif isinstance(val, dict):
                if isinstance(val.get(KeyName.positive), list):
                    # {'pos1,(pos2:1.2)': {'positive': [min, max], 'negative': 'neg1'}} 型
                    min, max = check_list(val.get(KeyName.positive))
                    obj.positive = TokenSet.make(key_str)
                    obj.negative = TokenSet.make(val.get(KeyName.negative))
                elif isinstance(val.get(KeyName.negative), list):
                    # {'pos1,(pos2:1.2)': {'positive': 'pos1', 'negative': [min, max], }} 型
                    min, max = check_list(val.get(KeyName.negative))
                    obj.positive = TokenSet.make(val.get(KeyName.positive))
                    obj.negative = TokenSet.make(key_str)
                else:
                    raise ValueError(
                        f"Rule '{key}' in 'intervals' must have 'positive' or 'negative' label."
                    )
            else:
                raise ValueError(
                    f"Rule '{key}' in 'intervals' must be a list or dict, but {type(val).__name__}."
                )
            obj.interval = (min, max)

        return obj

    def toprompt(
        self,
        priority: int,
        is_stable: bool,
        rule_path: RulePath,
        dynamic: SyringeNeedle.Dynamic,
        match: str = None,
    ) -> tuple[PromptBlueprint, PromptBlueprint, bool]:
        """
        マッチ文字列が条件を満たす場合にプロンプトを生成する

        Args:
            priority (int): 優先度
            is_stable (bool): 安定フラグ
            rule_path (RulePath): ルールパス
            dynamic (SyringeNeedle.Dynamic): 上層から共有される動的データ集
            match (str, optional): マッチした文字列

        Returns:
            tuple[PromptBlueprint, PromptBlueprint, bool | None]: プロンプトと空文字列の理由のタプル
            bool は空文字列を返す場合に, マッチしなかったことに因る場合に True
            フラグ条件不一致に因る場合に False
            それ以外(空文字列でない)の場合に None (使用しない)
        """
        if (self.matches and match not in self.matches) or (
            self.interval and (float(match) < self.interval[0] or float(match) > self.interval[1])
        ):
            # マッチせず
            # default つまり matches/interval が空の場合はここに入らない
            return PromptBlueprint(), PromptBlueprint(), True
        elif self.condition is not None and not self.condition.evaluate(dynamic.active_flags):
            # 条件がある上でフラグ条件に見合わない
            # default つまり matches/interval が空の場合はここに入らない
            return PromptBlueprint(), PromptBlueprint(), False

        # アクティブなフラグの更新は採用された場合のみ行う
        for fpm in self.flags_pm:
            for sign, flags in fpm.items():
                if sign == KeyName.add:
                    dynamic.active_flags |= flags
                if sign == KeyName.remove:
                    dynamic.active_flags -= flags

        positive = PromptBlueprint()
        negative = PromptBlueprint()

        for token in self.positive.tokens:
            positive.append(
                other=TokenBlueprint(
                    token=token,
                    priority=priority,
                    is_stable=is_stable,
                    rule_path=rule_path,
                    period=dynamic.period,
                    condition=self.condition,
                )
            )
        for token in self.negative.tokens:
            negative.append(
                other=TokenBlueprint(
                    token=token,
                    priority=priority,
                    is_stable=is_stable,
                    rule_path=rule_path,
                    period=dynamic.period,
                    condition=self.condition,
                )
            )
        return positive, negative, None


@dataclass
class Field:
    """
    正規表現パターンとルールの組み合わせを定義するクラス\n
    テキストからパターンマッチングでトークンを抽出し, ルールに従ってプロンプトを生成する

    例:
        {'pattern': '(xxx|yyy)', 'capturegrp': 1, 'priority': 2, 'lifetime': 'stable',\n
         'maps': {'xxx': {'positive': 'pos1,(pos2:1.2)', 'negative': 'neg1'},\n
         'yyy': 'pos3,(pos4:1.5)'},\n
         'default': {'positive': 'defpos1,(defpos2:1.7)', 'negative': 'defneg1'}}

    Attributes:
        pattern (str): 正規表現パターン
        capturegrp (int): キャプチャグループ番号(デフォルト: 0)
        priority (int): 優先度(デフォルト: lowest_priority)
        is_stable (bool): 安定フラグ(デフォルト: False)
        rules (list[Rule]): ルールのリスト
        default (Rule | None): デフォルトルール
        rule_path (RulePath): ルールパス
        re_cache (re.Pattern[str]): コンパイル済み正規表現
    """

    pattern: str = ""
    capturegrp: int = 0
    priority: int = Consts.lowest_priority
    is_stable: bool = False
    rules: list[Rule] = field(default_factory=list)
    default: Rule | None = None

    rule_path: RulePath = field(default_factory=RulePath)

    re_cache: re.Pattern[str] = field(default=None, init=False, repr=False, compare=False)

    @classmethod
    def make(
        cls,
        field: dict[str, dict],
        rule_path: RulePath,
        static: SyringeNeedle.Static,
        local_essentials: set[str],
    ):
        """
        YAML の定義から Field インスタンスを生成する

        Args:
            field (dict[str, dict]): フィールド定義の辞書
            rule_path (RulePath): ルールパス
            static (SyringeNeedle.Static): 上層から共有される静的データ集
            local_essential (set[str]): Screen 内で不可欠なルールの一覧

        Returns:
            Field: 生成されたFieldインスタンス

        Raises:
            ValueError: 定義形式が不正な場合, または正規表現が不正な場合
        """
        obj = cls()
        obj.rule_path = rule_path

        if KeyName.pattern in field:
            obj.pattern = field.get(KeyName.pattern)
        else:
            raise ValueError(f"Field definition missing mandatory 'pattern' key. Source: {field}")

        if KeyName.capturegrp in field:
            obj.capturegrp = int(field.get(KeyName.capturegrp))

        if KeyName.priority in field:
            priority = int(field.get(KeyName.priority))
            if rule_path.id not in static.priority_tbl or priority <= static.priority_tbl.get(
                rule_path.id
            ):
                static.priority_tbl[rule_path.id] = priority
            obj.priority = priority

        if KeyName.lifetime in field and field.get(KeyName.lifetime) == KeyName.stable:
            obj.is_stable = True
            # 上層で stable な同名ルールがあるものをすべて stable にする操作を行うための記録
            static.stable_rules.add(rule_path.id)

        if KeyName.essential in field:
            if field.get(KeyName.essential) == KeyName.local:
                local_essentials.add(rule_path.id)
            elif field.get(KeyName.essential) == KeyName.global_k:
                if obj.is_stable:
                    static.goal_global_essentials.add(rule_path.id)
                else:
                    # volatile なルールが global に essential な場合は local
                    local_essentials.add(rule_path.id)

        if KeyName.maps in field:
            for key, val in field.get(KeyName.maps).items():
                obj.rules.append(Rule.make(key=key, val=val, ruletype=RuleType.maps))
        elif KeyName.ranges in field:
            for key, val in field.get(KeyName.ranges).items():
                obj.rules.append(Rule.make(key=key, val=val, ruletype=RuleType.ranges))
        elif KeyName.intervals in field:
            for key, val in field.get(KeyName.intervals).items():
                obj.rules.append(Rule.make(key=key, val=val, ruletype=RuleType.intervals))
        else:
            raise ValueError(
                f"Field '{field.get(KeyName.pattern)}' must have either"
                " 'maps' or 'ranges' or 'intervals'."
            )

        if KeyName.default in field:
            val = field.get(KeyName.default)
            try:
                obj.default = Rule.make(KeyName.default, val, RuleType.default)
            except Exception as e:
                raise ValueError(f"Invalid default in field '{obj.pattern}'") from e

        try:
            if obj.re_cache is None:
                obj.re_cache = re.compile(obj.pattern, flags=re.MULTILINE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {obj.pattern}") from e

        return obj

    def toprompt(
        self, text: str, needle: SyringeNeedle, is_stable: int | None = None
    ) -> tuple[PromptBlueprint, PromptBlueprint]:
        """
        指定の text をポジティブプロンプト・ネガティブプロンプトのタプルにする\n
        マッチしない(キャプチャ逸脱を含む)場合はデフォルトを採用する

        Args:
            text (str): テキスト
            needle (SyringeNeedle): 上層から共有されるデータ集
            is_stable (bool | None, Optional): 外部から is_stable を指定する場合

        Returns:
            tuple[PromptBlueprint, PromptBlueprint]: タプル
        """
        positive = PromptBlueprint()
        negative = PromptBlueprint()

        # 同じルール ID の
        priority = (
            needle.static.priority_tbl.get(self.rule_path.id)
            if self.rule_path.id in needle.static.priority_tbl
            else self.priority
        )

        # 一度でも一致があり, かつそれがキャプチャ範囲適正か
        matched_once = False
        for match_itr in self.re_cache.finditer(text):
            try:
                match = match_itr.group(self.capturegrp)
            except Exception:
                # キャプチャグループ不正は無視
                print(
                    f"Capture group {self.capturegrp} not found in pattern '{self.pattern}'"
                    f" for text '{text}'"
                )
                continue

            matched_once = True
            for rule in self.rules:
                pos, neg, by_no_match = rule.toprompt(
                    match=match,
                    priority=priority,
                    is_stable=is_stable if is_stable is not None else self.is_stable,
                    rule_path=self.rule_path,
                    dynamic=needle.dynamic,
                )

                positive.append(pos)
                negative.append(neg)

        if matched_once and not positive.tokens and not negative.tokens:
            if self.default:
                # default
                pos, neg, _ = self.default.toprompt(
                    priority=priority,
                    is_stable=is_stable if is_stable is not None else self.is_stable,
                    rule_path=self.rule_path,
                    dynamic=needle.dynamic,
                )
                positive.append(pos)
                negative.append(neg)
            elif by_no_match:
                # どちらも空トークン(=マッチはしたが一致するルールがない)である場合を記録
                # これは今 period で継続中の stable トークンの削除に使用する
                # ただし default が設定されている場合, もしくは
                # フラグ条件不一致に因る場合は削除対象には追加しない
                needle.dynamic.empty_tokens_rule_ids.add(self.rule_path.id)

        if positive.tokens or negative.tokens:
            # マッチした場合にルールパスをスコープごとに記録
            needle.dynamic.achieved_essentials.add(self.rule_path.id)

        return positive, negative


@dataclass
class Screen:
    """
    複数のFieldと共通プロンプトをまとめた画面定義クラス\n
    ignitionパターンによる発火条件と, 複数のフィールドを持つ

    Attributes:
        ignition (Ignition): 発火条件
        fields (list[Field]): フィールドのリスト
        goal_local_essentials (set[str]): Screen 内で不可欠なルールの一覧
        common_positive (TokenSet): 共通ポジティブプロンプト
        common_negative (TokenSet): 共通ネガティブプロンプト
    """

    @dataclass
    class Ignition:
        """
        画面の発火条件を定義するクラス

        Attributes:
            patterns (list[re.Pattern]): 発火パターンのリスト
            is_all (bool): 全てのパターンにマッチする必要がある場合True,\n
                           いずれかにマッチすればよい場合False
        """

        patterns: list[re.Pattern] = field(default_factory=list)
        is_all: bool = False

    ignition: Ignition = field(default_factory=Ignition)
    fields: list[Field] = field(default_factory=list)
    goal_local_essentials: set[str] = field(default_factory=set)
    common_positive: TokenSet = field(default_factory=TokenSet)
    common_negative: TokenSet = field(default_factory=TokenSet)

    def collect_fields(self, node: dict, rule_path: RulePath, static: SyringeNeedle.Static) -> None:
        """
        YAML のノードを再帰的に探索し, Field 定義を収集する

        Args:
            node (dict): 探索対象のノード
            rule_path (RulePath): 現在のルールパス
            static (SyringeNeedle.Static): 上層から共有される静的データ集
        """
        if not isinstance(node, dict):
            # str や list は無視
            return

        if KeyName.pattern in node and (
            KeyName.maps in node or KeyName.ranges in node or KeyName.intervals in node
        ):
            # 'pattern' キー及び 'maps'/'ranges'/'intervals'が存在することを
            # 正しい Field の条件とする
            field = Field.make(node, rule_path, static, self.goal_local_essentials)
            self.fields.append(field)
            return

        for k, v in node.items():
            self.collect_fields(v, RulePath(rule_path + (k,)), static)

    @classmethod
    def make(
        cls, screen_name: str, screen: dict[str, dict[str, Any]], static: SyringeNeedle.Static
    ):
        """
        YAML の定義から Screen インスタンスを生成する

        Args:
            screen_name (str): 画面名
            screen (dict[str, dict[str, Any]]): 画面定義の辞書
            static (SyringeNeedle.Static): 上層から共有される静的データ集

        Returns:
            Screen: 生成されたScreenインスタンス

        Raises:
            ValueError: ignitionパターンの定義が不正な場合
        """
        obj = cls()

        for key, val in screen.items():
            if key == KeyName.ignition and isinstance(val, dict):
                type, patterns = next(iter(val.items()))
                if not isinstance(patterns, list):
                    raise ValueError("Ignition patterns must be list")

                obj.ignition = cls.Ignition(
                    patterns=[re.compile(str(p)) for p in patterns],
                    is_all=True if type == KeyName.all else False,
                )
            elif key == KeyName.POSITIVE and isinstance(val, str):
                obj.common_positive = TokenSet.make(val)
            elif key == KeyName.NEGATIVE and isinstance(val, str):
                obj.common_negative = TokenSet.make(val)
            else:
                rule_path: RulePath = RulePath((screen_name, key))
                obj.collect_fields(val, rule_path, static)

        return obj

    def sort(self) -> None:
        """
        フィールドの優先度を連番に振り直す\n
        lowest_priority を除く優先度順にソートし, 1から始まる連番を割り当てる\n
        lowest_priority は最後に配置される
        """
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
        """
        テキストが発火条件を満たすかチェックする

        Args:
            text (str): チェック対象のテキスト

        Returns:
            bool: 発火条件を満たす場合True, そうでない場合False
        """
        if not self.ignition.patterns:
            return False

        if self.ignition.is_all:
            return all(p.search(text) for p in self.ignition.patterns)
        else:
            return any(p.search(text) for p in self.ignition.patterns)

    def toprompt(
        self, text: str, needle: SyringeNeedle
    ) -> tuple[PromptBlueprint, PromptBlueprint, bool] | None:
        """
        テキストからプロンプトを生成する\n
        発火条件を満たさない場合は空のプロンプトを返す\n
        共通プロンプトは無条件で付与する

        Args:
            text (str): テキスト
            needle (SyringeNeedle): 上層から共有されるデータ集

        Returns:
            tuple[PromptBlueprint, PromptBlueprint, bool] | None: タプル
            essential 未達成時は None
            発火時は bool が True
        """
        if not self.check_ignition(text):
            return PromptBlueprint(), PromptBlueprint(), False

        positive = PromptBlueprint()
        negative = PromptBlueprint()
        optimized_goal_local_essentials = self.goal_local_essentials.copy()
        for fld in self.fields:
            is_stable = None
            # 同名のルール ID で stable なものが存在する場合に stable として実行
            if fld.rule_path.id in needle.static.stable_rules:
                is_stable = True

            # 同名のルール ID で global なものが存在する場合に local 指定をなくして実行
            if fld.rule_path.id in needle.static.goal_global_essentials:
                optimized_goal_local_essentials -= {fld.rule_path.id}

            pos, neg = fld.toprompt(text, needle=needle, is_stable=is_stable)
            positive.append(pos)
            negative.append(neg)

        # 共通プロンプトは常に最後尾
        for token in self.common_positive.tokens:
            positive.append(
                TokenBlueprint(
                    token=token,
                    priority=max(positive.tokens, key=lambda x: x.priority).priority + 1
                    if positive.tokens
                    else 1,
                    is_stable=False,
                    period=needle.dynamic.period,
                )
            )
        for token in self.common_negative.tokens:
            negative.append(
                TokenBlueprint(
                    token=token,
                    priority=max(negative.tokens, key=lambda x: x.priority).priority + 1
                    if negative.tokens
                    else 1,
                    is_stable=False,
                    period=needle.dynamic.period,
                )
            )

        # 各 Screen で達成すべきはローカルとグローバルの和集合
        goal_essentials = needle.static.goal_global_essentials | optimized_goal_local_essentials
        if not (goal_essentials <= needle.dynamic.achieved_essentials):
            # 実際に達成した不可欠ルールパスの集合に達成すべきものの集合が含まれない場合は空で返す
            return None
        return positive, negative, True


@dataclass
class Prompter:
    """
    複数の Screen を管理し, テキストからプロンプトを生成するメインクラス\n
    stable トークンを継続的に保持し, 世代管理を行う

    Attributes:
        screens (list[Screen]): 画面のリスト
        last_prompt (tuple[str, str]): 最後に生成したプロンプト(未発火時に返すため)
        continuing_positive (PromptBlueprint): 継続ポジティブプロンプト
        continuing_negative (PromptBlueprint): 継続ネガティブプロンプト
        needle (SyringeNeedle): 下層と共有するデータ集
    """

    yamlpath: Path = Path()
    screens: list[Screen] = field(default_factory=list)
    last_prompt: tuple[str, str] = ("", "")
    continuing_positive: PromptBlueprint = field(default_factory=PromptBlueprint)
    continuing_negative: PromptBlueprint = field(default_factory=PromptBlueprint)
    needle: SyringeNeedle = field(default_factory=SyringeNeedle)

    @classmethod
    def make(cls, yamlpath: Path):
        """
        YAML ファイルから Prompter インスタンスを生成する

        Args:
            yamlpath (Path): YAMLファイルのパス

        Returns:
            Prompter: 生成されたPrompterインスタンス
        """
        obj = cls()
        obj.yamlpath = Path(yamlpath)
        with open(yamlpath, "r", encoding="utf-8") as f:
            yamldict: dict = yaml.safe_load(f)
        for key, val in yamldict.items():
            obj.screens.append(Screen.make(key, val, obj.needle.static))
        obj.renumber_priorities()
        return obj

    def renumber_priorities(self) -> None:
        """全ての Screen のフィールド優先度を連番に振り直す"""
        for screen in self.screens:
            screen.sort()

    def toprompt(self, text: str) -> tuple[str, str]:
        """
        テキストからポジティブプロンプトとネガティブプロンプトを生成する\n
        stable トークンは継続プロンプトとして保持され, 次回以降も使用される

        Args:
            text (str): テキスト

        Returns:
            tuple[str, str]: (ポジティブプロンプト文字列, ネガティブプロンプト文字列) のタプル
        """
        positive = PromptBlueprint()
        negative = PromptBlueprint()
        self.needle.dynamic.achieved_essentials = set()
        self.needle.dynamic.empty_tokens_rule_ids = set()

        # 継続分を最初に記録(この時点でここに入っているものはアクティブなフラグに見合うものしかない)
        # 継続の際にそのトークンのルールパスを達成済みとしておく
        for token in self.continuing_positive.tokens:
            positive.append(token)
            self.needle.dynamic.achieved_essentials.add(token.rule_path.id)
        for token in self.continuing_negative.tokens:
            negative.append(token)
            self.needle.dynamic.achieved_essentials.add(token.rule_path.id)

        exists_not_achieved_screen = False
        has_ignited = False
        for screen in self.screens:
            result = screen.toprompt(text, self.needle)
            if result is None:
                # 不可欠ルール条件未達成の場合
                # 発火はしている
                has_ignited = True
                exists_not_achieved_screen = True
                continue

            pos, neg, res_has_ignited = result
            has_ignited |= res_has_ignited  # False で上書きしてはいけないので累積 OR
            positive.append(pos)
            negative.append(neg)

        if not has_ignited:
            # 全 Screen が未発火の場合は前回のプロンプトをそのまま返す
            return self.last_prompt

        # マッチしなかったルール ID と同じ継続中 stable トークンは削除
        for empty_rule_id in self.needle.dynamic.empty_tokens_rule_ids:
            for token in self.continuing_positive.tokens:
                if token.rule_path.id == empty_rule_id and token in positive.tokens:
                    positive.tokens.remove(token)

            for token in self.continuing_negative.tokens:
                if token.rule_path.id == empty_rule_id and token in negative.tokens:
                    negative.tokens.remove(token)

        self.continuing_positive = PromptBlueprint()
        self.continuing_negative = PromptBlueprint()
        if exists_not_achieved_screen:
            # 不可欠ルールを達成したスクリーンがなかった
            return "", ""

        # 継続分を記録(アクティブなフラグが条件に見合うもののみ), ただし同じルール元パスのものは更新
        # なお stable でも達成できなかった(= not achieved_screen)場合は継続しない
        for token in positive.tokens:
            if token.is_stable and token.evaluate(self.needle.dynamic.active_flags):
                self.continuing_positive.append(token)
        for token in negative.tokens:
            if token.is_stable and token.evaluate(self.needle.dynamic.active_flags):
                self.continuing_negative.append(token)

        self.needle.dynamic.period += 1
        self.last_prompt = (positive.to_promptstr(), negative.to_promptstr())

        return self.last_prompt

    def todict(self) -> dict:
        return asdict(self)
