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

    interpreter = "interpreter"
    ignition = "ignition"
    pattern = "pattern"
    capturegrp = "capturegrp"
    maps = "maps"
    ranges = "ranges"
    intervals = "intervals"
    import_k = "import"
    recurse = "recurse"
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
class PromptParts:
    """
    Cartegory パスごとにまとめられたトークン

    Attributes:
        path (CategoryPath): Category パス
        tokens (list[Token]): トークンのリスト
    """

    path: CategoryPath = field(default_factory=tuple)
    tokens: list[Token] = field(default_factory=list)


@dataclass
class Prompt:
    """
    Screen ごとにまとめられた PromptParts

    Attributes:
        screen_id (str): Screen ID
        positive (list[PromptParts]): ポジティブプロンプト
        negative (list[PromptParts]): ネガティブプロンプト
    """

    screen_id: str | None = None
    positive: list[PromptParts] = field(default_factory=list)
    negative: list[PromptParts] = field(default_factory=list)


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
class CategoryRegister:
    """
    import の際に CategoryPath から索いて Category を復元する際の元データ
    """

    pattern: re.Pattern[str] = field(default_factory=re.Pattern[str])
    capturegrp: int = 0
    rules: list[Rule] = field(default_factory=list)
    children: list[Category] = field(default_factory=list)


@dataclass
class Report:
    """
    マッチしたがヒットしなかったテキストの記録
    """

    matched: str = ""
    pattern: str = ""
    capturegrp: int = 0
    screen_id: str = ""
    path: CategoryPath = field(default_factory=CategoryPath)

    def __eq__(self, other: Report):
        return (
            self.matched == other.matched
            and self.pattern == other.pattern
            and self.capturegrp == other.capturegrp
            and self.screen_id == other.screen_id
        )


@dataclass
class Category:
    """
    正規表現パターンと Rule の組み合わせを定義するクラス\n
    テキストからパターンマッチングでトークンを抽出し, Rule に従って CategoryDeliverable を生成する\n
    sub_category が空でない場合は, 各マッチング結果をリストの各 Category に移譲する

    例:
        {'pattern': '(xxx|yyy)', 'capturegrp': 1,\n
         'maps': {'xxx': {'positive': 'pos1,(pos2:1.2)', 'negative': 'neg1'},\n
                  'yyy': 'pos3,(pos4:1.5)'},\n
         'default': {'positive': 'defpos1,(defpos2:1.7)', 'negative': 'defneg1'}}

    Attributes:
        pattern (re.Pattern[str]): コンパイル済み正規表現
        capturegrp (int): キャプチャグループ番号(デフォルト: 0)
        category_path (CategoryPath): Category パス
        rules (list[Rule]): Rule のリスト (children と排他)
        children (list[Category]): 再帰的に定義された Category のリスト (rules と排他)
        default (Rule | None): デフォルト Rule
    """

    pattern: re.Pattern[str] = field(default=None, init=False, repr=False, compare=False)
    capturegrp: int = 0
    category_path: CategoryPath = field(default_factory=tuple)
    rules: list[Rule] = field(default_factory=list)
    children: list[Category] = field(default_factory=list)
    default: Rule | None = None

    @classmethod
    def make(
        cls,
        category: dict[str, int | str | dict | list],
        screen_id: str,
        category_path: CategoryPath,
        catreg_dict: dict[CategoryPath, CategoryRegister],
    ):
        """
        YAML の定義から Category インスタンスを生成する

        Args:
            category (dict[str, dict]): Category 定義の辞書
            screen_id (str): Screen ID
            category_path (CategoryPath): Category パス
            catreg_dict (dict[CategoryPath, CategoryRegister]): CategoryPath ごとの CategoryRegister

        Returns:
            Category: 生成された Category インスタンス

        Raises:
            ValueError: 定義形式が不正な場合, または正規表現が不正な場合
        """
        obj = cls()

        obj.category_path = category_path

        def collect_categories(
            node: dict,
            category_path: CategoryPath,
            catreg_dict: dict[CategoryPath, CategoryRegister],
        ) -> None:
            """
            YAML のノードを再帰的に探索し, Category 定義を収集する
            """
            if not isinstance(node, dict):
                # str や list は無視
                return

            if KeyName.import_k in node or KeyName.pattern in node:
                # 最下層の Category = 'import' キーか 'pattern' キーが存在する
                category = Category.make(node, screen_id, category_path, catreg_dict)
                obj.children.append(category)
                return

            for k, v in node.items():
                collect_categories(v, (category_path + (k,)), catreg_dict)

        if KeyName.import_k in category:
            target_path = category.get(KeyName.import_k)
            if not isinstance(target_path, list):
                raise ValueError("Type of value for 'import' must be list.")
            elif tuple(target_path) not in catreg_dict:
                raise ValueError(f"CategoryPath '{target_path}' has not been defined in the YAML.")

            target_catreg = catreg_dict.get(tuple(target_path))
            if KeyName.pattern in category and KeyName.capturegrp in category:
                # pattern と capturegrp が定義されている場合はそちらを採用
                try:
                    obj.pattern = re.compile(category.get(KeyName.pattern), flags=re.MULTILINE)
                except re.error as e:
                    raise ValueError(f"Invalid regex pattern: {obj.pattern.pattern}") from e

                obj.capturegrp = int(category.get(KeyName.capturegrp))
            else:
                # そうでない場合は import 元のものを採用
                obj.pattern = target_catreg.pattern
                obj.capturegrp = target_catreg.capturegrp

            # rules と children は排他なので必ずどちらか一方
            if target_catreg.rules:
                obj.rules.extend(target_catreg.rules)
            elif target_catreg.children:
                obj.children.extend(target_catreg.children)
        else:
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

            if (
                sum(
                    k in category
                    for k in (KeyName.maps, KeyName.ranges, KeyName.intervals, KeyName.recurse)
                )
                != 1
            ):
                raise ValueError(
                    "Category must have only 1 Ruletype,"
                    "maps/ranges/intervals/recurse if without import."
                )
            elif KeyName.maps in category:
                for key, val in category.get(KeyName.maps).items():
                    obj.rules.append(MapsRule.make(key=key, val=val))
            elif KeyName.ranges in category:
                for key, val in category.get(KeyName.ranges).items():
                    obj.rules.append(RangesRule.make(key=key, val=val))
            elif KeyName.intervals in category:
                for key, val in category.get(KeyName.intervals).items():
                    obj.rules.append(IntervalsRule.make(key=key, val=val))
            elif KeyName.recurse in category:
                for key, val in category.get(KeyName.recurse).items():
                    collect_categories(
                        node=val,
                        category_path=obj.category_path + (key,),
                        catreg_dict=catreg_dict,
                    )

        catreg_dict[(screen_id,) + category_path] = CategoryRegister(
            pattern=obj.pattern, capturegrp=obj.capturegrp, rules=obj.rules, children=obj.children
        )

        if KeyName.default in category:
            val = category.get(KeyName.default)
            try:
                obj.default = DefaultRule.make(KeyName.default, val)
            except Exception as e:
                raise ValueError(f"Invalid default in field '{obj.pattern.pattern}'") from e

        return obj

    def has_children(self) -> bool:
        """
        再帰的に Category を有するか
        """
        return self.children and not self.rules

    def to_prompts(
        self, text: str, screen_id: str
    ) -> tuple[list[tuple[PromptParts, PromptParts]] | None, list[Report]]:
        """
        指定の text から PromptParts を生成する

        - 再帰的 Category を有する場合\n
        順に Rule を適用していく\n
        マッチしたがヒットしない場合は default を採用する

        - 再帰的 Category を有する場合\n
        順に Category.to_prompts() を処理していく

        Args:
            text (str): テキスト
            screen_id (str): Screen ID

        Returns:
            tuple[list[tuple[PromptParts, PromptParts]] | None, list[Report]]:
            ヒット時に PromptParts のタプル(ポジティブ/ネガティブ)のリスト\n
            マッチしない, あるいはマッチしたがヒットせず default 適用を試みるも未定義の場合に None\n
            PromptParts の片方が空の tokens である場合があることに注意\n
            Report はヒットしなかった場合を記録 (default が適用された場合も含める)
        """
        results: dict[CategoryPath, tuple[PromptParts, PromptParts]] = {}
        reports: list[Report] = []

        def get_or_create(path: CategoryPath) -> tuple[PromptParts, PromptParts]:
            if path not in results:
                results[path] = (PromptParts(path=path), PromptParts(path=path))
            return results[path]

        has_matched = False
        for match_itr in self.pattern.finditer(text):
            try:
                match = match_itr.group(self.capturegrp)
            except Exception:
                # キャプチャグループ不正は無視
                continue

            has_matched = True
            if self.has_children():
                for child_category in self.children:
                    child_results, child_reports = child_category.to_prompts(match, screen_id)
                    reports.extend(child_reports)

                    if child_results is None:
                        continue

                    for pos_parts, neg_parts in child_results:
                        pos, neg = get_or_create(pos_parts.path)
                        pos.tokens.extend(pos_parts.tokens)
                        neg.tokens.extend(neg_parts.tokens)
            else:
                hit = False
                for rule in self.rules:
                    result_hit = rule.to_tokenlists(match=match)
                    if result_hit is None:
                        continue

                    hit = True
                    pos, neg = result_hit
                    dst_pos, dst_neg = get_or_create(self.category_path)
                    dst_pos.tokens.extend(pos)
                    dst_neg.tokens.extend(neg)

                if not hit:
                    report = Report(
                        matched=match,
                        pattern=self.pattern.pattern,
                        capturegrp=self.capturegrp,
                        screen_id=screen_id,
                        path=self.category_path,
                    )
                    if report not in reports:
                        reports.append(report)

        if has_matched:
            if not results:
                if self.default is not None:
                    # 未ヒット = どの Rule でもポジティブ/ネガティブともにトークンが追加されなかった
                    #   -> default
                    pos, neg = self.default.to_tokenlists()
                    dst_pos, dst_neg = get_or_create(self.category_path)
                    dst_pos.tokens.extend(pos)
                    dst_neg.tokens.extend(neg)
                else:
                    # default も未定義につき適用不可だった
                    return None, reports
        else:
            # 一切マッチしなかった
            return None, reports

        return list(results.values()), reports


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

    def collect_categories(
        self,
        node: dict,
        category_path: CategoryPath,
        catreg_dict: dict[CategoryPath, CategoryRegister],
    ) -> None:
        """
        YAML のノードを再帰的に探索し, Category 定義を収集する

        Args:
            node (dict): 探索対象のノード
            category_path (CategoryPath): 現在の Category パス
            catreg_dict (dict[CategoryPath, CategoryRegister]): CategoryPath ごとの CategoryRegister
        """
        if not isinstance(node, dict):
            # str や list は無視
            return

        if KeyName.import_k in node or KeyName.pattern in node:
            # 最下層の Category = 'import' キーか 'pattern' キーが存在する
            category = Category.make(node, self.screen_id, category_path, catreg_dict)
            self.categories.append(category)
            return

        for k, v in node.items():
            self.collect_categories(v, (category_path + (k,)), catreg_dict)

    @classmethod
    def make(
        cls,
        screen_id: str,
        screen: dict[str, dict[str, Any] | list[str]],
        common_dict: dict[str, tuple[list[Token], list[Token]]],
        catreg_dict: dict[CategoryPath, CategoryRegister],
    ):
        """
        YAML の定義から Screen インスタンスを生成する

        Args:
            screen_id (str): Screen 名
            screen (dict[str, dict[str, Any]]): Screen 定義の辞書
            common_dict (dict[str, tuple[list[Token], list[Token]]]): Screen ごとの common 領域
            catreg_dict (dict[CategoryPath, CategoryRegister]): CategoryPath ごとの CategoryRegister

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
                elif isinstance(val, list):
                    # import
                    src_screen_id = val[0]
                    for sid, commons in common_dict.items():
                        if sid != src_screen_id:
                            continue
                        obj.common_positive = commons[0]
                        obj.common_negative = commons[1]
                        break
                    else:
                        raise ValueError(
                            f"No such Screen ID ('{src_screen_id}') for importing commons."
                        )
                else:
                    raise ValueError("Syntax of 'common' is invalid.")
                common_dict[screen_id] = (obj.common_positive, obj.common_negative)
            else:
                obj.collect_categories(
                    node=val,
                    category_path=CategoryPath((key,)),
                    catreg_dict=catreg_dict,
                )

        return obj

    def to_prompts(self, text: str) -> tuple[Prompt | None, list[Report]]:
        """
        テキストから Prompt を生成する\n
        PromptParts の tokens が空の場合は追加しない

        Args:
            text (str): テキスト

        Returns:
            tuple[Prompt | None, list[Report]]: Prompt, 未発火時は None\n
            Report はヒットしなかった場合を記録 (default が適用された場合も含める)
        """
        if self.ignition.search(text) is None:
            # 発火しなかった場合は None
            return None, []

        prompt = Prompt(screen_id=self.screen_id)
        reports: list[Report] = []
        for category in self.categories:
            results, rprts = category.to_prompts(text, self.screen_id)
            reports.extend(rprts)
            if results is None:
                # tokens が空の場合は追加しない
                continue

            for pos_parts, neg_parts in results:
                if pos_parts.tokens:
                    prompt.positive.append(pos_parts)
                if neg_parts.tokens:
                    prompt.negative.append(neg_parts)

        if self.common_positive:
            prompt.positive.append(PromptParts(tokens=self.common_positive))
        if self.common_negative:
            prompt.negative.append(PromptParts(tokens=self.common_negative))

        return prompt, reports


@dataclass
class Prompter:
    """
    複数の Screen を管理し, テキストから PromptBase を生成するメインクラス

    Attributes:
        yamlpath (Path): YAML パス
        screens (list[Screen]): 画面のリスト
    """

    yamlpath: Path = Path()
    interpreter_keyword: str = ""
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

        catreg_dict: dict[CategoryPath, CategoryRegister] = {}
        common_dict: dict[str, tuple[list[Token], list[Token]]] = {}
        for key, val in yamldict.items():
            if key == KeyName.interpreter:
                obj.interpreter_keyword = val
            else:
                obj.screens.append(Screen.make(key, val, common_dict, catreg_dict))

        return obj

    def to_prompt(self, text: str) -> tuple[Prompt, list[Report]]:
        """
        テキストから Prompt を生成する\n
        Prompt が空の list の場合は追加しない\n
        発火した Screen がなかった場合も空の Prompt を返す (Screen ID = None)

        Args:
            text (str): テキスト

        Returns:
            tuple[Prompt, list[Report]]: Prompt\n
            Report はヒットしなかった場合を記録 (default が適用された場合も含める)
        """
        prompt: Prompt = None
        reports: list[Report] = []
        for screen in self.screens:
            prompt, rprts = screen.to_prompts(text)
            reports.extend(rprts)
            if prompt is not None:
                # 初めて発火した Screen のみを付帯
                break

        return prompt if prompt is not None else Prompt(), reports

    def todict(self) -> dict:
        return asdict(self)
