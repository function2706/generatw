"""
共用関数
"""

from __future__ import annotations

import tkinter
from enum import Enum, auto
from pathlib import Path
from typing import Any, Protocol

from common.classes import GUIConfigs, PicStats, TaskBlueprint


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


class MasterIF(Protocol):
    """
    Master インターフェース定義クラス
    """

    root: tkinter.Tk

    @property
    def frontend_type(self) -> FrontEnd: ...
    @property
    def frontend_name(self) -> str: ...
    @property
    def backend_type(self) -> BackEnd: ...
    @property
    def backend_name(self) -> str: ...
    @property
    def pics_dir_path(self) -> Path: ...
    @property
    def crnt_gui_configs(self) -> GUIConfigs: ...
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
    def on_upscale(self) -> None: ...
    def on_remove(self) -> None: ...
    def on_debug(self) -> None: ...
    def on_interrupt(self) -> None: ...

    def refresh_piclist(self) -> None: ...
    def clear_tasks(self) -> None: ...
    def reserve_task(self) -> None: ...


class DisplayerIF(Protocol):
    master: MasterIF

    @property
    def config_window_x(self) -> int: ...
    @property
    def config_window_y(self) -> int: ...
    @property
    def config_window_width(self) -> int: ...
    @property
    def config_window_height(self) -> int: ...
