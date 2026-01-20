"""
画像管理クラス, 及びこれが包含するサブクラス群
"""

from __future__ import annotations

import os
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from common.classes import PicStats


@dataclass
class Archiver:
    """
    画像監視クラス
    """

    rootdir: Path | None = None
    piclist: list[dict[str, list[PicStats]]] = field(default_factory=list)
    crnt_picstats: PicStats | None = None

    @classmethod
    def make(cls, rootdir: Path):
        """
        コンストラクタ\n
        piclist は ディレクトリ名とそのディレクトリに属するファイル名群を各成分とするリスト\n
        注目中の画像を PicStats の形で記憶する(専ら表示中と同義)

        Args:
            rootdir (Path): 監視対象ディレクトリ
        """
        self = cls(rootdir=rootdir)
        self.refresh_piclist()
        return self

    def refresh_piclist(self) -> None:
        """
        監視対象ディレクトリ内の画像ファイルを PicStats の形で再帰的にリスト化する
        """
        self.piclist = []
        for dirpath, _, filenames in os.walk(self.rootdir):
            picstats: list[PicStats] = []
            for filename in filenames:
                if filename.lower().endswith(".png"):
                    path = Path(dirpath) / filename
                    picstats.append(PicStats.make(path))
            if picstats:
                dirname = Path(dirpath).name
                self.piclist.append({dirname: picstats})

    def get_picstats_list(self, dirname: str) -> list[PicStats]:
        """
        監視対象ディレクトリ内で指定のディレクトリ名に紐づく PicStats リストを取得する\n
        存在しない場合は空リストを返す

        Args:
            dirname (str): ディレクトリ名

        Returns:
            list[PicStats]: PicStats リスト
        """
        for d in self.piclist:
            if dirname in d:
                return d[dirname]
        return []

    def next_picstats(self) -> None:
        """
        PicStats リストにおいて, 注目中 PicStats の次のものに移動する\n
        末尾を注目中である場合は移動しない\n
        注目していない場合, リストが空の場合は何もしない
        """
        if self.crnt_picstats is None:
            return

        picstats_list = self.get_picstats_list(self.crnt_picstats.dir)
        if not picstats_list:
            return

        idx = picstats_list.index(self.crnt_picstats)
        self.crnt_picstats = picstats_list[min(idx + 1, len(picstats_list) - 1)]

    def prev_picstats(self) -> None:
        """
        PicStats リストにおいて, 注目中 PicStats の前のものに移動する\n
        末尾を注目中である場合は移動しない\n
        注目していない場合, リストが空の場合は何もしない
        """
        if self.crnt_picstats is None:
            return

        picstats_list = self.get_picstats_list(self.crnt_picstats.dir)
        if not picstats_list:
            return

        idx = picstats_list.index(self.crnt_picstats)
        self.crnt_picstats = picstats_list[max(idx - 1, 0)]

    def warp_picstats(self, dir: str) -> None:
        """
        PicStats リストにおいて, そのディレクトリ内のランダムな PicStats に移動する\n
        リストが空の場合は何もしない
        """
        picstats_list = self.get_picstats_list(dir)
        if not picstats_list:
            return

        self.crnt_picstats = random.choice(picstats_list)

    def remove_crnt_picstats(self) -> None:
        """
        注目中 PicStats にあたる画像を削除し, リストも更新する(該当 PicStats が削除される)\n
        最後の 1 枚であった場合はディレクトリも削除し, 注目を解除する\n
        ※ディレクトリのみが存在するという状況が仕様上あってはならないので, これらの処理を分けない\n
        注目中 PicStats が None の場合はなにもしない
        """
        if self.crnt_picstats is None:
            return

        os.remove(self.crnt_picstats.path)
        self.refresh_piclist()
        if not self.get_picstats_list(self.crnt_picstats.dir):
            os.rmdir(self.rootdir / Path(self.crnt_picstats.dir))
            self.crnt_picstats = None

        self.refresh_piclist()

    def todict(self) -> dict[str, Any]:
        """
        dict への変換

        Returns:
            dict[str, Any]: dict インスタンス
        """
        return asdict(self)
