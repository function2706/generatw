"""
画像管理クラス
"""

from __future__ import annotations

import os
import random
from collections import deque
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

import master.events
from archiver.dataclasses import NoImageStats, PicStats
from common.functions import BottleMail, PathConsts


class EventType(Enum):
    created = auto()
    deleted = auto()
    moved = auto()


class PicEventHandler(PatternMatchingEventHandler):
    """
    画像ファイルの WatchDog\n
    PNG のみ監視対象
    """

    def __init__(self, reports: deque[tuple[EventType, Path]]):
        """
        コンストラクタ
        """
        super().__init__(patterns=["*.png", "*.PNG"], ignore_directories=True, case_sensitive=False)
        self.reports = reports

    def on_created(self, event):
        """
        ファイル作成時のイベントハンドラ

        Args:
            event (_type_): イベント
        """
        self.reports.append((EventType.created, Path(event.src_path)))

    def on_deleted(self, event):
        """
        ファイル削除時のイベントハンドラ

        Args:
            event (_type_): イベント
        """
        self.reports.append((EventType.deleted, Path(event.src_path)))

    def on_moved(self, event):
        """
        ファイル移動/変更時のイベントハンドラ\n
        内容変更には非対応

        Args:
            event (_type_): イベント
        """
        print(f"Event: {event.event_type}, Path: {event.src_path} -> {event.dest_path}")


@dataclass
class PicArchive:
    """
    現在の注目画像と, 画像リストのセット\n
    画像は PicStats として保存される
    """

    piclist: list[dict[str, list[PicStats]]] = field(default_factory=list)

    def __post_init__(self):
        """
        コンストラクタ後に監視対象ディレクトリのリストを作成する
        """
        self.refresh_piclist()

    def refresh_piclist(self) -> None:
        """
        監視対象ディレクトリ内の画像ファイルを PicStats の形で再帰的にリスト化する
        """
        self.piclist = []
        for dirpath, _, filenames in os.walk(PathConsts.pic_dir):
            picstats: list[PicStats] = []
            for filename in filenames:
                if filename.lower().endswith(".png"):
                    path = Path(dirpath) / filename
                    picstats.append(PicStats.make(path))
            if picstats:
                dirname = Path(dirpath).name
                self.piclist.append({dirname: picstats})

    def add(self, path: Path) -> None:
        """
        指定の PicStats をリストに追加する\n
        追加先ディレクトリは PicStats の dir をもとに判断し,\n
        そのディレクトリを持つ dict の list に追加する\n
        もしそのディレクトリがない場合は新たに作成し, そこに追加する

        Args:
            picstats (PicStats): PicStats
        """
        picstats = PicStats.make(path, retry=5, cooldown=0.1)
        dir = picstats.dir
        for item in self.piclist:
            if dir in item:
                item[dir].append(picstats)
                return

        # ディレクトリが存在しない
        self.piclist.append({dir: [picstats]})

    def remove(self, path: Path) -> None:
        """
        指定の PicStats とパスが一致する PicStats をリストから削除する\n
        削除の結果 list が空になった場合, その dict も削除する

        Args:
            picstats (PicStats): PicStats
        """
        dir = path.parent.name
        for i, item in enumerate(self.piclist):
            if dir not in item:
                continue

            picstats_list = item[dir]
            for j, pstats in enumerate(picstats_list):
                if pstats.path == path:
                    picstats_list.pop(j)
                    break

            # もし画像リストが空になった際はその辞書ごとリストから削除
            if not picstats_list:
                self.piclist.pop(i)
            break

    def get_picstats_list(self, dirname: str) -> list[PicStats]:
        """
        監視対象ディレクトリ内で指定のディレクトリ名に紐づく PicStats リストを取得する\n
        存在しない場合は空リストを返す

        Args:
            dirname (str): ディレクトリ名

        Returns:
            list[PicStats]: PicStats リスト
        """
        return next((d[dirname] for d in self.piclist if dirname in d), [])

    def todict(self) -> dict[str, Any]:
        """
        dict への変換

        Returns:
            dict[str, Any]: dict インスタンス
        """
        return asdict(self)


class Archiver:
    """
    画像管理クラス
    """

    def __init__(self, to_master: BottleMail[master.events.ArchiverEvent]):
        """
        コンストラクタ
        """
        PathConsts.pic_dir.mkdir(parents=True, exist_ok=True)
        self.archive = PicArchive()
        self.crnt_picstats: PicStats | NoImageStats = None
        self.to_master = to_master

        # pics 監視モジュール
        self.reports: deque[tuple[EventType, Path]] = deque()
        self.observer = Observer()
        self.observer.schedule(
            PicEventHandler(self.reports), path=str(PathConsts.pic_dir), recursive=True
        )
        self.observer.start()

    def finalize(self):
        """
        終了処理
        """
        self.observer.stop()

    @property
    def crnt_picstats_copy(self) -> PicStats | NoImageStats:
        """
        注目中 PicStats のコピーを渡す

        Returns:
            PicStats | NoImageStats: 注目中 PicStats のコピー
        """
        return deepcopy(self.crnt_picstats)

    def count_files_in(self, dirname: str) -> int:
        """
        指定のディレクトリ下のファイル数を取得する

        Args:
            dirname (str): ディレクトリ

        Returns:
            int: ファイル数
        """
        return len(self.archive.get_picstats_list(dirname))

    def drop_picstats(self) -> None:
        """
        注目中 PicStats を解除する
        """
        self.crnt_picstats = NoImageStats
        self.to_master.enclose(master.events.NewPicStats(self.crnt_picstats))

    def forward_picstats(self) -> None:
        """
        PicStats リストにおいて, 注目中 PicStats の次のものに移動する\n
        末尾を注目中である場合は移動しない\n
        注目していない場合, リストが空の場合は何もしない
        """
        if self.crnt_picstats is None or self.crnt_picstats is NoImageStats:
            return

        picstats_list = self.archive.get_picstats_list(self.crnt_picstats.dir)
        if not picstats_list:
            return

        idx = picstats_list.index(self.crnt_picstats)
        self.crnt_picstats = picstats_list[min(idx + 1, len(picstats_list) - 1)]
        self.to_master.enclose(master.events.NewPicStats(self.crnt_picstats))

    def backward_picstats(self) -> None:
        """
        PicStats リストにおいて, 注目中 PicStats の前のものに移動する\n
        末尾を注目中である場合は移動しない\n
        注目していない場合, リストが空の場合は何もしない
        """
        if self.crnt_picstats is None or self.crnt_picstats is NoImageStats:
            return

        picstats_list = self.archive.get_picstats_list(self.crnt_picstats.dir)
        if not picstats_list:
            return

        idx = picstats_list.index(self.crnt_picstats)
        self.crnt_picstats = picstats_list[max(idx - 1, 0)]
        self.to_master.enclose(master.events.NewPicStats(self.crnt_picstats))

    def warp_picstats(self, dir: str) -> None:
        """
        PicStats リストにおいて, そのディレクトリ内のランダムな PicStats に移動する\n
        リストが空の場合は何もしない
        """
        picstats_list = self.archive.get_picstats_list(dir)
        if not picstats_list:
            return

        self.crnt_picstats = random.choice(picstats_list)
        self.to_master.enclose(master.events.NewPicStats(self.crnt_picstats))

    def remove_crnt_picstats(self) -> None:
        """
        注目中 PicStats にあたる画像を削除する\n
        (リストの更新は process_reports に一任)
        """
        if self.crnt_picstats is None or self.crnt_picstats is NoImageStats:
            return

        os.remove(self.crnt_picstats.path)

    def process_reports(self) -> None:
        """
        WatchDog からの報告を順に処理する\n
        イベントごとの処理の詳細はコメントの通り\n
        本関数は tkinter のメインループで呼び出すこと
        """
        while True:
            try:
                eventtype, path = self.reports.popleft()
            except IndexError:
                # これ以上キュー内にイベントがない
                break

            if eventtype == EventType.created:
                # 追加: リストにも追加
                self.archive.add(path)
            elif eventtype == EventType.deleted:
                # 削除: リストからも削除, さらにまだ注目中なら他へ移す
                # もしディレクトリが空ならこれも削除し, まだ注目中なら注目を解除する
                self.archive.remove(path)
                if self.count_files_in(path.parent.name) > 0:
                    if self.crnt_picstats.path == path:
                        self.warp_picstats(self.crnt_picstats.dir)
                else:
                    os.rmdir(path.parent)
                    if self.crnt_picstats.path == path:
                        self.drop_picstats()
            elif eventtype == EventType.moved:
                print("T.B.D.")
