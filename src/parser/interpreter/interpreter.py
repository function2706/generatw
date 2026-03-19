"""
Prompt 解釈クラス
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from common.expr import Expr, TrueExpr
from parser.prompter import CategoryPath, Prompt, Prompter, PromptParts, Report, Token


@dataclass
class MemoryEntry:
    """
    ポジティブ・ネガティブを CategoryPath でまとめて記憶するためのデータ定義
    """

    path: CategoryPath = field(default_factory=CategoryPath, compare=False)
    pos_tokens: list[Token] = field(default_factory=list)
    neg_tokens: list[Token] = field(default_factory=list)


@dataclass
class Memory:
    """
    ポジティブプロンプトとネガティブプロンプトを CategoryPath ごとに束ねたデータ
    """

    entries: list[MemoryEntry] = field(default_factory=list)

    def to_prompt(self, screen_id: str) -> Prompt:
        prompt_set = Prompt(screen_id=screen_id)
        for entry in self.entries:
            if entry.pos_tokens:
                prompt_set.positive.append(PromptParts(path=entry.path, tokens=entry.pos_tokens))
            if entry.neg_tokens:
                prompt_set.negative.append(PromptParts(path=entry.path, tokens=entry.neg_tokens))

        return prompt_set


def prompt_to_memory(prompt: Prompt | None) -> Memory | None:
    """
    指定の Prompt から Memory を得る\n
    None についてはそのまま None を返す
    Args:
        prompt (Prompt | None): Prompt
    Returns:
        Memory | None: Memory
    """
    if prompt is None:
        return None

    memory = Memory()
    for parts in prompt.positive:
        memory.entries.append(MemoryEntry(path=parts.path, pos_tokens=parts.tokens))
    for parts in prompt.negative:
        exists = False
        for entry in memory.entries:
            if parts.path != entry.path:
                continue
            # dedupe されている場合は代入と変わらない
            entry.neg_tokens.extend(parts.tokens)
            exists = True
        if not exists:
            # ポジティブ側になかった場合は単独で登録
            memory.entries.append(MemoryEntry(parts.path, neg_tokens=parts.tokens))
    return memory


@dataclass(frozen=True)
class CategoryConfig:
    sift_condition: Expr | None  # ふるいがけ条件 (None = 恒真)
    log_report: bool  # Report を残すか


type PrimitiveCategoryConfig = tuple[CategoryPath, Expr | None, bool]


@dataclass(frozen=True)
class ScreenConfig:
    cat_configs: dict[CategoryPath, CategoryConfig]  # カテゴリーコンフィグ
    sufficiency: Expr | None  # 充足条件 (None = 恒真)
    syncer: Callable[[Memory], Memory] | None  # 同期処理定義

    @classmethod
    def set(
        cls,
        primitive_category_configs: list[PrimitiveCategoryConfig],
        sufficiency: Expr | None,
        syncer: Callable[[Memory], Memory] | None,
    ):
        return cls(
            cat_configs={
                path: CategoryConfig(sift_condition=sift_cond, log_report=log_report)
                for path, sift_cond, log_report in primitive_category_configs
            },
            sufficiency=sufficiency,
            syncer=syncer,
        )

    def sift_condition_of(self, category_path: CategoryPath) -> Expr | None:
        """
        指定の category_path とペアの sift_condition を取得する\n
        category_path にあたるものが存在しない場合は None を返す\n
        sift_condition に None が指定されている場合は恒真とする

        Args:
            category_path (CategoryPath): CategoryPath

        Returns:
            Expr | None: sift_condition
        """
        cat_config = self.cat_configs.get(category_path)
        if cat_config is None:
            return None

        return cat_config.sift_condition if cat_config.sift_condition is not None else TrueExpr()

    def should_leave_report_of(self, category_paths: set[CategoryPath]) -> bool:
        """
        指定の category_paths をもつ Report を残すべきか\n
        条件が定義されている CategoryPath を1つでも持つ場合はその条件を返す\n
        そうでない場合は False

        Args:
            category_path (CategoryPath): CategoryPath

        Returns:
            bool: True: 残すべき
        """
        for cat_path, cat_config in self.cat_configs.items():
            if cat_path in category_paths:
                return cat_config.log_report
        return False


type ScreenTable = dict[
    str,  # Screen ID
    ScreenConfig,
]


class Interpreter(ABC):
    """
    クリップボード監視, ステータス記録クラス
    """

    def __init__(self, yamlpath: Path):
        """
        コンストラクタ

        ScreenTable: Screen ID の順序はプロンプト化における優先順位を表す

        Args:
            yamlpath (Path): YAML パス
        """
        self.prompter: Prompter = None
        self.yamlpath = yamlpath
        self.screen_table: ScreenTable = {}

        self.switch_prompter(yamlpath)

    @classmethod
    def keyword(cls) -> str:
        """
        キーワード (YAML の "interpreter" キーの値との照合値)を取得する

        Returns:
            str: キーワード_
        """
        return cls.__name__

    def switch_prompter(self, yamlpath: Path) -> None:
        """
        指定の YAML を Prompter として設定する\n
        "interpreter" キーワードと一致しない場合は何もしない(そのまま)

        Args:
            yamlpath (Path): YAML パス
        """
        yamlpath = Path(yamlpath)
        if yamlpath.exists():
            with open(yamlpath, encoding="utf-8") as f:
                yamldict: dict = yaml.safe_load(f)
                keyword = yamldict.get("interpreter")
            if keyword == self.keyword():
                self.prompter = Prompter.make(yamlpath)
                self.yamlpath = yamlpath

    def reload_prompter(self) -> None:
        """
        設定している YAML によって Prompter を開き直す
        """
        self.switch_prompter(self.yamlpath)

    @abstractmethod
    def save_state(self) -> dict:
        """
        このインスタンスの状態を保存可能な形式で返す\n
        記憶がない場合は空の dict を返す

        Returns:
            dict: 状態を表す辞書
        """
        pass

    @abstractmethod
    def restore_state(self, state: dict) -> None:
        """
        指定の状態から記憶を復元する\n
        不正な状態が渡された場合は無視する(何もしない)

        Args:
            state (dict): 保存された状態
        """
        pass

    def sufficiency_of(self, screen_id: str) -> Expr | None:
        """
        ScreenTable から指定の Screen ID の充足条件を取得する\n
        指定の Screen ID にあたるものが存在しない場合は None を返す\n
        None が指定されている場合は恒真とする

        Args:
            screen_id (str): Screen ID

        Returns:
            Expr | None: 充足条件
        """
        screen_config = self.screen_table.get(screen_id)
        if screen_config is None:
            return None

        return screen_config.sufficiency if screen_config.sufficiency is not None else TrueExpr()

    def sync(self, prompt: Prompt) -> Prompt | None:
        """
        Screen を貫通して記憶するデータと, 記憶中のデータの同期を行う\n
        各派生クラスで定義された Screen ID ごとの処理を実施\n
        定義されていない(None)場合は何もしない\n
        初めて一致した Screen ID についてのみ実施\n
        None についてはそのまま None を返す\n
        本関数は非破壊的である

        Args:
            prompt (Prompt): プロンプト
        """
        if prompt is None:
            return None

        screen_config = self.screen_table.get(prompt.screen_id)
        if screen_config is None:
            return None
        elif screen_config.syncer is None:
            return prompt

        memory = prompt_to_memory(prompt)
        if memory is None:
            return None
        return screen_config.syncer(memory).to_prompt(prompt.screen_id)

    def strip(self, prompt: Prompt | None) -> Prompt | None:
        """
        カテゴリーリストに存在しない PromptParts を削ぎ落とす\n
        ただし common は必ず結果に含める\n
        None についてはそのまま None を返す\n
        本関数は非破壊的である

        Args:
            prompt (Prompt | None): Prompt

        Returns:
            Prompt | None: Prompt
        """
        if prompt is None:
            return None

        screen_config = self.screen_table.get(prompt.screen_id)
        if screen_config is None:
            return None

        def strip_(parts_list: list[PromptParts]) -> list[PromptParts]:
            result: list[PromptParts] = []
            for parts in parts_list:
                if len(parts.path) == 0:
                    # common は必ず追加
                    result.append(parts)
                    continue

                if parts.path in screen_config.cat_configs:
                    # CategoryPath がリスト内にある
                    result.append(parts)
            return result

        result = Prompt(screen_id=prompt.screen_id)
        result.positive = strip_(prompt.positive)
        result.negative = strip_(prompt.negative)

        return result

    def dedupe(self, prompt: Prompt | None) -> Prompt | None:
        """
        Prompt 内の重複トークンを排除し, 単一の正規トークンに統合する\n
        同一の token 文字列を持つ Token が複数の PromptParts にまたがって存在する場合,
        以下のルールに従って一つに絞り込む：\n
        **採用するトークン (weight の選択)**:
            |weight - 1| が最大のもの, すなわち強調・減衰度合いが最も強いものを採用する
            同点の場合は前に出現したものが優先される\n
        **配置先の CategoryPath (位置の選択)**:
            重複するトークンを含む CategoryPath 群のうち, `category_list` において
            最も早く登場するものに統一する
            ただし common (path が空) は配置先候補から除外され, 常に他の明示的な Path が優先される\n
        **出現順序の保持**:
            配置先 Path が決定した後, 元の PromptParts 内での出現インデックス (idx) を
            基準として昇順に並べ直すことで, 元の順序感を可能な限り維持する\n
        本関数は非破壊的である\n
        prompt が None の場合はそのまま None を返す

        Args:
            prompt (Prompt | None): 重複排除対象の Prompt

        Returns:
            Prompt | None: 重複排除済みの新しい Prompt
        """
        if prompt is None:
            return None

        screen_config = self.screen_table.get(prompt.screen_id)
        if screen_config is None:
            return None

        category_list = list(screen_config.cat_configs.keys())
        category_list.append(())  # common 用に末尾に空の Path を追加

        type Best = dict[str, tuple[Token, set[tuple[CategoryPath, int]]]]

        def make_best_(parts_list: list[PromptParts]) -> Best:
            """
            最も weight が 1 から遠いトークンと, 収集元の CategoryPath をすべて記録する
            """
            best: Best = {}
            for parts in parts_list:
                for token in parts.tokens:
                    score = abs(token.weight - 1.0)
                    current = best.get(token.token)
                    idx = parts.tokens.index(token)
                    if current is None:
                        best[token.token] = (token, {(parts.path, idx)})
                    else:
                        crnt_token = token if score > abs(current[0].weight - 1.0) else current[0]
                        # common (= path が空)は最優先候補になり得ないので Path 候補から除外
                        crnt_paths = current[1] | {(parts.path, idx)} if parts.path else current[1]
                        best[token.token] = (crnt_token, crnt_paths)
            return best

        def make_new_parts_(best: Best) -> list[PromptParts]:
            """
            Best から重複排除済みの PromptParts リストを再構築する

            1. best の各トークンについて, category_paths の順序に従って最優先の Path を決定
            2. 元の出現順序 (idx) を保持しながら PromptParts を生成
            3. 同じ Path を持つトークンを集約して最終的な parts リストを構築
            """
            new_parts_n_idxs: list[tuple[PromptParts, int]] = []
            appended: set[str] = set()
            for token_key, (best_token, best_paths_idxs) in best.items():
                for path in category_list:
                    for best_path, best_idx in best_paths_idxs:
                        if token_key in appended or path != best_path:
                            # Path 候補が複数ある場合の対策
                            continue

                        # 初めてひっかかった, つまり最優先のカテゴリーパスのみ採用
                        new_parts_n_idxs.append(
                            (PromptParts(path=best_path, tokens=[best_token]), best_idx)
                        )
                        appended.add(token_key)

            # idx (= tuple[1]) について昇順にソート
            sorted_list = sorted(new_parts_n_idxs, key=lambda t: t[1])

            new_parts_list: list[PromptParts] = []
            for parts, _ in sorted_list:
                # ソート 済みなので順に加えていけば idx について昇順
                for member_parts in new_parts_list:
                    if parts.path == member_parts.path:
                        member_parts.tokens.extend(parts.tokens)
                        break
                else:
                    new_parts_list.append(parts)

            return new_parts_list

        return Prompt(
            screen_id=prompt.screen_id,
            positive=make_new_parts_(make_best_(prompt.positive)),
            negative=make_new_parts_(make_best_(prompt.negative)),
        )

    def sift(self, prompt: Prompt | None) -> Prompt | None:
        """
        CategoryPath ごとに存在適性を確認し, 適するもののみとなるようふるいがけする\n
        ふるいがけルールはカテゴリーリストの各 Path に紐づくものによる\n
        ただし common は必ず結果に含める\n
        None についてはそのまま None を返す\n
        本関数は非破壊的である

        Args:
            prompt (Prompt | None): ふるいがけ対象の Prompt

        Returns:
            Prompt | None: ふるいがけ済みの新しい Prompt
        """
        if prompt is None:
            return None

        screen_config = self.screen_table.get(prompt.screen_id)
        if screen_config is None:
            return None

        def sift_(parts_list: list[PromptParts]) -> list[PromptParts]:
            existing_paths: set[CategoryPath] = set()
            for parts in parts_list:
                existing_paths.add(parts.path)
            new_parts_list: list[PromptParts] = []
            for parts in parts_list:
                if len(parts.path) == 0:
                    # common は必ず追加
                    new_parts_list.append(parts)
                    continue

                cond = screen_config.sift_condition_of(parts.path)
                if cond is not None and cond.eval(existing_paths):
                    new_parts_list.append(parts)
            return new_parts_list

        return Prompt(
            screen_id=prompt.screen_id,
            positive=sift_(prompt.positive),
            negative=sift_(prompt.negative),
        )

    def sort(self, prompt: Prompt | None) -> Prompt | None:
        """
        PromptBase を適切にソートする\n
        ソートルールはカテゴリーリスト内の CategoryPath の順序に従う\n
        リスト内にない CategoryPath は順に最後尾に置き換えられ,\n
        リスト内の存在しない CategoryPath は無視される\n
        また(通常は誤って)同じ CategoryPath がリスト内に存在する場合, 比べて後ろの位置となる\n
        None についてはそのまま None を返す\n
        本関数は非破壊的である

        Args:
            prompt (Prompt | None): ソート対象の Prompt

        Returns:
            Prompt | None: ソート済みの新しい Prompt
        """
        if prompt is None:
            return None

        screen_config = self.screen_table.get(prompt.screen_id)
        if screen_config is None:
            return None

        def sort_(parts_list: list[PromptParts]) -> list[PromptParts]:
            order_index: dict[CategoryPath, int] = {}
            i = 0
            for path in screen_config.cat_configs:
                order_index[path] = i
                i += 1
            return sorted(parts_list, key=lambda c: order_index.get(c.path, float("inf")))

        return Prompt(
            screen_id=prompt.screen_id,
            positive=sort_(prompt.positive),
            negative=sort_(prompt.negative),
        )

    def edit(self, prompt: Prompt | None) -> Prompt | None:
        """
        非破壊的に prompt を編集, 記録する\n
        None についてはそのまま None を返す

        Args:
            prompt (Prompt | None): Prompt

        Returns:
            Prompt | None: Prompt
        """
        if prompt is None:
            return None

        return self.sort(self.sync(self.sift(self.dedupe(self.strip(prompt)))))

    def strip_reports(self, reports: list[Report]) -> list[Report]:
        """
        非破壊的に残すべきでないレポートを削ぎ落とす

        Args:
            reports (list[Report]): レポートリスト

        Returns:
            list[Report]: 残すべきもののみとなったレポートのリスト
        """
        new_reports: list[Report] = []
        for report in reports:
            screen_config = self.screen_table.get(report.screen_id)
            if screen_config is None:
                continue

            if screen_config.should_leave_report_of(report.paths):
                new_reports.append(report)
        return new_reports

    def make_prompt(self, text: str) -> tuple[Prompt | None, list[Report]]:
        """
        テキストをもとに Prompter によって Prompt を得る\n
        Prompt は dedupe かつ sort 済み, 加えて edit も実施済みである\n
        Prompter 未指定の場合は None を返す

        Args:
            text (str): テキスト

        Returns:
            tuple[Prompt | None, list[Report]]: Prompt, Prompter 未指定の場合に None
            及び Prompt 化の際のレポート
        """
        if self.prompter is None:
            return None

        prompt, reports = self.prompter.to_prompt(text)
        return self.edit(prompt), self.strip_reports(reports)

    def check_sufficiency_of(self, prompt: Prompt) -> bool:
        """
        指定の Prompt が生成に十分な情報を持っているか\n
        ScreenConfig 上で指定された不可欠 CategoryPath をすべて持っているかを確認する\n
        指定の CategoryPath はポジティブ・ネガティブプロンプトの一方に存在すればよいものとする\n
        None であったり, 両プロンプトが空である場合は False\n
        本関数は make_prompt() にて得られた Prompt を対象とすることを想定している(特に strip())

        Args:
            prompt (Prompt): Prompt

        Returns:
            bool: True: 十分, False: 不十分(空文字列)
        """
        if prompt is None or (not prompt.positive and not prompt.negative):
            return False

        existing_paths: set[CategoryPath] = set()
        for parts in prompt.positive:
            existing_paths.add(parts.path)
        for parts in prompt.negative:
            existing_paths.add(parts.path)

        return self.sufficiency_of(prompt.screen_id).eval(existing_paths)
