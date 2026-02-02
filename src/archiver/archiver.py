"""
画像管理クラス
"""

from __future__ import annotations

import os
import random
from collections import deque
from copy import deepcopy
from enum import Enum, auto
from pathlib import Path

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from archiver.dataclasses import NoImageStats, PicArchive, PicStats


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


class Archiver:
    """
    画像管理クラス
    """

    def __init__(self, rootdir: Path):
        """
        コンストラクタ

        Args:
            rootdir (Path): 監視対象ディレクトリ
        """
        self.rootdir = rootdir
        rootdir.mkdir(parents=True, exist_ok=True)
        self.archive = PicArchive(rootdir)
        self.crnt_picstats: PicStats | NoImageStats = None
        self.next_picstats: PicStats | NoImageStats = None

        # pics 監視モジュール
        self.reports: deque[tuple[EventType, Path]] = deque()
        self.observer = Observer()
        self.observer.schedule(PicEventHandler(self.reports), path=str(rootdir), recursive=True)
        self.observer.start()

    def finalize(self):
        """
        終了処理
        """
        self.observer.stop()

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
        self.next_picstats = NoImageStats

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
        self.next_picstats = picstats_list[min(idx + 1, len(picstats_list) - 1)]

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
        self.next_picstats = picstats_list[max(idx - 1, 0)]

    def warp_picstats(self, dir: str) -> None:
        """
        PicStats リストにおいて, そのディレクトリ内のランダムな PicStats に移動する\n
        リストが空の場合は何もしない
        """
        picstats_list = self.archive.get_picstats_list(dir)
        if not picstats_list:
            return

        self.next_picstats = random.choice(picstats_list)

    def remove_crnt_picstats(self) -> None:
        """
        注目中 PicStats にあたる画像を削除する\n
        (リストの更新は process_reports に一任)
        """
        if self.crnt_picstats is None or self.crnt_picstats is NoImageStats:
            return

        os.remove(self.crnt_picstats.path)

    def inherit_picstats(self) -> PicStats:
        """
        移動予定先 PicStats への移動を実施する\n
        移動が予約されていない, あるいは同じものが予約されている場合はなにもしない\n
        それ以外は現在のものと入れ替え予約を解消し, 新しいもののコピーを返す\n
        本関数は tkinter のメインループで, next の予約を行う全関数よりもあとに呼び出すこと
        """
        if self.next_picstats is None or self.next_picstats == self.crnt_picstats:
            return None

        self.crnt_picstats = self.next_picstats
        self.next_picstats = None
        return self.crnt_picstats_copy

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
                        self.next_picstats = NoImageStats
            elif eventtype == EventType.moved:
                print("T.B.D.")

    @property
    def crnt_picstats_copy(self) -> PicStats | NoImageStats:
        """
        注目中 PicStats のコピーを渡す

        Returns:
            PicStats | NoImageStats: 注目中 PicStats のコピー
        """
        return deepcopy(self.crnt_picstats)
