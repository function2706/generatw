"""
共用関数
"""

from __future__ import annotations

import tkinter
from pathlib import Path
from typing import Protocol

from archiver.dataclasses import NoImageStats, PicStats
from common.functions import BackEnd, FrontEnd
from displayer.dataclasses import GUIConfigs
from generator.dataclasses import TaskBlueprint


class MasterIF(Protocol):
    """
    Master インターフェース定義クラス
    """

    root: tkinter.Tk
    after_id: str

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
    def crnt_progress(self) -> float: ...


class DisplayerIF(Protocol):
    master: MasterIF
    crnt_config: GUIConfigs
    last_picstats: PicStats | NoImageStats
    last_task: TaskBlueprint

    @property
    def config_window_x(self) -> int: ...
    @property
    def config_window_y(self) -> int: ...
    @property
    def config_window_width(self) -> int: ...
    @property
    def config_window_height(self) -> int: ...

    def on_backward(self) -> None: ...
    def on_forward(self) -> None: ...
    def on_upscale(self) -> None: ...
    def on_delete(self) -> None: ...
