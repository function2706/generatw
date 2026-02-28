"""
クリップボード監視, ステータス記録クラス
"""

from __future__ import annotations

import random
import threading
import time
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path

import pyperclip
import yaml

import master.events
from common.functions import BottleMail, dirname_by_prompts, dump_json
from master.interfaces import MasterIF
from parser.interpreter.debug_interpreter import DebugInterpreter
from parser.interpreter.interpreter import Interpreter
from parser.interpreter.test_interpreter import TestInterpreter
from parser.interpreter.theworld_interpreter import TheWorldInterpreter
from parser.prompter import Prompt

INTERPRETER_LIST: list[type[Interpreter]] = [
    TestInterpreter,
    TheWorldInterpreter,
]


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

    in_debugging: threading.Event = field(default_factory=threading.Event)  # デバッグ中
    shutdown: threading.Event = field(default_factory=threading.Event)  # 終了予定


class Parser:
    """
    クリップボード監視, ステータス記録クラス
    """

    def __init__(self, master: MasterIF, to_master: BottleMail[master.events.ParserEvent]):
        """
        コンストラクタ\n
        YAML がない場合に ValueError を投げる

        Args:
            master (MasterIF): Master インターフェース
            to_master (BottleMail[ParserEvent]): 対 Master IPC
        """
        self.master = master
        self.to_master = to_master

        self.interpreter: Interpreter = None
        self.interpreter_cache: Interpreter = None
        self.debug_interpreter: DebugInterpreter = DebugInterpreter(Consts.debug_yamlpath)

        self.crnt_clipboard = ""
        self.crnt_prompt: Prompt = None

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

    def switch_interpreter(self, yamlpath: Path) -> None:
        """
        指定の YAML に記載された "interpreter" キーに紐づく Interpreter を起動する

        Args:
            yamlpath (Path): YAML パス
        """
        keyword = None
        with open(yamlpath, "r", encoding="utf-8") as f:
            yamldict: dict = yaml.safe_load(f)
            keyword = yamldict.get("interpreter")

        for interpreter in INTERPRETER_LIST:
            if keyword is not None and interpreter.keyword() == keyword:
                self.interpreter = interpreter(yamlpath)
                self.interpreter_cache = deepcopy(self.interpreter)

    def make_prompt_strs(self) -> tuple[str, str]:
        """
        現在の Prompter 成果物からプロンプト文字列を生成する

        Returns:
            str: プロンプト文字列
        """
        if self.crnt_prompt is None:
            return None

        pos_list = [
            token.to_str() for tokens in self.crnt_prompt.positive for token in tokens.tokens
        ]
        neg_list = [
            token.to_str() for tokens in self.crnt_prompt.negative for token in tokens.tokens
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

    def is_enough_prompt(self) -> bool:
        """
        記録中の Prompt が生成に十分な情報を持っているか

        Returns:
            bool: True: 十分, False: 不十分(空文字列)
        """
        if self.event.in_debugging.is_set():
            return self.debug_interpreter.check_essentiality_of(self.crnt_prompt)
        else:
            return self.interpreter.check_essentiality_of(self.crnt_prompt)

    def inform_new_prompt(self, prompt: Prompt) -> None:
        """
        Master に新たなプロンプトを報告する\n
        更新がない, あるいは情報が不十分な場合は何もしない

        Args:
            prompt_set (Prompt): Prompt
        """
        try:
            if not prompt.positive and not prompt.negative:
                # 完全に空の場合は何もしない(想定外クリップボード文字列の検知も含む)
                return

            if prompt == self.crnt_prompt:
                return
            self.crnt_prompt = prompt

            if self.master.crnt_gui_configs.print_new_prompt_set:
                dump_json(prompt, "new_prompt_set")

            if not self.is_enough_prompt():
                # 空ではないが条件を満たさない
                self.to_master.enclose(master.events.NewPrompts(is_enough=False))
                return

            pos, neg = self.make_prompt_strs()
            if self.master.crnt_gui_configs.print_new_prompt:
                dump_json({"POS": pos, "NEG": neg}, "new_prompt")

            self.to_master.enclose(
                master.events.NewPrompts(is_enough=True, positive=pos, negative=neg)
            )
        finally:
            self.event.in_debugging.clear()

    def ready_for_debug(self) -> None:
        """
        クリップボードの編集が許可されている場合はダミーを設定する\n
        そうでない場合はダミープロンプトをワンショットで Master へ伝える
        """
        dummy_input = (
            f"debug name:{str(random.randint(1, 3))} vibe:{str(random.randint(1, 9))}"
            f" upper:{str(random.randint(1, 9))} lower:{str(random.randint(1, 9))}"
        )
        self.event.in_debugging.set()
        if self.master.crnt_gui_configs.allow_edit_clipboard:
            # スレッド上の手順に委ねる
            pyperclip.copy(dummy_input)
            return

        prompt_set = self.debug_interpreter.make_prompt(dummy_input)
        if prompt_set is None:
            return

        self.inform_new_prompt(prompt_set)

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

                prompt = None
                if self.event.in_debugging.is_set():
                    prompt = self.debug_interpreter.make_prompt(new_clipboard)
                elif self.interpreter is not None:
                    prompt = self.interpreter.make_prompt(new_clipboard)

                if prompt is not None:
                    self.inform_new_prompt(prompt)
            except Exception as e:
                raise Exception(
                    f"Any exception occurred in {threading.current_thread().name}: "
                ) from e
