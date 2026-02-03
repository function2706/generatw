"""
クリップボード監視, ステータス記録クラス
"""

from __future__ import annotations

import copy
import random
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generic, Mapping, Protocol, TypeVar

import pyperclip

from common.functions import BottleMail, dirname_by_prompts, dump_json
from master.events import NewClipStats, ParserEvent
from master.interfaces import MasterIF


@dataclass(frozen=True)
class Consts:
    """
    このクラス関連の定数
    """

    thread_interval_sec = 0.1

    # 画像保存先ディレクトリ
    pichome_dir: str = "pics"
    # デバッグ用キャラクター名の部分文字列
    charaname_substr_debug: str = "DebuggingPM"


@dataclass
class Event:
    """
    イベントフラグ
    """

    shutdown: threading.Event = field(default_factory=threading.Event)  # 終了予定


class HasCommonMembers(Protocol):
    """
    Generic な Stats が 共通メンバを持つことを伝えるためのクラス
    """

    # var: int <- ここで共通メンバ変数の存在を通告することもできる

    def refresh(self) -> None: ...
    def todict(self) -> dict[str, Any]: ...


Stats = TypeVar("Stats", bound=HasCommonMembers)


class Parser(ABC, Generic[Stats]):
    """
    クリップボード監視, ステータス記録クラス
    """

    @property
    @abstractmethod
    def chara_tbl(self) -> Mapping[str, str]:
        """
        キャラクタプロンプトテーブル\n
        キャラクタ名と対応するプロンプトの定義

        Returns:
            Mapping[str, str]: テーブル
        """
        raise NotImplementedError

    def __init__(self, master: MasterIF, to_master: BottleMail[ParserEvent], stats: Stats):
        """
        コンストラクタ

        Args:
            master (MasterIF): Master インターフェース
            to_master (BottleMail[ParserEvent]): 対 Master IPC
            stats (Stats): Stats インスタンス
            ※TypeVar ではないインスタンスを渡さないとメソッドにアクセスできない
              そしてその型は派生先しか知らないので, そこから渡してもらう
        """
        self.master = master
        self.to_master = to_master

        self.crnt_clipboard = ""
        self.crnt_clipstats: Stats = stats

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

    def whoami(self) -> str:
        """
        自身のフロントエンド名を取得する

        Returns:
            str: フロントエンド名
        """
        return self.__class__.__name__.replace("Parser", "")

    def pics_dir_path(self) -> Path:
        """
        画像ディレクトリパスを取得する\n
        (pics/<クラス名>)

        Returns:
            Path: ディレクトリパス
        """
        return Path(Consts.pichome_dir) / Path(self.whoami())

    @abstractmethod
    def make_dummy_stats(self, name: str = None) -> Stats:
        """
        ダミーステータスを生成する(デバッグ用)\n
        データはモードに即して定義される

        Args:
            name (str, optional): name フィールドに代入する文字列, None でない場合はこの値で初期化

        Returns:
            Stats: ダミーステータス
        """
        pass

    def ready_for_debug(self) -> bool:
        """
        クリップボードの編集が許可されている場合はダミークリップボードを設定する\n
        そうでない場合はダミーステータスのみを編集し, メイン処理に委ねる

        Returns:
            bool: メイン処理の反映が必要なら True, そうでない場合は False
        """
        if self.master.crnt_gui_configs.allow_edit_clipboard:
            pyperclip.copy(Consts.charaname_substr_debug + str(random.randint(1, 8)))
            return False

        new_stats = self.make_dummy_stats()
        if new_stats is None or new_stats == self.crnt_clipstats:
            return False

        self.crnt_clipstats = new_stats
        if self.master.crnt_gui_configs.print_new_stats:
            dump_json(self.crnt_clipstats.todict(), "new_stats(debug)")

        return True

    def parse_clipboard(self) -> Stats | None:
        """
        クリップボードを監視し, 記録中文字列と異なる場合に記録した後,\n
        クリップボード文字列をもとに各ステータスを取得する

        Returns:
            Stats: 新たなステータス, 更新がない場合やエラー時に None
        """
        try:
            new_clipboard = pyperclip.paste()
        except Exception as e:
            print("An exception occur for watching clipboard.", e)
            return None

        if self.crnt_clipboard == new_clipboard:
            return None

        if self.master.crnt_gui_configs.print_new_clipboard:
            print("new_clipboard:")
            print(new_clipboard)

        self.crnt_clipboard = new_clipboard

        if Consts.charaname_substr_debug in self.crnt_clipboard:
            # クリップボードの編集が許可されている場合のデバッグ経路
            return self.make_dummy_stats(name=self.crnt_clipboard)

        new_stats = copy.deepcopy(self.crnt_clipstats)
        new_stats.refresh(self.crnt_clipboard)
        return new_stats

    def refresh_stats(self) -> bool:
        """
        記録中クリップボード文字列をもとにステータスを更新する\n
        前回のステータスと同じかどうかの判断も行う

        Returns:
            bool: True: ステータス更新あり, False: 更新なし
        """

        new_stats = self.parse_clipboard()
        if new_stats is None or new_stats == self.crnt_clipstats:
            return False

        self.crnt_clipstats = new_stats
        if self.master.crnt_gui_configs.print_new_stats:
            dump_json(self.crnt_clipstats.todict(), "new_stats")
        return True

    @abstractmethod
    def is_stats_enough_for_prompt(self) -> bool:
        """
        記録中ステータスがプロンプト生成に際し十分な情報を有しているか

        Returns:
            bool: True: 有している, False: 有していない
        """
        pass

    @abstractmethod
    def make_pos_prompt(self) -> str:
        """
        記録中ステータスからポジティブプロンプトを生成する

        Returns:
            str: プロンプト
        """
        pass

    @abstractmethod
    def make_neg_prompt(self) -> str:
        """
        記録中ステータスからネガティブプロンプトを生成する

        Returns:
            str: プロンプト
        """
        pass

    def get_crnt_stats_dir(self) -> str:
        """
        記録中ステータスに適合するディレクトリ名を返す

        Returns:
            str: ディレクトリ名
        """
        return dirname_by_prompts(self.make_pos_prompt(), self.make_neg_prompt())

    def parser(self) -> None:
        """
        クリップボード監視を行う
        """
        while not self.event.shutdown.is_set():
            time.sleep(Consts.thread_interval_sec)
            try:
                if not self.refresh_stats():
                    continue
                self.to_master.enclose(NewClipStats(is_enough=self.is_stats_enough_for_prompt()))
            except Exception as e:
                raise
                print(f"Any exception occurred in {threading.current_thread().name}: ", e)
