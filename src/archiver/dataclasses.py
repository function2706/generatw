"""
共用クラス
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image, PngImagePlugin


@dataclass
class PicInfo:
    """
    画像のメタデータ
    """

    positive_prompt: str = ""
    negative_prompt: str = ""
    steps: int = 0
    sampler: str = ""
    scheduler: str = ""
    cfg_scale: float = 0.0
    seed: int = 0
    width: int = 0
    height: int = 0
    model_name: str = ""
    model_hash: str = ""
    clip_skip: int = 0

    @classmethod
    def make(
        cls,
        positive_prompt: str,
        negative_prompt: str,
        steps: str,
        sampler: str,
        scheduler: str,
        cfg_scale: str,
        seed: str,
        width: str,
        height: str,
        model_name: str,
        model_hash: str,
        clip_skip: str,
    ):
        return cls(
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            steps=steps,
            sampler=sampler,
            scheduler=scheduler,
            cfg_scale=cfg_scale,
            seed=seed,
            width=width,
            height=height,
            model_name=model_name,
            model_hash=model_hash,
            clip_skip=clip_skip,
        )

    @classmethod
    def fromimage(cls, image: Image):
        """
        コンストラクタ\n
        tEXt フィールドからセットする

        Args:
            image (Image): Open して得られる Image インスタンス
        """
        info: dict = image.info
        return cls(
            positive_prompt=info.get("positive_prompt"),
            negative_prompt=info.get("negative_prompt"),
            steps=cls.to_int(info.get("steps")),
            sampler=info.get("sampler"),
            scheduler=info.get("scheduler"),
            cfg_scale=cls.to_float(info.get("cfg_scale")),
            seed=cls.to_int(info.get("seed")),
            width=cls.to_int(info.get("width")),
            height=cls.to_int(info.get("height")),
            model_name=info.get("model_name"),
            model_hash=info.get("model_hash"),
            clip_skip=cls.to_int(info.get("clip_skip")),
        )

    @staticmethod
    def to_int(v):
        return int(v) if v is not None else None

    @staticmethod
    def to_float(v):
        return float(v) if v is not None else None

    def todict(self) -> dict[str, Any]:
        """
        dict への変換

        Returns:
            dict[str, Any]: dict インスタンス
        """
        return asdict(self)

    def topnginfo(self) -> PngImagePlugin.PngInfo:
        """
        topnginfo PngInfo への変換

        Returns:
            PngImagePlugin.PngInfo: PngInfo
        """
        info = PngImagePlugin.PngInfo()
        info.add_text("positive_prompt", self.positive_prompt)
        info.add_text("negative_prompt", self.negative_prompt)
        info.add_text("steps", str(self.steps))
        info.add_text("sampler", self.sampler)
        info.add_text("scheduler", self.scheduler)
        info.add_text("cfg_scale", str(self.cfg_scale))
        info.add_text("seed", str(self.seed))
        info.add_text("width", str(self.width))
        info.add_text("height", str(self.height))
        info.add_text("model_name", self.model_name)
        info.add_text("model_hash", self.model_hash)
        info.add_text("clip_skip", str(self.clip_skip))
        return info


@dataclass
class PicStats:
    """
    画像情報 (パス, ディレクトリ名, ファイル名, メタデータ)
    """

    path: Path
    dir: str | None = None
    name: str | None = None
    info: PicInfo | None = None

    @classmethod
    def make(cls, path: Path, retry: int = 0, cooldown: float = 0.0):
        """
        コンストラクタ

        Args:
            path (Path): 画像のパス
        """
        dir_name = path.parent.name
        file_name = path.name

        info = None

        # 最大5回リトライ（書き込み完了を待つ）
        for _ in range(retry + 1):
            try:
                with Image.open(path) as image:
                    # 画像を実際に少し読み込んでみて壊れていないか確認
                    image.verify()
                with Image.open(path) as image:
                    # verifyの後は一旦閉じ直す必要がある
                    info = PicInfo.fromimage(image)
                    break
            except Exception:
                time.sleep(cooldown)
                continue
        else:
            print(f"Error PicStats {path}: Giving up after retries.")

        return cls(path=path, dir=dir_name, name=file_name, info=info)

    def todict(self) -> dict[str, Any]:
        """
        dict への変換

        Returns:
            dict[str, Any]: dict インスタンス
        """
        return asdict(self)


@dataclass
class PicArchive:
    """
    現在の注目画像と, 画像リストのセット\n
    画像は PicStats として保存される
    """

    rootdir: Path | None = None
    piclist: list[dict[str, list[PicStats]]] = field(default_factory=list)

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
