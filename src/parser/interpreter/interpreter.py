"""
Prompt 解釈クラス
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from common.expr import Expr, TrueExpr
from parser.prompter import CategoryPath, Prompt, Prompter, PromptParts, Report, Token


@dataclass(frozen=True)
class KeyEntry:
    pos_tokens: tuple[tuple[str, float], ...]
    neg_tokens: tuple[tuple[str, float], ...]

    def stringfy(self) -> str:
        """
        ラベル文字列用にポジティブプロンプトの先頭トークンのみを文字列化する\n
        ポジティブプロンプトが空ならネガティブプロンプトの先頭トークンを用いる\n
        重さは付与しない

        Returns:
            str: 重さがないトークン文字列
        """
        return f"{self.pos_tokens[0][0]}" if self.pos_tokens else f"{self.neg_tokens[0][0]}"


@dataclass
class MemoryEntry:
    """
    ポジティブ・ネガティブを CategoryPath でまとめて記憶するためのデータ定義
    """

    pos_tokens: list[Token] = field(default_factory=list)
    neg_tokens: list[Token] = field(default_factory=list)

    def to_key_entry(self) -> KeyEntry:
        return KeyEntry(
            pos_tokens=tuple((t.token, t.weight) for t in self.pos_tokens),
            neg_tokens=tuple((t.token, t.weight) for t in self.neg_tokens),
        )


@dataclass
class Memory:
    """
    ポジティブプロンプトとネガティブプロンプトを CategoryPath ごとに束ねたデータ
    """

    screen_id: str = ""
    entries: dict[CategoryPath, MemoryEntry] = field(default_factory=dict)

    def get_key_entry(self, keyname: str) -> KeyEntry | None:
        """
        キーカテゴリー名にあたる KeyEntry を取得する\n
        存在しない場合は None を返す

        Args:
            keyname (str): キーカテゴリー名

        Returns:
            KeyEntry | None: MemoryEntry
        """
        for path, entry in self.entries.items():
            if len(path) > 0 and path[-1] == keyname:
                return entry.to_key_entry()
        return None

    def to_prompt(self) -> Prompt:
        """
        Prompt への変換

        Returns:
            Prompt: Prompt
        """
        prompt = Prompt(screen_id=self.screen_id)
        for path, entry in self.entries.items():
            if entry.pos_tokens:
                prompt.positive.append(PromptParts(path=path, tokens=entry.pos_tokens))
            if entry.neg_tokens:
                prompt.negative.append(PromptParts(path=path, tokens=entry.neg_tokens))
        return prompt

    def stringfy(self) -> dict[str, dict[str, MemoryEntry]]:
        return {
            self.screen_id: {
                (path if isinstance(path, CategoryPath) else CategoryPath(path)).stringfy(): entry
                for path, entry in self.entries.items()
            }
        }


# キーカテゴリーごとの Memory
type Record = dict[
    KeyEntry,  # キーカテゴリーにあたる MemoryEntry (immutable)
    Memory,
]


@dataclass
class PromptContainer:
    prompt: Prompt
    records: dict[str, Record]
    last_memory: Memory
    keyname: str


@dataclass
class CompatiblePrompt(Prompt):
    """
    Memory との相互互換性を持つ Prompt
    """

    def to_memory(self) -> Memory:
        """
        Memory への変換

        Returns:
            Memory: Memory
        """
        memory = Memory(screen_id=self.screen_id)
        for parts in self.positive:
            memory.entries[parts.path] = MemoryEntry(pos_tokens=list(parts.tokens))
        for parts in self.negative:
            if parts.path in memory.entries:
                entry = memory.entries.get(parts.path)
                # dedupe されている場合は代入と変わらない
                entry.neg_tokens.extend(list(parts.tokens))
            else:
                # ポジティブ側になかった場合は単独で登録
                memory.entries[parts.path] = MemoryEntry(neg_tokens=list(parts.tokens))
        return memory


@dataclass(frozen=True)
class CategoryConfig:
    sift_condition: Expr  # ふるいがけ条件
    log_report: bool  # Report を残すか

    @classmethod
    def set(
        cls,
        sift_condition: Expr | None,  # None = 恒真
        log_report: bool,
    ):
        return cls(
            sift_condition=sift_condition if sift_condition is not None else TrueExpr(),
            log_report=log_report,
        )


@dataclass(frozen=True)
class ScreenConfig:
    cat_configs: dict[CategoryPath, CategoryConfig]  # カテゴリーコンフィグ
    sufficiency: Expr  # 充足条件
    request_cats: dict[str, list[CategoryPath]]  # 他の Screen から要求するカテゴリーの一覧
    takeover_cats: list[CategoryPath]  # 直前 Screen から引き継ぐカテゴリーの一覧

    @classmethod
    def set(
        cls,
        cat_configs: dict[CategoryPath, tuple[Expr | None, bool]],
        sufficiency: Expr | None = None,  # None = 恒真
        request_cats: dict[str, list[CategoryPath]] | None = None,  # None = 無指定
        takeover_cats: list[CategoryPath] | None = None,  # None = 無指定
    ):
        return cls(
            cat_configs={cat: CategoryConfig.set(cc[0], cc[1]) for cat, cc in cat_configs.items()},
            sufficiency=sufficiency if sufficiency is not None else TrueExpr(),
            request_cats=request_cats if request_cats is not None else {},
            takeover_cats=takeover_cats if takeover_cats is not None else [],
        )

    def strip(self, container: PromptContainer) -> None:
        """
        カテゴリーリストに存在しない PromptParts を削ぎ落とす\n
        ただし common は必ず結果に含める

        Args:
            container (PromptContainer): PromptContainer
        """

        def strip_(parts_list: list[PromptParts]) -> list[PromptParts]:
            result: list[PromptParts] = []
            for parts in parts_list:
                if len(parts.path) == 0:
                    # common は必ず追加
                    result.append(parts)
                    continue

                if parts.path in self.cat_configs:
                    # CategoryPath がリスト内にある
                    result.append(parts)
            return result

        container.prompt = Prompt(
            screen_id=container.prompt.screen_id,
            positive=strip_(container.prompt.positive),
            negative=strip_(container.prompt.negative),
        )

    def dedupe(self, container: PromptContainer) -> None:
        """
        Prompt 内の重複トークンを排除し, 単一の正規トークンに統合する\n
        同一の token 文字列を持つ Token が複数の PromptParts にまたがって存在する場合,
        以下のルールに従って一つに絞り込む:\n
        1. 採用するトークン (weight の選択):\n
            |weight - 1| が最大のもの, すなわち強調・減衰度合いが最も強いものを採用する
            同点の場合は前に出現したものが優先される\n
        2. 配置先の CategoryPath (位置の選択):\n
            重複するトークンを含む CategoryPath 群のうち, `category_list` において
            最も早く登場するものに統一する
            ただし common (path が空) は配置先候補から除外され, 常に他の明示的な Path が優先される\n
        3. 出現順序の保持:\n
            配置先 Path が決定した後, 元の PromptParts 内での出現インデックス (idx) を
            基準として昇順に並べ直すことで, 元の順序感を可能な限り維持する\n

        Args:
            container (PromptContainer): 重複排除対象の PromptContainer
        """
        category_list = list(self.cat_configs.keys())
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

        container.prompt = Prompt(
            screen_id=container.prompt.screen_id,
            positive=make_new_parts_(make_best_(container.prompt.positive)),
            negative=make_new_parts_(make_best_(container.prompt.negative)),
        )

    def sift(self, container: PromptContainer) -> None:
        """
        CategoryPath ごとに存在適性を確認し, 適するもののみとなるようふるいがけする\n
        ふるいがけルールはカテゴリーリストの各 Path に紐づくものによる\n
        ただし common は必ず結果に含める

        Args:
            prompt (PromptContainer): ふるいがけ対象の PromptContainer
        """

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

                cat_config = self.cat_configs.get(parts.path)
                if cat_config is None:
                    raise ValueError(f"No such category, '{parts.path}'.")

                if cat_config.sift_condition.eval(existing_paths):
                    new_parts_list.append(parts)
            return new_parts_list

        container.prompt = Prompt(
            screen_id=container.prompt.screen_id,
            positive=sift_(container.prompt.positive),
            negative=sift_(container.prompt.negative),
        )

    def sync(self, container: PromptContainer) -> None:
        """
        Screen を貫通して記憶するデータと, 記憶中のデータの同期を行う\n
        TakeOver: 直前の Screen からキーカテゴリーをもとに求めるカテゴリー群を追加\n
                  (キーカテゴリーにあたるエントリーが存在しない場合も補填)\n
        Request: 各 Screen の最新の記憶からキーカテゴリーをもとに求めるカテゴリー群を追加\n
        Offer: 自身の Screen に紐づくエントリーをすべて提供

        Args:
            container (PromptContainer): PromptContainer
        """
        memory = CompatiblePrompt(
            screen_id=container.prompt.screen_id,
            positive=container.prompt.positive,
            negative=container.prompt.negative,
        ).to_memory()

        # TakeOver: キーカテゴリーを引き継ぐことも想定して Request 前に実施
        if container.last_memory is not None:
            for path in self.takeover_cats:
                last_mem_entry = container.last_memory.entries.get(path)
                if last_mem_entry is not None:
                    memory.entries[path] = last_mem_entry

        # Request: キーカテゴリーが合致する Memory を要求
        for screen_id, paths in self.request_cats.items():
            record = container.records.get(screen_id)
            if record is None:
                continue

            rec_memory = record.get(memory.get_key_entry(container.keyname))
            if rec_memory is None:
                continue

            for path in paths:
                if path in rec_memory.entries:
                    memory.entries[path] = deepcopy(rec_memory.entries[path])
        container.prompt = memory.to_prompt()

        # Offer: Memory 上のすべての MemoryEntry をキーカテゴリーと紐づけて提供
        key_entry = memory.get_key_entry(container.keyname)
        common_purged_memory = Memory(
            screen_id=memory.screen_id,
            entries={path: entry for path, entry in memory.entries.items() if path},
        )
        if key_entry is not None:
            if container.prompt.screen_id in container.records:
                container.records[container.prompt.screen_id][key_entry] = common_purged_memory
            else:
                container.records[container.prompt.screen_id] = {key_entry: common_purged_memory}
        container.last_memory.screen_id = common_purged_memory.screen_id
        container.last_memory.entries = deepcopy(common_purged_memory.entries)

    def sort(self, container: PromptContainer) -> None:
        """
        PromptBase を適切にソートする\n
        ソートルールはカテゴリーリスト内の CategoryPath の順序に従う\n
        リスト内にない CategoryPath は順に最後尾に置き換えられ,\n
        リスト内の存在しない CategoryPath は無視される\n
        また(通常は誤って)同じ CategoryPath がリスト内に存在する場合, 比べて後ろの位置となる

        Args:
            container (PromptContainer): ソート対象の PromptContainer
        """

        def sort_(parts_list: list[PromptParts]) -> list[PromptParts]:
            order_index: dict[CategoryPath, int] = {}
            i = 0
            for path in self.cat_configs:
                order_index[path] = i
                i += 1
            return sorted(parts_list, key=lambda c: order_index.get(c.path, float("inf")))

        container.prompt = Prompt(
            screen_id=container.prompt.screen_id,
            positive=sort_(container.prompt.positive),
            negative=sort_(container.prompt.negative),
        )

    def edit(
        self, prompt: Prompt | None, records: dict[str, Record], last_memory: Memory, keyname: str
    ) -> Prompt | None:
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

        container = PromptContainer(
            prompt=prompt, records=records, last_memory=last_memory, keyname=keyname
        )
        self.strip(container)
        self.dedupe(container)
        self.sift(container)
        self.sync(container)
        self.sort(container)
        return container.prompt

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
            should_append = False
            for cat_path, cat_config in self.cat_configs.items():
                if cat_path in report.paths:
                    should_append = cat_config.log_report
            if should_append:
                new_reports.append(report)
        return new_reports


type ScreenTable = dict[
    str,  # Screen ID
    ScreenConfig,
]


class Interpreter:
    """
    クリップボード監視, ステータス記録クラス
    """

    def __init__(self, yamlpath: Path, keyname: str):
        """
        コンストラクタ

        ScreenTable: Screen ID の順序はプロンプト化における優先順位を表す

        Args:
            yamlpath (Path): YAML パス
        """
        self.prompter: Prompter = None
        self.yamlpath = yamlpath
        self.screen_table: ScreenTable = {}
        self.records: dict[str, Record] = {}  # Screen ごとの Record
        self.last_memory = Memory()
        self.keyname: str = keyname

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

    def export_state(self) -> tuple[dict[str, Record], Memory]:
        """
        Screen ごとの Record と 直前 Screen の Memory をエクスポートする\n
        記憶がない場合は空の dict と Memory を返す

        Returns:
            dict[str, Record]: Screen ごとの Record
        """
        return self.records, self.last_memory

    def import_state(self, saved: tuple[dict[str, Record], Memory]) -> None:
        """
        Screen ごとの Record と 直前 Screen の Memory をインポートする

        Args:
            saved (dict[stuple[dict[str, Record], Memory]): Record と Memory
        """
        self.records = saved[0]
        self.last_memory = saved[1]

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
            return None, []

        prompt, reports = self.prompter.to_prompt(text)
        if prompt.screen_id is None:
            return None, []

        screen_config = self.screen_table.get(prompt.screen_id)
        if screen_config is None:
            raise ValueError(f"No such screen, '{prompt.screen_id}'.")

        edited = screen_config.edit(prompt, self.records, self.last_memory, self.keyname)
        return edited, screen_config.strip_reports(reports)

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

        screen_config = self.screen_table.get(prompt.screen_id)
        if screen_config is None:
            raise ValueError(f"No such screen, '{prompt.screen_id}'.")

        return screen_config.sufficiency.eval(existing_paths)
