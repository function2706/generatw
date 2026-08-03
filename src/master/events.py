"""
対 Master イベント定義
"""

from __future__ import annotations

from dataclasses import dataclass

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
class DetectPicsChanges(ArchiverEvent):
    type: str


@dataclass
class DisplayerEvent:
    pass


@dataclass
class OnSelectCharacter(DisplayerEvent):
    """キャラクター選択"""

    char_id: str


@dataclass
class OnReloadCharacter(DisplayerEvent):
    """選択中キャラクター/アクションの再読み込み"""

    pass


@dataclass
class OnAction(DisplayerEvent):
    """アクション実行 (挨拶/着せ替え/スキンシップ 等)"""

    action_id: str
    wardrobe_key: str | None = None  # kind=wardrobe のアクションで使用


@dataclass
class OnSaveState(DisplayerEvent):
    """内部状態の保存"""

    pass


@dataclass
class OnLoadState(DisplayerEvent):
    """内部状態の復元"""

    pass


@dataclass
class OnResetState(DisplayerEvent):
    """内部状態を初期値へ戻す"""

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
class OnFlushTxt2ImgTasks(DisplayerEvent):
    pass


@dataclass
class OnFlushImg2ImgTasks(DisplayerEvent):
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
