import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, TypeAlias

import pyperclip
import yaml


class KeyName(StrEnum):
    """YAML設定ファイルで使用されるキー名の定数"""

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
    """YAML設定ファイルで使用される値の定数"""

    stable = "stable"
    volatile = "volatile"
    any = "any"
    all = "all"


@dataclass(frozen=True)
class Consts:
    """システム全体で使用される定数"""

    lowest_priority = -1


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


SourcePath: TypeAlias = list[str]


@dataclass
class TokenBlueprint:
    """
    プロンプト化のためのトークンデータ\n
    トークン本体に加えて, 優先度や安定性などのメタデータを保持する

    Attributes:
        token (Token): トークン本体
        priority (int): 優先度(小さいほど高優先)
        is_stable (bool): 安定フラグ(True の場合は次回以降も継続)
        source_path (SourcePath): ソースパス(YAML内の階層)
        period (int): 生成された世代番号
    """

    token: Token = field(default_factory=Token)
    priority: int = 0
    is_stable: bool = False
    source_path: SourcePath = field(default_factory=SourcePath)
    period: int = 0

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
        tokens に要素を追加し, 共通する SourcePath のものは削除する\n
        より新しい period を持つトークンで既存のトークンを上書きする

        Args:
            other (TokenBlueprint | PromptBlueprint): 追加する要素

        Raises:
            TypeError: 引数の型が不正な場合
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

    Attributes:
        matches (set[str]): マッチ対象文字列の集合
        positive (TokenSet): ポジティブプロンプトのトークン集合
        negative (TokenSet): ネガティブプロンプトのトークン集合
    """

    matches: set[str] = field(default_factory=set)
    positive: TokenSet = field(default_factory=TokenSet)
    negative: TokenSet = field(default_factory=TokenSet)

    @classmethod
    def make(cls, key: str, val: str | dict | list, is_maps: bool = True):
        """
        YAML の定義から Rule インスタンスを生成する

        Args:
            key (str): ルールのキー
            val (str | dict | list): ルールの値
            is_maps (bool): maps形式の場合True, ranges形式の場合False

        Returns:
            Rule: 生成されたRuleインスタンス

        Raises:
            ValueError: 定義形式が不正な場合
        """
        key_str = str(key)
        if key_str == KeyName.default:
            matches = set()
            if isinstance(val, str):
                positive = TokenSet.make(val)
                negative = TokenSet.make()
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
                negative = TokenSet.make()
            elif isinstance(val, dict):
                positive = TokenSet.make(val.get(KeyName.positive))
                negative = TokenSet.make(val.get(KeyName.negative))
            else:
                raise ValueError(
                    f"Rule '{key}' in 'maps' must be a string or dict, but {type(val).__name__}."
                )
        else:
            positive = TokenSet.make(key_str)
            if isinstance(val, list):
                # {'pos1,(pos2:1.2)': ['con1', 'con2']} 型
                matches = {str(i) for i in val}
                negative = TokenSet.make()
            elif isinstance(val, dict):
                # {'pos1,(pos2:1.2)': {'conditions': ['con1', 'con2'], 'negative': 'neg1'}} 型
                matches = {str(i) for i in val.get(KeyName.conditions, [])}
                negative = TokenSet.make(val.get(KeyName.negative))
            else:
                raise ValueError(
                    f"Rule '{key}' in 'ranges' must be a list or dict, but {type(val).__name__}."
                )

        return cls(matches=matches, positive=positive, negative=negative)

    def toprompt(
        self,
        priority: int,
        is_stable: bool,
        source_path: SourcePath,
        period: int,
        match: str = None,
    ) -> tuple[PromptBlueprint, PromptBlueprint]:
        """
        マッチ文字列が条件を満たす場合にプロンプトを生成する

        Args:
            priority (int): 優先度
            is_stable (bool): 安定フラグ
            source_path (SourcePath): ソースパス
            period (int): 世代番号
            match (str, optional): マッチした文字列

        Returns:
            tuple[PromptBlueprint, PromptBlueprint]: タプル
        """
        if self.matches and match not in self.matches:
            # default = matches が空の場合はここに入らない
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
                )
            )
        for token in self.negative.tokens:
            negative.append(
                TokenBlueprint(
                    token=token,
                    priority=priority,
                    is_stable=is_stable,
                    source_path=source_path,
                    period=period,
                )
            )
        return positive, negative


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
        source_path (SourcePath): ソースパス
        re_cache (re.Pattern[str]): コンパイル済み正規表現
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
        """
        YAML の定義から Field インスタンスを生成する

        Args:
            field (dict[str, dict]): フィールド定義の辞書

        Returns:
            Field: 生成されたFieldインスタンス

        Raises:
            ValueError: 定義形式が不正な場合, または正規表現が不正な場合
        """
        obj = cls()

        if KeyName.pattern in field:
            obj.pattern = field.get(KeyName.pattern)
        else:
            raise ValueError(f"Field definition missing mandatory 'pattern' key. Source: {field}")

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
            raise ValueError(
                f"Field '{field.get(KeyName.pattern)}' must have either 'maps' or 'ranges'."
            )

        if KeyName.default in field:
            val = field.get(KeyName.default)
            try:
                obj.default = Rule.make(KeyName.default, val)
            except Exception as e:
                raise ValueError(f"Invalid default in field '{obj.pattern}'") from e

        try:
            if obj.re_cache is None:
                obj.re_cache = re.compile(obj.pattern, flags=re.MULTILINE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {obj.pattern}") from e

        return obj

    def toprompt(self, text: str, period: int) -> tuple[PromptBlueprint, PromptBlueprint]:
        """
        指定の text をポジティブプロンプト・ネガティブプロンプトのタプルにする\n
        マッチしない(キャプチャ逸脱を含む)場合はデフォルトを採用する

        Args:
            text (str): テキスト
            period (int): プロンプト化の世代

        Returns:
            tuple[PromptBlueprint, PromptBlueprint]: タプル
        """
        positive = PromptBlueprint()
        negative = PromptBlueprint()

        matched_once = False
        for match_itr in self.re_cache.finditer(text):
            matched_once = True
            try:
                match = match_itr.group(self.capturegrp)
            except Exception:
                # キャプチャグループ不正は無視
                print(
                    f"Capture group {self.capturegrp} not found in pattern '{self.pattern}'"
                    f" for text '{text}'"
                )
                continue

            for rule in self.rules:
                pos, neg = rule.toprompt(
                    match=match,
                    priority=self.priority,
                    is_stable=self.is_stable,
                    source_path=self.source_path,
                    period=period,
                )
                positive.append(pos)
                negative.append(neg)

        if matched_once and self.default and not positive.tokens and not negative.tokens:
            # default
            pos, neg = self.default.toprompt(
                priority=self.priority,
                is_stable=self.is_stable,
                source_path=self.source_path,
                period=period,
            )
            positive.append(pos)
            negative.append(neg)

        return positive, negative


@dataclass
class Screen:
    """
    複数のFieldと共通プロンプトをまとめた画面定義クラス\n
    ignitionパターンによる発火条件と, 複数のフィールドを持つ

    Attributes:
        ignition (Ignition): 発火条件
        fields (list[Field]): フィールドのリスト
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
    common_positive: TokenSet = field(default_factory=TokenSet)
    common_negative: TokenSet = field(default_factory=TokenSet)

    def collect_fields(self, node: dict, source_path: SourcePath) -> None:
        """
        YAML のノードを再帰的に探索し, Field 定義を収集する

        Args:
            node (dict): 探索対象のノード
            source_path (SourcePath): 現在のソースパス
        """
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
        """
        YAML の定義から Screen インスタンスを生成する

        Args:
            screen_name (str): 画面名
            screen (dict[str, dict[str, Any]]): 画面定義の辞書

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

    def toprompt(self, text: str, period: int) -> tuple[PromptBlueprint, PromptBlueprint]:
        """
        テキストからプロンプトを生成する\n
        発火条件を満たさない場合は空のプロンプトを返す

        Args:
            text (str): テキスト
            period (int): プロンプト化の世代

        Returns:
            tuple[PromptBlueprint, PromptBlueprint]: タプル
        """
        if not self.check_ignition(text):
            return PromptBlueprint(), PromptBlueprint()

        positive = PromptBlueprint()
        negative = PromptBlueprint()
        for fld in self.fields:
            pos, neg = fld.toprompt(text, period=period)
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
                    period=period,
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
                    period=period,
                )
            )

        return positive, negative


@dataclass
class Prompter:
    """
    複数の Screen を管理し, テキストからプロンプトを生成するメインクラス\n
    stable トークンを継続的に保持し, 世代管理を行う

    Attributes:
        screens (list[Screen]): 画面のリスト
        continuing_positive (PromptBlueprint): 継続ポジティブプロンプト
        continuing_negative (PromptBlueprint): 継続ネガティブプロンプト
        period (int): 現在の世代番号
    """

    screens: list[Screen] = field(default_factory=list)
    continuing_positive: PromptBlueprint = field(default_factory=PromptBlueprint)
    continuing_negative: PromptBlueprint = field(default_factory=PromptBlueprint)
    period: int = 0

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
        with open(yamlpath, "r", encoding="utf-8") as f:
            yaml_dict: dict = yaml.safe_load(f)
        for key, val in yaml_dict.items():
            obj.screens.append(Screen.make(key, val))
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

        # 継続分を最初に記録
        positive.append(self.continuing_positive)
        negative.append(self.continuing_negative)

        for screen in self.screens:
            pos, neg = screen.toprompt(text, self.period)
            positive.append(pos)
            negative.append(neg)

        # 継続分を記録, ただし同じルール元パスのものは更新
        for token in positive.tokens:
            if token.is_stable:
                self.continuing_positive.append(token)
        for token in negative.tokens:
            if token.is_stable:
                self.continuing_negative.append(token)

        self.period += 1

        return positive.to_promptstr(), negative.to_promptstr()


prompter = Prompter.make("src/debug/parse_test/yamls/testcase1.yaml")
pos, neg = prompter.toprompt("today Name2")
print("POS1:", pos)
print("NEG1:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase2.yaml")
pos, neg = prompter.toprompt("go id:10")
print("POS2:", pos)
print("NEG2:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase3.yaml")
pos, neg = prompter.toprompt("go v:B")
print("POS3:", pos)
print("NEG3:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase3.yaml")
pos, neg = prompter.toprompt("go nothing")
print("POS4:", pos)
print("NEG4:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase4.yaml")
pos, neg = prompter.toprompt("go x")
print("POS5:", pos)
print("NEG5:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase5.yaml")
pos, neg = prompter.toprompt("go v:A")
print("POS6-1:", pos)
print("NEG6-1:", neg)
pos, neg = prompter.toprompt("go v:B")
print("POS6-2:", pos)
print("NEG6-2:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase5.yaml")
pos, neg = prompter.toprompt("hello v:A")
print("POS7:", pos)
print("NEG7:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase6.yaml")
pos, neg = prompter.toprompt("go 8")
print("POS8:", pos)
print("NEG8:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase7.yaml")
pos, neg = prompter.toprompt("go x")
print("POS9:", pos)
print("NEG9:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase8.yaml")
pos, neg = prompter.toprompt("go x")
print("POS10:", pos)
print("NEG10:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase9.yaml")
pos, neg = prompter.toprompt("go v:A")
print("POS11-1:", pos)
print("NEG11-1:", neg)
pos, neg = prompter.toprompt("go v:B")
print("POS11-2:", pos)
print("NEG11-2:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase10.yaml")
pos, neg = prompter.toprompt("go v:A")
print("POS12-1:", pos)
print("NEG12-1:", neg)
pos, neg = prompter.toprompt("go v:B")
print("POS12-2:", pos)
print("NEG12-2:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase11.yaml")
pos, neg = prompter.toprompt("go v:A")
print("POS13-1:", pos)
print("NEG13-1:", neg)
pos, neg = prompter.toprompt("go v:B")
print("POS13-2:", pos)
print("NEG13-2:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase12.yaml")
pos, neg = prompter.toprompt("go v:A")
print("POS14-1:", pos)
print("NEG14-1:", neg)
pos, neg = prompter.toprompt("go nothing")
print("POS14-2:", pos)
print("NEG14-2:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase13.yaml")
pos, neg = prompter.toprompt("go v:A")
print("POS15-1:", pos)
print("NEG15-1:", neg)
pos, neg = prompter.toprompt("go v:B")
print("POS15-2:", pos)
print("NEG15-2:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase14.yaml")
pos, neg = prompter.toprompt("go")
print("POS16:", pos)
print("NEG16:", neg)
prompter = Prompter.make("src/debug/parse_test/yamls/testcase15.yaml")
pos, neg = prompter.toprompt("go a:on b:on")
print("POS17-1:", pos)
print("NEG17-1:", neg)
pos, neg = prompter.toprompt("go a:off")
print("POS17-2:", pos)
print("NEG17-2:", neg)

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
prompter = Prompter.make("src/debug/parse_test/yamls/test.yaml")
pos, neg = prompter.toprompt("today: 2026/02/05, Name2 (vibe: Vibe1)")
print("POS:", pos)
print("NEG:", neg)
pos, neg = prompter.toprompt("sub: WOW!! mood: Mood2 , equip: Slacks foobar")
print("POS:", pos)
print("NEG:", neg)
pos, neg = prompter.toprompt("today: foobarBarFugahogeHogeBazbaz")
print("POS:", pos)
print("NEG:", neg)
pos, neg = prompter.toprompt("sub: WOW!! mood: Mood1 , equip: Blouse ")
print("POS:", pos)
print("NEG:", neg)
pos, neg = prompter.toprompt("today: 2026/07/21, Name1 (vibe: ) foobarBarFugahogeHogeBazbaz")
print("POS:", pos)
print("NEG:", neg)

prompter = Prompter.make("yamls/the_world.yaml")
new_clipboard = pyperclip.paste()
pos, neg = prompter.toprompt(new_clipboard)
print("POS:", pos)
print("NEG:", neg)
