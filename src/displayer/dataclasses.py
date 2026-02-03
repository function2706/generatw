"""
共用クラス
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from archiver.dataclasses import NoImageStats, PicStats
from generator.dataclasses import TaskBlueprint

if TYPE_CHECKING:
    from master.interfaces import MasterIF


@dataclass
class GUIConfigs:
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
    print_picinfo: bool = False
    print_event: bool = False


class DisplayerIF(Protocol):
    master: MasterIF
    last_picstats: PicStats | NoImageStats
    last_task: TaskBlueprint

    @property
    def crnt_configs(self) -> GUIConfigs: ...
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


@dataclass
class DisplayerEvent:
    pass


@dataclass
class OnRepeatTask(DisplayerEvent):
    pass


@dataclass
class OnInterruptTask(DisplayerEvent):
    pass


@dataclass
class OnFlushTasks(DisplayerEvent):
    pass


@dataclass
class OnDebug(DisplayerEvent):
    pass


@dataclass
class OnDumpArchiver(DisplayerEvent):
    pass


@dataclass
class OnDumpTaskList(DisplayerEvent):
    pass


@dataclass
class OnBackward(DisplayerEvent):
    pass


@dataclass
class OnForward(DisplayerEvent):
    pass


@dataclass
class OnUpscale(DisplayerEvent):
    pass


@dataclass
class OnDelete(DisplayerEvent):
    pass


@dataclass
class OnChangeConfig(DisplayerEvent):
    new_config: GUIConfigs
