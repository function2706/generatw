"""
クリップボード監視, ステータス記録クラス
"""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

import pyperclip

from common.functions import BottleMail, dirname_by_prompts
from master.events import NewPrompts, ParserEvent
from master.interfaces import MasterIF
from parser.prompter import Prompter


@dataclass(frozen=True)
class Consts:
    """
    このクラス関連の定数
    """

    thread_interval_sec = 0.1

    # デバッグ用 YAML
    debug_yamlpath: Path = Path("yamls/Debug.yaml")


@dataclass
class Event:
    """
    イベントフラグ
    """

    shutdown: threading.Event = field(default_factory=threading.Event)  # 終了予定
    is_debugging: threading.Event = field(default_factory=threading.Event)  # デバッグ予定


class Parser:
    """
    クリップボード監視, ステータス記録クラス
    """

    def __init__(self, master: MasterIF, to_master: BottleMail[ParserEvent]):
        """
        コンストラクタ

        Args:
            master (MasterIF): Master インターフェース
            to_master (BottleMail[ParserEvent]): 対 Master IPC
        """
        self.master = master
        self.to_master = to_master

        self.crnt_clipboard = ""
        self.prompter: Prompter = None
        self.prompter_lock = Lock()
        self.crnt_positive = ""
        self.crnt_negative = ""

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

    @property
    def crnt_prompt_dir(self) -> str:
        """
        記録中プロンプトに適合するディレクトリ名を返す

        Returns:
            str: ディレクトリ名
        """
        return dirname_by_prompts(self.crnt_positive, self.crnt_negative)

    def reset_prompter(self, yamlpath: Path) -> None:
        """
        Prompter を指定の YAML で再起動する

        Args:
            yamlpath (Path): YAML パス
        """
        if yamlpath.exists():
            with self.prompter_lock:
                self.prompter = Prompter.make(yamlpath)

    def is_enough_prompt(self) -> bool:
        """
        生成に十分なプロンプトか

        Returns:
            bool: True: 十分, False: 不十分(空文字列)
        """
        return self.crnt_positive or self.crnt_negative

    def report_new_prompt(self, pos: str, neg: str) -> None:
        """
        Master に新たなプロンプトを報告する\n
        pos, neg の双方が空の場合は情報不十分と見なし, 何もしない

        Args:
            pos (str): ポジティブプロンプト
            neg (str): ネガティブプロンプト
        """
        if not pos and not neg:
            return

        if self.master.crnt_gui_configs.print_new_prompt:
            print(f'POS: "{pos}"')
            print(f'NEG: "{neg}"')

        self.crnt_positive = pos
        self.crnt_negative = neg
        self.to_master.enclose(NewPrompts(positive=pos, negative=neg))

    def do_debug(self, text: str) -> None:
        """
        デバッグを実行する\n
        Prompter の更新は行わないが, 現在のプロンプトの記録は行う(ディレクトリ名のため)

        Args:
            text (str): テキスト
        """
        self.reset_prompter(Consts.debug_yamlpath)
        with self.prompter_lock:
            pos, neg = self.prompter.toprompt(text)

        self.report_new_prompt(pos, neg)

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
            # クリップボードを変更する場合はその後の工程を正規手順に委ねる
            pyperclip.copy(dummy_input)
            self.event.is_debugging.set()
            return

        # クリップボードを変更しない場合はワンショットで直接生成する
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

                if self.event.is_debugging.is_set():
                    self.do_debug(new_clipboard)
                    self.event.is_debugging.clear()
                elif self.prompter is not None:
                    with self.prompter_lock:
                        pos, neg = self.prompter.toprompt(new_clipboard)
                    self.report_new_prompt(pos, neg)
            except Exception as e:
                print(f"Any exception occurred in {threading.current_thread().name}: ", e)
