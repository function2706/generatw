"""
共用関数
"""

from __future__ import annotations

import tkinter
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Protocol

from common.classes import PicStats, TaskBlueprint


class FrontEnd(Enum):
    """
    フロントエンド識別子
    """

    reverse = auto()
    the_world = auto()


class BackEnd(Enum):
    """
    バックエンド識別子
    """

    a1111 = auto()
    comfy_ui = auto()


@dataclass
class CrntGUIConfigs:
    """
    Displayer 外で参照する設定フォーマット
    """

    srv_ipaddr: str = ""
    srv_port: str = ""
    sd_steps: int = 0
    sd_batch_size: int = 0
    sd_width: int = 0
    sd_height: int = 0
    allow_edit_clipboard: bool = False
    print_new_clipboard: bool = False
    print_new_stats: bool = False
    print_images: bool = False
    print_picinfo: bool = False

    @classmethod
    def make(
        cls,
        srv_ipaddr: str,
        srv_port: str,
        sd_steps: int,
        sd_batch_size: int,
        sd_width: int,
        sd_height: int,
        allow_edit_clipboard: bool,
        print_new_clipboard: bool,
        print_new_stats: bool,
        print_images: bool,
        print_picinfo: bool,
    ):
        """
        コンストラクタ

        Args:
            srv_ipaddr (str): ポスト先 IP アドレス
            srv_port (str): ポスト先ポート
            sd_steps (int): ステップ数
            sd_batch_size (int): バッチサイズ
            sd_width (int): 幅
            sd_height (int): 高さ
            allow_edit_clipboard (bool): デバッグ時にクリップボード更新を認めるか
            print_new_clipboard (bool): クリップボードの更新があった場合にログ出力するか
            print_new_stats (bool): ステータスの更新があった場合にログ出力するか
            print_images (bool): 応答 image があった場合にログ出力するか
            print_picinfo (bool): 応答 image の PicInfo をログ出力するか
        """
        return cls(
            srv_ipaddr=srv_ipaddr,
            srv_port=srv_port,
            sd_steps=sd_steps,
            sd_batch_size=sd_batch_size,
            sd_width=sd_width,
            sd_height=sd_height,
            allow_edit_clipboard=allow_edit_clipboard,
            print_new_clipboard=print_new_clipboard,
            print_new_stats=print_new_stats,
            print_images=print_images,
            print_picinfo=print_picinfo,
        )


class MasterIF(Protocol):
    """
    Master インターフェース定義クラス
    """

    root: tkinter.Tk

    @property
    def frontend_name(self) -> str: ...
    @property
    def backend_name(self) -> str: ...
    @property
    def pics_dir_path(self) -> Path: ...
    @property
    def crnt_gui_configs(self) -> CrntGUIConfigs: ...
    @property
    def crnt_picstats(self) -> PicStats: ...
    @property
    def crnt_archiver(self) -> dict[str, Any]: ...
    @property
    def crnt_task(self) -> TaskBlueprint: ...
    @property
    def crnt_tasks(self) -> int: ...
    @property
    def crnt_tasklist(self) -> list[TaskBlueprint]: ...
    @property
    def crnt_progress(self) -> float: ...

    def on_next(self) -> None: ...
    def on_prev(self) -> None: ...
    def on_good(self) -> None: ...
    def on_bad(self) -> None: ...
    def on_debug(self) -> None: ...
    def on_interrupt(self) -> None: ...

    def refresh_piclist(self) -> None: ...
    def clear_tasks(self) -> None: ...
    def reserve_task(self) -> None: ...
