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


class SDPngInfo(PngImagePlugin.PngInfo):
    """
    Stable Diffusion 特化の PngInfo
    """

    def __init__(self, infos: dict, idx: int):
        """
        コンストラクタ
        PNG に付与する PNG Info を生成する\n
        info 領域上のデータは "images" で削ぎ落とした時点でなくなるので, 再度の付与を行う\n
        info 領域上のデータは同時生成した画像群に関する配列構造のため, インデックスの指定も必要

        Args:
            infos (dict): info 領域上のデータ
            idx (int): 配列のインデックス
        """
        super().__init__()
        self.add_text("prompt", infos.get("all_prompts", [])[idx])
        self.add_text("negative_prompt", infos.get("all_negative_prompts", [])[idx])
        self.add_text("steps", str(infos.get("steps", 0)))
        self.add_text("sampler", infos.get("sampler_name", ""))
        self.add_text(
            "schedule_type",
            dict(infos.get("extra_generation_params", {})).get("Schedule type", ""),
        )
        self.add_text("cfg_scale", str(infos.get("cfg_scale", 0)))
        self.add_text("seed", str(infos.get("all_seeds", [])[idx]))
        self.add_text("width", str(infos.get("width", 0)))
        self.add_text("height", str(infos.get("height", 0)))
        self.add_text("sd_model_name", infos.get("sd_model_name", ""))
        self.add_text("sd_model_hash", infos.get("sd_model_hash", ""))
        self.add_text("clip_skip", str(infos.get("clip_skip", 0)))
        self.add_text("parameters", infos.get("infotexts", [])[idx])


@dataclass
class PicInfo:
    """
    画像のメタデータ
    """

    prompt: str | None = None
    negative_prompt: str | None = None
    steps: int | None = None
    sampler: str | None = None
    schedule_type: str | None = None
    cfg_scale: float | None = None
    seed: int | None = None
    width: int | None = None
    height: int | None = None
    sd_model_name: str | None = None
    sd_model_hash: str | None = None
    clip_skip: int | None = None
    parameters: str | None = None

    @classmethod
    def make(cls, image: Image):
        """
        コンストラクタ

        Args:
            image (Image): Open して得られる Image インスタンス
        """
        info: dict = image.info
        return cls(
            prompt=info.get("prompt"),
            negative_prompt=info.get("negative_prompt"),
            steps=cls.to_int(info.get("steps")),
            sampler=info.get("sampler"),
            schedule_type=info.get("schedule_type"),
            cfg_scale=cls.to_float(info.get("cfg_scale")),
            seed=cls.to_int(info.get("seed")),
            width=cls.to_int(info.get("width")),
            height=cls.to_int(info.get("height")),
            sd_model_name=info.get("sd_model_name"),
            sd_model_hash=info.get("sd_model_hash"),
            clip_skip=cls.to_int(info.get("clip_skip")),
            parameters=info.get("parameters"),
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
                info = PicInfo.make(image)
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
