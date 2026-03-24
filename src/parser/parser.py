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
from parser.interpreter.reverse_interpreter import ReverseInterpreter
from parser.interpreter.test_interpreter import TestInterpreter
from parser.interpreter.theworld_interpreter import TheWorldInterpreter
from parser.prompter import Prompt

INTERPRETER_LIST: list[type[Interpreter]] = [
    TestInterpreter,
    TheWorldInterpreter,
    ReverseInterpreter,
]


def safe_paste(retry: int = 5, delay: float = 0.1) -> str | None:
    """
    クリップボードから文字列を取得する\n
    PyperclipWindowsException (pyperclip が Windows 上でクリップボードを open できない)については\n
    delay 秒ごとに retry 回再試行し, すべてに失敗した場合に None を返す

    Args:
        retry (int, optional): リトライ回数. Defaults to 5.
        delay (float, optional): リトライ間隔. Defaults to 0.1.

    Returns:
        str | None: 文字列, 失敗時に None
    """
    for _ in range(retry):
        try:
            return pyperclip.paste()
        except pyperclip.PyperclipWindowsException:
            time.sleep(delay)
    return None


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
        with open(yamlpath, encoding="utf-8") as f:
            yamldict: dict = yaml.safe_load(f)
            keyword = yamldict.get("interpreter")

        for interpreter in INTERPRETER_LIST:
            if keyword is not None and interpreter.keyword() == keyword:
                self.interpreter = interpreter(yamlpath)
                self.interpreter_cache = deepcopy(self.interpreter)

    def reload_interpreter(self, carry_over: bool = False) -> None:
        """
        YAML の再読み込みを実施する

        Args:
            carry_over (bool, optional): インスタンスに記憶データがある場合持ち越すか
        """
        if self.interpreter is None:
            return

        saved_state = None
        if carry_over:
            saved_state = self.interpreter.export_state()

        self.interpreter.reload_prompter()
        if carry_over and saved_state is not None:
            self.interpreter.import_state(saved_state)

        self.interpreter_cache = deepcopy(self.interpreter)

    def make_prompt_strs(self) -> tuple[str, str] | None:
        """
        現在の Prompter 成果物からプロンプト文字列を生成する\n
        現在のプロンプトが未指定 (None) の場合は None を返す

        Returns:
            str | None: プロンプト文字列
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
        記録中プロンプトに適合するディレクトリ名を返す\n
        現在のプロンプトが未指定 (None) の場合は None を返す

        Returns:
            str | None: ディレクトリ名
        """
        strs = self.make_prompt_strs()
        return dirname_by_prompts(strs[0], strs[1]) if strs is not None else None

    def is_enough_prompt(self) -> bool:
        """
        記録中の Prompt が生成に十分な情報を持っているか

        Returns:
            bool: True: 十分, False: 不十分(空文字列)
        """
        if self.event.in_debugging.is_set():
            return self.debug_interpreter.check_sufficiency_of(self.crnt_prompt)
        elif self.interpreter is not None:
            return self.interpreter.check_sufficiency_of(self.crnt_prompt)
        return False

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

        prompt_set, _ = self.debug_interpreter.make_prompt(dummy_input)
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
                new_clipboard = safe_paste()
                if new_clipboard is None:
                    print("Clipboard unavailable, retrying...")
                    continue

                if self.crnt_clipboard == new_clipboard:
                    continue

                self.crnt_clipboard = new_clipboard

                if self.master.crnt_gui_configs.print_new_clipboard:
                    print("new_clipboard:")
                    print(new_clipboard)

                prompt = None
                if self.event.in_debugging.is_set():
                    prompt, _ = self.debug_interpreter.make_prompt(new_clipboard)
                elif self.interpreter is not None:
                    prompt, reports = self.interpreter.make_prompt(new_clipboard)
                    if reports:
                        self.to_master.enclose(master.events.NewReports(reports))

                if prompt is not None:
                    self.inform_new_prompt(prompt)
            except Exception as e:
                raise Exception(
                    f"Any exception occurred in {threading.current_thread().name}: "
                ) from e
