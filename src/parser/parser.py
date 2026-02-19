"""
クリップボード監視, ステータス記録クラス
"""

from __future__ import annotations

import random
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

import pyperclip

from common.functions import BottleMail, dirname_by_prompts, dump_json
from master.events import NewPrompts, ParserEvent
from master.interfaces import MasterIF
from parser.prompter import (
    CategoryPath,
    Prompt,
    Prompter,
    PromptParts,
    Token,
)


@dataclass(frozen=True)
class Consts:
    """
    このクラス関連の定数
    """

    thread_interval_sec = 0.01

    # デバッグ用 YAML
    debug_yamlpath: Path = Path("yamls/Debug.yaml")


@dataclass
class Event:
    """
    イベントフラグ
    """

    shutdown: threading.Event = field(default_factory=threading.Event)  # 終了予定


@dataclass
class PromptSet:
    positive: Prompt = field(default_factory=Prompt)
    negative: Prompt = field(default_factory=Prompt)


class Parser(ABC):
    """
    クリップボード監視, ステータス記録クラス
    """

    def __init__(
        self,
        master: MasterIF,
        to_master: BottleMail[ParserEvent],
        priority: list[CategoryPath],
    ):
        """
        コンストラクタ

        Args:
            master (MasterIF): Master インターフェース
            to_master (BottleMail[ParserEvent]): 対 Master IPC
            priority (list[CategoryPath]): トークン優先度
        """
        self.master = master
        self.to_master = to_master
        self.keyword = self.__class__.__name__

        self.crnt_clipboard = ""
        self.crnt_prompt_set: PromptSet = None
        self.prompter: Prompter = None
        self.prompter_lock = Lock()
        self.priority = priority

        self.event = Event()
        self.parser_thread = threading.Thread(
            target=self.parser, args=(), daemon=True, name="parser"
        )

    def start(self) -> None:
        """
        スレッドを開始する
        """
        self.parser_thread.start()

    def join(self) -> None:
        """
        スレッドの join を行う\n
        すでに死んでいる場合は何もしない
        """
        if not self.parser_thread.is_alive():
            return
        self.parser_thread.join()

    def finalize(self) -> None:
        """
        終了処理
        """
        self.event.shutdown.set()

    def reset_prompter(self, yamlpath: Path) -> None:
        """
        Prompter を指定の YAML で再起動する

        Args:
            yamlpath (Path): YAML パス
        """
        if yamlpath.exists():
            with self.prompter_lock:
                prompter = Prompter.make(yamlpath)
                if prompter.parser_keyword == self.keyword:
                    self.prompter = prompter

    def strip(self, prompt: Prompt) -> Prompt:
        """
        priority に存在しない PromptParts を削ぎ落とす\n
        ただし common は除外する(必ず結果に含める)\n
        本関数は非破壊的である

        Args:
            prompt (Prompt): Prompt

        Returns:
            Prompt: Prompt
        """
        result: Prompt = []
        for prompt_parts in prompt:
            if len(prompt_parts.path) >= 2 and prompt_parts.path not in self.priority:
                continue
            result.append(prompt_parts)
        return result

    def dedupe(self, prompt: Prompt) -> Prompt:
        """
        Prompt において同じ token を持つ Token のうち, |weight - 1| が最大のものを残す\n
        順序は同じ token を持つ CategoryPath において,\n
        priority で指定されている内の最も早いものに統一する\n
        本関数は非破壊的である

        Args:
            prompt (Prompt): Prompt

        Returns:
            Prompt: Prompt
        """

        def update_best(
            best: dict[str, tuple[Token, set[CategoryPath]]], token: Token, path: CategoryPath
        ) -> None:
            """最も weight が 1 に近いトークンと, 収集元の CategoryPath をすべて記録する"""
            score = abs(token.weight - 1.0)
            current = best.get(token.token)
            if current is None:
                best[token.token] = (token, {path})
            else:
                crnt_token = token if score > abs(current[0].weight - 1.0) else current[0]
                crnt_paths = current[1] | {path}
                best[token.token] = (crnt_token, crnt_paths)

        best: dict[str, tuple[Token, set[CategoryPath]]] = {}
        for prompt_parts in prompt:
            for token in prompt_parts.tokens:
                update_best(best, token, prompt_parts.path)

        def filter(
            prompt_parts: PromptParts, best: dict[str, tuple[Token, set[CategoryPath]]]
        ) -> PromptParts:
            result = PromptParts()
            for token in prompt_parts.tokens:
                if best.get(token.token) is not None and best.get(token.token)[0] is token:
                    result.tokens.append(token)
                    if not result.path:
                        result.path = next(
                            (p for p in self.priority if p in best[token.token][1]),
                            prompt_parts.path,
                        )
                    best.pop(token.token)
            return result

        new_prompt: Prompt = []
        for prompt_parts in prompt:
            new_prompt.append(filter(prompt_parts, best))

        return new_prompt

    def sort(self, prompt: Prompt) -> Prompt:
        """
        PromptBase を適切にソートする\n
        ソートルールは priority 内の CategoryPath の順序に従う\n
        priority 内にない CategoryPath は順に最後尾に置き換えられ,\n
        priority 内の存在しない CategoryPath は無視される\n
        また(通常は誤って)同じ CategoryPath が priority 内に存在する場合, 比べて後ろの位置となる\n
        本関数は非破壊的である
        """
        order_index: dict[CategoryPath, int] = {path: i for i, path in enumerate(self.priority)}

        return sorted(prompt, key=lambda c: order_index.get(c.path, float("inf")))

    def edit(self, prompt: Prompt) -> Prompt:
        """
        非破壊的に prompt を編集, 記録する\n
        各派生クラスはこの関数をオーバーライドすべきである(この関数自体を実行するのは構わない)

        Args:
            prompt (Prompt): Prompt

        Returns:
            Prompt: Prompt
        """
        return self.sort(self.dedupe(self.strip(prompt)))

    def make_prompt_set(self, text: str) -> PromptSet | None:
        """
        テキストをもとに Prompter によって PromptSet を得る\n
        PromptSet は dedupe かつ sort 済み, 加えて edit も実施済みである\n
        Prompter 未指定の場合は None を返す

        Args:
            text (str): テキスト

        Returns:
            PromptSet | None: PromptSet, Prompter 未指定の場合に None
        """
        if self.prompter is None:
            return None

        with self.prompter_lock:
            positive, negative = self.prompter.to_prompt(text)

        return PromptSet(positive=self.edit(positive), negative=self.edit(negative))

    def make_prompt_strs(self) -> tuple[str, str]:
        """
        現在の Prompter 成果物からプロンプト文字列を生成する

        Returns:
            str: プロンプト文字列
        """
        if self.crnt_prompt_set is None:
            return None

        pos_list = [
            token.to_str() for tokens in self.crnt_prompt_set.positive for token in tokens.tokens
        ]
        neg_list = [
            token.to_str() for tokens in self.crnt_prompt_set.negative for token in tokens.tokens
        ]

        return ",".join(pos_list), ",".join(neg_list)

    @property
    def crnt_prompt_dir(self) -> str:
        """
        記録中プロンプトに適合するディレクトリ名を返す

        Returns:
            str: ディレクトリ名
        """
        pos, neg = self.make_prompt_strs()
        return dirname_by_prompts(pos, neg)

    @abstractmethod
    def is_enough_prompt(self, prompt_set: PromptSet | None = None) -> bool:
        """
        生成に十分なプロンプトか\n
        判定対象は指定のものか, 現在記憶中の最新プロンプトか\n
        各派生クラスはこの関数をオーバーライドすべきである(この関数自体を実行するのは構わない)

        Args:
            prompt_set (PromptSet | None, optional): PromptSet. Defaults to None.

        Returns:
            bool: True: 十分, False: 不十分(空文字列)
        """
        prmpt_set = prompt_set if prompt_set is not None else self.crnt_prompt_set
        return prmpt_set is not None and (prmpt_set.positive or prmpt_set.negative)

    def inform_new_prompt(self, prompt_set: PromptSet) -> None:
        """
        Master に新たなプロンプトを報告する\n
        更新がない, あるいは情報が不十分な場合は何もしない

        Args:
            prompt_set (PromptSet): PromptSet
        """
        if not prompt_set.positive and not prompt_set.negative:
            # 完全に空の場合は何もしない(想定外クリップボード文字列の検知も含む)
            return

        if prompt_set == self.crnt_prompt_set:
            return
        self.crnt_prompt_set = prompt_set

        if self.master.crnt_gui_configs.print_new_prompt_set:
            dump_json(prompt_set, "new_prompt_set")

        if not self.is_enough_prompt(prompt_set):
            # 空ではないが条件を満たさない
            self.to_master.enclose(NewPrompts(is_enough=False))
            return None

        pos, neg = self.make_prompt_strs()
        if self.master.crnt_gui_configs.print_new_prompt:
            dump_json({"POS": pos, "NEG": neg}, "new_prompt")

        self.to_master.enclose(NewPrompts(is_enough=True, positive=pos, negative=neg))

    def do_debug(self, text: str) -> None:
        """
        デバッグを実行する\n
        Prompter の更新は行わないが, 現在のプロンプトの記録は行う(ディレクトリ名のため)

        Args:
            text (str): テキスト
        """
        original_yamlpath = self.prompter.yamlpath

        self.reset_prompter(Consts.debug_yamlpath)
        prompt_set = self.make_prompt_set(text)
        if prompt_set is None:
            return

        self.reset_prompter(original_yamlpath)
        self.inform_new_prompt(prompt_set)

    def ready_for_debug(self) -> None:
        """
        クリップボードの編集が許可されている場合はダミーを設定する\n
        そうでない場合はダミープロンプトをワンショットで Master へ伝える
        """
        dummy_input = (
            f"debug name:{str(random.randint(1, 3))} vibe:{str(random.randint(1, 9))}"
            f" upper:{str(random.randint(1, 9))} lower:{str(random.randint(1, 9))}"
        )
        if self.master.crnt_gui_configs.allow_edit_clipboard:
            pyperclip.copy(dummy_input)

        self.do_debug(dummy_input)

    def parser(self) -> None:
        """
        クリップボード監視を行い, プロンプトの生成と報告を行う
        """
        while not self.event.shutdown.is_set():
            time.sleep(Consts.thread_interval_sec)
            try:
                new_clipboard = pyperclip.paste()
                if self.crnt_clipboard == new_clipboard:
                    continue

                self.crnt_clipboard = new_clipboard

                if self.master.crnt_gui_configs.print_new_clipboard:
                    print("new_clipboard:")
                    print(new_clipboard)

                prompt_set = self.make_prompt_set(new_clipboard)
                if prompt_set is not None:
                    self.inform_new_prompt(prompt_set)
            except Exception as e:
                raise Exception(
                    f"Any exception occurred in {threading.current_thread().name}: "
                ) from e
