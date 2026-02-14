"""
共用クラス
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
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
    ancestor: str = ""

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
            ancestor=info.get("ancestor"),
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
        info.add_text("ancestor", self.ancestor)
        return info


@dataclass
class PicStats:
    """
    画像情報 (パス, ディレクトリ名, ファイル名, メタデータ)
    """

    path: Path | None
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


class NoImageStats:
    """
    PicStats が存在しないことを明示する専用オブジェクト
    """

    pass
