"""
共用クラス
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from PIL import Image, PngImagePlugin


@dataclass(frozen=True)
class PMConsts:
    """
    このクラス関連の定数
    """

    # 画像保存先ディレクトリ
    pichome_dir: str = "pics"
    # デバッグ用キャラクター名の部分文字列
    charaname_substr_debug: str = "DebuggingPM"


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
        info.add_text("prompt", self.positive_prompt)
        info.add_text("negative_prompt", self.negative_prompt)
        info.add_text("steps", str(self.steps))
        info.add_text("sampler", self.sampler)
        info.add_text("schedule_type", self.scheduler)
        info.add_text("cfg_scale", str(self.cfg_scale))
        info.add_text("seed", str(self.seed))
        info.add_text("width", str(self.width))
        info.add_text("height", str(self.height))
        info.add_text("sd_model_name", self.model_name)
        info.add_text("sd_model_hash", self.model_hash)
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
    def make(cls, path: Path):
        """
        コンストラクタ

        Args:
            path (Path): 画像のパス
        """
        dir_name = path.parent.name
        file_name = path.name

        try:
            with Image.open(path) as image:
                info = PicInfo.fromimage(image)
        except Exception as e:
            print(f"Error PicStats {path}: {e}")
            info = None

        return cls(
            path=path,
            dir=dir_name,
            name=file_name,
            info=info,
        )

    def todict(self) -> dict[str, Any]:
        """
        dict への変換

        Returns:
            dict[str, Any]: dict インスタンス
        """
        return asdict(self)


@dataclass
class TaskBlueprint:
    """
    タスクの設計図\n
    プロンプトの組, 生成キュー用に使用する\n
    インスタンス化した際, その時点のプロンプトを記録中ステータスから生成し, セットする
    """

    prompt: str = ""
    negative_prompt: str = ""
    steps: int = 0
    batch_size: int = 0
    sampler_name: str = "DPM++ 2S a"
    scheduler: str = "Karras"
    cfg_scale: float = 7.0
    seed: int = -1
    width: int = 0
    height: int = 0

    dst_addr: str = ""
    dst_port: str = ""

    @classmethod
    def make(
        cls, pos: str, neg: str, stps: int, b_size: int, w: int, h: int, d_addr: str, d_port: str
    ):
        """
        コンストラクタ

        Args:
            pos (str): ポジティブプロンプト
            neg (str): ネガティブプロンプト
            stps (int): ステップ数
            b_size (int): バッチサイズ
            w (int): 幅
            h (int): 高さ
            d_addr (str): 宛先アドレス
            d_port (str): 宛先ポート
        """
        return cls(
            prompt=pos,
            negative_prompt=neg,
            steps=stps,
            batch_size=b_size,
            width=w,
            height=h,
            dst_addr=d_addr,
            dst_port=d_port,
        )

    def todict(self) -> dict[str, Any]:
        """
        dict への変換

        Returns:
            dict[str, Any]: dict インスタンス
        """
        return asdict(self)
