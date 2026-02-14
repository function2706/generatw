"""
対 Master イベント定義
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from archiver.dataclasses import NoImageStats, PicStats
from common.functions import BackEnd
from displayer.dataclasses import GUIConfigs
from generator.dataclasses import TaskBlueprint


@dataclass
class ArchiverEvent:
    pass


@dataclass
class NewPicStats(ArchiverEvent):
    next_picstats: PicStats | NoImageStats


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
class OnSelectYaml(DisplayerEvent):
    path: Path


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
class OnSwitchBackend(DisplayerEvent):
    new_backend: BackEnd


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
class ChangeTasks(GeneratorEvent):
    tasks: int = 0


@dataclass
class ParserEvent:
    pass


@dataclass
class NewPrompts(ParserEvent):
    positive: str
    negative: str
