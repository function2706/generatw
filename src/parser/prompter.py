from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, TypeAlias

import yaml


class KeyName(StrEnum):
    """YAML設定ファイルで使用されるキー名の定数"""

    parser = "parser"
    ignition = "ignition"
    pattern = "pattern"
    capturegrp = "capturegrp"
    maps = "maps"
    ranges = "ranges"
    intervals = "intervals"
    default = "default"
    common = "common"
    positive = "positive"
    negative = "negative"


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
    weight: float = 1.0

    @classmethod
    def make(cls, original_token: str):
        """
        文字列から Token インスタンスを生成する

        Args:
            original_token (str): 元のトークン文字列('word' または '(word:1.2)' 形式)

        Returns:
            Token: 生成された Token インスタンス

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

    def to_str(self) -> str:
        """
        プロンプト文字列に変換する

        Returns:
            str: プロンプト文字列('token' または '(token:weight)' 形式)
        """
        return f"({self.token}:{self.weight})" if self.weight != 1.0 else self.token


def make_tokens(text: str | None = None) -> list[Token]:
    """
    カンマ区切りの文字列から list[Token] インスタンスを生成する\n
    text が None の場合は空リストを返す

    Args:
        text (str|None): カンマ区切りのトークン文字列

    Returns:
        list[Token]: 生成された list[Token] インスタンス
    """
    if text is None:
        return []

    text_str = str(text)
    parts = [p.strip() for p in text_str.split(",") if p.strip()]
    return [Token.make(p) for p in parts]


CategoryPath: TypeAlias = tuple[str, ...]


@dataclass
class CategoryDeliverable:
    """
    Parser に共有する成果物の部品\n
    トークン本体に加えて, Screen 名や Category のパスを付帯する

    Attributes:
        path (CategoryPath): Category パス
        positive (list[Token]): ポジティブプロンプト
        negative (list[Token]): ネガティブプロンプト
    """

    path: CategoryPath = field(default_factory=tuple)
    positive: list[Token] = field(default_factory=list)
    negative: list[Token] = field(default_factory=list)


@dataclass
class ScreenDeliverable:
    """
    Parser に共有する成果物\n
    発火した Screen の Category に関するデータを付帯する
    """

    screen_id: str = ""
    categories: list[CategoryDeliverable] = field(default_factory=list)


@dataclass
class Rule(ABC):
    """
    マッチ条件とプロンプトの対応関係を定義するクラス

    Attributes:
        positive_tokens (list[Token]): ポジティブプロンプトのトークン集合
        negative_tokens (list[Token]): ネガティブプロンプトのトークン集合
    """

    positive_tokens: list[Token] = field(default_factory=list)
    negative_tokens: list[Token] = field(default_factory=list)

    @classmethod
    @abstractmethod
    def make(cls, key: str, val: str | dict | list):
        """
        YAML の定義から Rule インスタンスを生成する

        Args:
            key (str): ルールのキー
            val (str | dict | list): ルールの値

        Returns:
            Rule: 生成された Rule インスタンス

        Raises:
            ValueError: 定義形式が不正な場合
        """
        pass

    @abstractmethod
    def check_hit(self, match: str | None) -> bool:
        """
        ヒット可否を判定する

        Args:
            match (str): マッチした文字列

        Returns:
            bool: True: ヒット, False: ヒットせず
        """
        pass

    def to_tokenlists(self, match: str | None = None) -> tuple[list[Token], list[Token]] | None:
        """
        マッチ文字列が条件を満たす場合に list[Token] を生成する

        Args:
            match (str, optional): マッチした文字列

        Returns:
            tuple[list[Token], list[Token]] | None: ポジティブ/ネガティブプロンプト用
            ヒットしなかった場合に None
        """
        if not self.check_hit(match):
            return None

        return list(self.positive_tokens), list(self.negative_tokens)


@dataclass
class MapsRule(Rule):
    """
    maps 定義

    maps: {'xxx': {'positive': 'pos1,(pos2:1.2)', 'negative': 'neg1'}}\n
      -> Rule(matches={'xxx'}, positive=list[Token]([...]), negative=list[Token]([...]))

    Attributes:
        matches (set[str]): マッチ候補のセット
    """

    matches: set[str] = field(default_factory=set)

    @classmethod
    def make(cls, key: str, val: str | dict | list):
        obj = cls()

        obj.matches = {str(key)}
        if isinstance(val, str):
            # {'xxx': 'pos1,(pos2:1.2)'} 型
            obj.positive_tokens = make_tokens(val)
            obj.negative_tokens = make_tokens()
        elif isinstance(val, dict):
            obj.positive_tokens = make_tokens(val.get(KeyName.positive))
            obj.negative_tokens = make_tokens(val.get(KeyName.negative))
        else:
            raise ValueError(
                f"Rule '{key}' in 'maps' must be a string or dict, but {type(val).__name__}."
            )

        return obj

    def check_hit(self, match: str | None) -> bool:
        return match is not None and match in self.matches


@dataclass
class RangesRule(Rule):
    """
    ranges 定義

    例:
    ranges: {'pos1,(pos2:1.2)': ['con1', 'con2']}\n
      -> Rule(matches={'con1', 'con2'}, positive=list[Token]([...]), negative=list[Token]([]))

    Attributes:
        matches (set[str]): マッチ候補のセット
    """

    matches: set[str] = field(default_factory=set)

    @classmethod
    def make(cls, key: str, val: str | dict | list):
        obj = cls()

        key_str = str(key)
        if isinstance(val, list):
            # {'pos1,(pos2:1.2)': ['con1', 'con2']} 型
            obj.matches = {str(i) for i in val}
            obj.positive_tokens = make_tokens(key_str)
            obj.negative_tokens = make_tokens()
        elif isinstance(val, dict):
            if isinstance(val.get(KeyName.positive), list):
                # {'pos1,(pos2:1.2)': {'positive': ['con1', 'con2'], 'negative': 'neg1'}} 型
                obj.matches = {str(i) for i in val.get(KeyName.positive, [])}
                obj.positive_tokens = make_tokens(key_str)
                obj.negative_tokens = make_tokens(val.get(KeyName.negative))
            elif isinstance(val.get(KeyName.negative), list):
                # {'pos1,(pos2:1.2)': {'positive': 'pos1', 'negative': ['con1', 'con2'], }} 型
                obj.matches = {str(i) for i in val.get(KeyName.negative, [])}
                obj.positive_tokens = make_tokens(val.get(KeyName.positive))
                obj.negative_tokens = make_tokens(key_str)
            else:
                raise ValueError(
                    f"Rule '{key}' in 'ranges' must have 'positive' or 'negative' label."
                )
        else:
            raise ValueError(
                f"Rule '{key}' in 'ranges' must be a list or dict, but {type(val).__name__}."
            )

        return obj

    def check_hit(self, match: str | None) -> bool:
        return match is not None and match in self.matches


@dataclass
class IntervalsRule(Rule):
    """
    intervals 定義

    interval: {'pos1,(pos2:1.2)': [min, max]}\n
      -> Rule(interval=(min, max), positive=list[Token]([...]), negative=list[Token]([]))

    Attributes:
        interval (tuple[float, float]): マッチ候補の範囲(閉区間)
    """

    interval: tuple[float, float] = field(default_factory=tuple)

    @classmethod
    def make(cls, key: str, val: str | dict | list):
        def check_list(lst: list) -> tuple[float, float]:
            if len(lst) != 2:
                raise ValueError(f"'interval' list must be 2-length, this is {len(lst)}-length.")
            try:
                min = float(lst[0])
                max = float(lst[1])
            except Exception as e:
                raise TypeError(f"'{lst[0]}' or '{lst[1]}' is invalid value form.") from e
            if min > max:
                raise ValueError(f"Invalid interval: min={lst[0]} > max={lst[1]}")
            return min, max

        obj = cls()

        key_str = str(key)
        if isinstance(val, list):
            # {'pos1,(pos2:1.2)': [min, max]} 型
            min, max = check_list(val)
            obj.positive_tokens = make_tokens(key_str)
            obj.negative_tokens = make_tokens()
        elif isinstance(val, dict):
            if isinstance(val.get(KeyName.positive), list):
                # {'pos1,(pos2:1.2)': {'positive': [min, max], 'negative': 'neg1'}} 型
                min, max = check_list(val.get(KeyName.positive))
                obj.positive_tokens = make_tokens(key_str)
                obj.negative_tokens = make_tokens(val.get(KeyName.negative))
            elif isinstance(val.get(KeyName.negative), list):
                # {'pos1,(pos2:1.2)': {'positive': 'pos1', 'negative': [min, max], }} 型
                min, max = check_list(val.get(KeyName.negative))
                obj.positive_tokens = make_tokens(val.get(KeyName.positive))
                obj.negative_tokens = make_tokens(key_str)
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

    def check_hit(self, match: str | None) -> bool:
        try:
            match_float = float(match)
        except Exception:
            return False

        return match is not None and (self.interval[0] <= match_float <= self.interval[1])


@dataclass
class DefaultRule(Rule):
    """
    default 定義
    """

    @classmethod
    def make(cls, key: str, val: str | dict | list):
        obj = cls()

        if isinstance(val, str):
            obj.positive_tokens = make_tokens(val)
            obj.negative_tokens = make_tokens()
        elif isinstance(val, dict):
            obj.positive_tokens = make_tokens(val.get(KeyName.positive))
            obj.negative_tokens = make_tokens(val.get(KeyName.negative))
        else:
            raise ValueError("Syntax of 'default' is invalid.")

        return obj

    def check_hit(self, match: str | None) -> bool:
        return True


@dataclass
class Category:
    """
    正規表現パターンと Rule の組み合わせを定義するクラス\n
    テキストからパターンマッチングでトークンを抽出し, Rule に従って CategoryDeliverable を生成する

    例:
        {'pattern': '(xxx|yyy)', 'capturegrp': 1,\n
         'maps': {'xxx': {'positive': 'pos1,(pos2:1.2)', 'negative': 'neg1'},\n
                  'yyy': 'pos3,(pos4:1.5)'},\n
         'default': {'positive': 'defpos1,(defpos2:1.7)', 'negative': 'defneg1'}}

    Attributes:
        pattern (str): 正規表現パターン
        capturegrp (int): キャプチャグループ番号(デフォルト: 0)
        rules (list[Rule]): Rule のリスト
        default (Rule | None): デフォルト Rule
        category_path (CategoryPath): Category パス
        re_cache (re.Pattern[str]): コンパイル済み正規表現
    """

    pattern: re.Pattern[str] = field(default=None, init=False, repr=False, compare=False)
    capturegrp: int = 0
    category_path: CategoryPath = field(default_factory=tuple)
    rules: list[Rule] = field(default_factory=list)
    default: Rule | None = None

    @classmethod
    def make(cls, category: dict[str, dict], category_path: CategoryPath):
        """
        YAML の定義から Category インスタンスを生成する

        Args:
            field (dict[str, dict]): Category 定義の辞書
            category_path (CategoryPath): Category パス

        Returns:
            Category: 生成された Category インスタンス

        Raises:
            ValueError: 定義形式が不正な場合, または正規表現が不正な場合
        """
        obj = cls()

        obj.category_path = category_path

        if KeyName.pattern in category:
            try:
                obj.pattern = re.compile(category.get(KeyName.pattern), flags=re.MULTILINE)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {obj.pattern.pattern}") from e
        else:
            raise ValueError(
                f"Category definition missing mandatory 'pattern' key. Source: {category}"
            )

        if KeyName.capturegrp in category:
            obj.capturegrp = int(category.get(KeyName.capturegrp))

        if sum(k in category for k in (KeyName.maps, KeyName.ranges, KeyName.intervals)) != 1:
            raise ValueError("Category must have only 1 Ruletype, maps/ranges/intervals.")
        elif KeyName.maps in category:
            for key, val in category.get(KeyName.maps).items():
                obj.rules.append(MapsRule.make(key=key, val=val))
        elif KeyName.ranges in category:
            for key, val in category.get(KeyName.ranges).items():
                obj.rules.append(RangesRule.make(key=key, val=val))
        elif KeyName.intervals in category:
            for key, val in category.get(KeyName.intervals).items():
                obj.rules.append(IntervalsRule.make(key=key, val=val))

        if KeyName.default in category:
            val = category.get(KeyName.default)
            try:
                obj.default = DefaultRule.make(KeyName.default, val)
            except Exception as e:
                raise ValueError(f"Invalid default in field '{obj.pattern.pattern}'") from e

        return obj

    def to_category_deliverable(self, text: str) -> CategoryDeliverable | None:
        """
        指定の text から CategoryDeliverable を生成する\n
        マッチしたがヒットしない場合は default を採用する

        Args:
            text (str): テキスト

        Returns:
            CategoryDeliverable | None: ヒット時に CategoryDeliverable インスタンス
            マッチしない, あるいは default 適用を試みたが未定義の場合に None
        """
        result = CategoryDeliverable(path=self.category_path)

        has_matched = False
        for match_itr in self.pattern.finditer(text):
            try:
                match = match_itr.group(self.capturegrp)
            except Exception:
                # キャプチャグループ不正は無視
                continue

            has_matched = True
            for rule in self.rules:
                result_hit = rule.to_tokenlists(match=match)
                if result_hit is None:
                    continue

                pos, neg = result_hit
                result.positive.extend(pos)
                result.negative.extend(neg)

        if has_matched:
            if not result.positive and not result.negative:
                if self.default is not None:
                    # どの Rule でもトークンが追加されなかった -> default
                    pos, neg = self.default.to_tokenlists()
                    result.positive.extend(pos)
                    result.negative.extend(neg)
                else:
                    # default も未定義につき適用不可だった
                    return None
        else:
            # 一切マッチしなかった
            return None

        return result


@dataclass
class Screen:
    """
    複数の Category と共通プロンプトをまとめた画面定義クラス\n
    ignition パターンによる発火判定と, ScreenDeliverable の生成も行う

    Attributes:
        ignition (re.Pattern[str]): 発火条件
        categories (list[Category]): Category のリスト
        common_positive (list[Token]): 共通ポジティブプロンプト
        common_negative (list[Token]): 共通ネガティブプロンプト
    """

    screen_id: str = ""
    ignition: re.Pattern[str] = field(default=None, init=False, repr=False, compare=False)
    categories: list[Category] = field(default_factory=list)
    common_positive: list[Token] = field(default_factory=list)
    common_negative: list[Token] = field(default_factory=list)

    def collect_fields(self, node: dict, category_path: CategoryPath) -> None:
        """
        YAML のノードを再帰的に探索し, Category 定義を収集する

        Args:
            node (dict): 探索対象のノード
            category_path (CategoryPath): 現在の Category パス
        """
        if not isinstance(node, dict):
            # str や list は無視
            return

        if KeyName.pattern in node:
            # 最下層の Category = 'pattern' キーが存在する
            category = Category.make(node, category_path)
            self.categories.append(category)
            return

        for k, v in node.items():
            self.collect_fields(v, (category_path + (k,)))

    @classmethod
    def make(cls, screen_id: str, screen: dict[str, dict[str, Any]]):
        """
        YAML の定義から Screen インスタンスを生成する

        Args:
            screen_id (str): Screen 名
            screen (dict[str, dict[str, Any]]): Screen 定義の辞書

        Returns:
            Screen: 生成されたScreenインスタンス

        Raises:
            ValueError: ignitionパターンの定義が不正な場合
        """
        obj = cls()

        obj.screen_id = screen_id
        for key, val in screen.items():
            if key == KeyName.ignition:
                obj.ignition = re.compile(str(val))
            elif key == KeyName.common:
                if isinstance(val, str):
                    obj.common_positive = make_tokens(val)
                    obj.common_negative = make_tokens()
                elif isinstance(val, dict):
                    obj.common_positive = make_tokens(val.get(KeyName.positive))
                    obj.common_negative = make_tokens(val.get(KeyName.negative))
                else:
                    raise ValueError("Syntax of 'default' is invalid.")
            else:
                rule_path = CategoryPath((key,))
                obj.collect_fields(val, rule_path)

        return obj

    def to_screen_deliverable(self, text: str) -> ScreenDeliverable | None:
        """
        テキストから ScreenDeliverable を生成する

        Args:
            text (str): テキスト

        Returns:
            tuple[PromptBlueprint, PromptBlueprint, bool] | None: タプル, 未発火時は None
        """
        if self.ignition.search(text) is None:
            # 発火しなかった場合は None
            return None

        result = ScreenDeliverable(screen_id=self.screen_id)
        for category in self.categories:
            cat_deliverable = category.to_category_deliverable(text)
            if cat_deliverable is not None:
                result.categories.append(cat_deliverable)

        if self.common_positive or self.common_negative:
            common = CategoryDeliverable()
            common.positive.extend(self.common_positive)
            common.negative.extend(self.common_negative)
            result.categories.append(common)

        return result


PromptBase: TypeAlias = list[ScreenDeliverable]


@dataclass
class Prompter:
    """
    複数の Screen を管理し, テキストから PromptBase を生成するメインクラス

    Attributes:
        yamlpath (Path): YAML パス
        screens (list[Screen]): 画面のリスト
    """

    yamlpath: Path = Path()
    parser_keyword: str = ""
    screens: list[Screen] = field(default_factory=list)

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
            if key == KeyName.parser:
                obj.parser_keyword = val
            else:
                obj.screens.append(Screen.make(key, val))

        return obj

    def to_prompt_base(self, text: str) -> PromptBase:
        """
        テキストから PromptBase を生成する

        Args:
            text (str): テキスト

        Returns:
            tuple[str, str]: (ポジティブプロンプト文字列, ネガティブプロンプト文字列) のタプル
        """
        result: PromptBase = []

        for screen in self.screens:
            screen_deliverable = screen.to_screen_deliverable(text)
            if screen_deliverable is None:
                # 未発火
                continue

            result.append(screen_deliverable)

        return result

    def todict(self) -> dict:
        return asdict(self)
