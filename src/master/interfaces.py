"""
共用関数
"""

from __future__ import annotations

import tkinter
from pathlib import Path
from typing import Protocol

from common.functions import BackEnd
from displayer.dataclasses import GUIConfigs


class MasterIF(Protocol):
    """
    Master インターフェース定義クラス
    """

    root: tkinter.Tk
    after_id: str

    @property
    def backend_type(self) -> BackEnd: ...
    @property
    def backend_name(self) -> str: ...
    @property
    def pics_yaml_dir(self) -> Path: ...
    @property
    def crnt_gui_configs(self) -> GUIConfigs: ...
    @property
    def crnt_progress(self) -> float: ...
