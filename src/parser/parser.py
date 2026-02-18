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
from typing import TypeAlias

import pyperclip

from common.functions import BottleMail, dirname_by_prompts, dump_json
from master.events import NewPrompts, ParserEvent
from master.interfaces import MasterIF
from parser.prompter import (
    CategoryPath,
    PromptBase,
    Prompter,
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
class CategorizedTokens:
    tokens: list[Token] = field(default_factory=list)
    path: CategoryPath = field(default_factory=CategoryPath)


Prompt: TypeAlias = list[CategorizedTokens]


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

    def dedupe(self, prompt_base: PromptBase) -> PromptSet:
        """
        PromptBase から PromptSet を得る\n
        同じ token を持つ Token のうち, |weight - 1| が最大のものを残す\n
        順序は同じ token を持つ CategoryPath において,\n
        priority で指定されている内の最も早いものに統一する

        Args:
            prompt_base (PromptBase): PromptBase

        Returns:
            PromptSet: PromptSet
        """

        def update_best(
            best: dict[str, tuple[Token, set[CategoryPath]]], token: Token, path: CategoryPath
        ) -> None:
            score = abs(token.weight - 1.0)
            current = best.get(token.token)
            if current is None:
                best[token.token] = (token, {path})
            else:
                crnt_token = token if score > abs(current[0].weight - 1.0) else current[0]
                crnt_paths = current[1] | {path}
                best[token.token] = (crnt_token, crnt_paths)

        best_pos: dict[str, tuple[Token, set[CategoryPath]]] = {}
        best_neg: dict[str, tuple[Token, set[CategoryPath]]] = {}

        for screen in prompt_base:
            for cat in screen.categories:
                for token in cat.positive:
                    update_best(best_pos, token, (screen.screen_id,) + cat.path)
                for token in cat.negative:
                    update_best(best_neg, token, (screen.screen_id,) + cat.path)

        def _filter(
            tokens: list[Token], best: dict[str, tuple[Token, set[CategoryPath]]]
        ) -> tuple[list[Token], CategoryPath]:
            result_tokens = []
            result_path = None
            for token in tokens:
                if best.get(token.token) is not None and best.get(token.token)[0] is token:
                    result_tokens.append(token)
                    if result_path is None:
                        result_path = next(
                            (p for p in self.priority if p in best[token.token][1]), None
                        )
                    best.pop(token.token)
            return result_tokens, result_path

        positive: Prompt = []
        negative: Prompt = []
        for screen in prompt_base:
            new_categorized_tokens_list = []
            for category in screen.categories:
                tokens, path = _filter(category.positive, best_pos)
                new_categorized_tokens_list.append(CategorizedTokens(tokens=tokens, path=path))
            positive.extend(new_categorized_tokens_list)
            new_categorized_tokens_list = []
            for category in screen.categories:
                tokens, path = _filter(category.negative, best_neg)
                new_categorized_tokens_list.append(CategorizedTokens(tokens=tokens, path=path))
            negative.extend(new_categorized_tokens_list)

        return PromptSet(positive=positive, negative=negative)

    def sort(self, prompt: Prompt) -> Prompt:
        """
        PromptBase を適切にソートする\n
        ソートルールは priority 内の CategoryPath の順序に従う\n
        priority 内にない CategoryPath は順に最後尾に置き換えられ,\n
        priority 内の存在しない CategoryPath は無視される\n
        また(通常は誤って)同じ CategoryPath が priority 内に存在する場合, 最も後ろの位置となる
        """
        order_index: dict[CategoryPath, int] = {path: i for i, path in enumerate(self.priority)}

        return sorted(prompt, key=lambda c: order_index.get(c.path, float("inf")))

    @abstractmethod
    def edit(self, prompt_base: PromptBase) -> PromptBase:
        """
        dedupe, sort 以外の処理を行う

        Args:
            prompt_base (PromptBase): PromptBase

        Returns:
            PromptBase: PromptBase
        """
        pass

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
            prompt_set = self.dedupe(self.prompter.to_prompt_base(text))

        return self.edit(PromptSet(self.sort(prompt_set.positive), self.sort(prompt_set.negative)))

    def make_prompt_strs(self) -> tuple[str, str]:
        """
        現在の Prompter 成果物からプロンプト文字列を生成する

        Returns:
            str: プロンプト文字列
        """

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
    def is_enough_prompt(self) -> bool:
        """
        生成に十分なプロンプトか\n
        判定基準は各派生クラスに依存

        Returns:
            bool: True: 十分, False: 不十分(空文字列)
        """
        return

    def inform_new_prompt(self, prompt_set: PromptSet) -> None:
        """
        Master に新たなプロンプトを報告する\n
        更新がない, あるいは情報が不十分な場合は何もしない

        Args:
            prompt_set (PromptSet): PromptSet
        """
        if self.is_enough_prompt():
            self.to_master.enclose(NewPrompts(is_enough=False))
            return

        if prompt_set == self.crnt_prompt_set:
            return
        self.crnt_prompt = prompt_set

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
                print(f"Any exception occurred in {threading.current_thread().name}: ", e)
