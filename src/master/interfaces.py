"""
共用関数
"""

from __future__ import annotations

import tkinter
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from common.functions import BackEnd, FrontEnd

if TYPE_CHECKING:
    from displayer.dataclasses import GUIConfigs


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
