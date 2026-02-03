"""
対 Master イベント定義
"""

from __future__ import annotations

from dataclasses import dataclass

from archiver.dataclasses import NoImageStats, PicStats
from displayer.dataclasses import GUIConfigs
from generator.dataclasses import TaskBlueprint


@dataclass
class ArchiverEvent:
    next_picstats: PicStats | NoImageStats


@dataclass
class ChangePicStats(ArchiverEvent):
    pass


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


@dataclass
class GeneratorEvent:
    pass


@dataclass
class TaskStart(GeneratorEvent):
    new_task: TaskBlueprint


@dataclass
class TaskComplete(GeneratorEvent):
    pass


@dataclass
class NewProgress(GeneratorEvent):
    progress: float = 0.0


@dataclass
class TaskReserve(GeneratorEvent):
    tasks: int = 0
