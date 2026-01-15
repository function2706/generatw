"""
画像管理クラス, 及びこれが包含するサブクラス群
"""

from __future__ import annotations

import os
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image, PngImagePlugin


class SDPngInfo(PngImagePlugin.PngInfo):
    """
    Stable Diffusion 特化の PngInfo
    """

    def __init__(self, infos: Dict, idx: int):
        """
        コンストラクタ
        PNG に付与する PNG Info を生成する\n
        info 領域上のデータは "images" で削ぎ落とした時点でなくなるので, 再度の付与を行う\n
        info 領域上のデータは同時生成した画像群に関する配列構造のため, インデックスの指定も必要

        Args:
            infos (Dict): info 領域上のデータ
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

    prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    steps: Optional[int] = None
    sampler: Optional[str] = None
    schedule_type: Optional[str] = None
    cfg_scale: Optional[float] = None
    seed: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    sd_model_name: Optional[str] = None
    sd_model_hash: Optional[str] = None
    clip_skip: Optional[int] = None
    parameters: Optional[str] = None

    @classmethod
    def make(cls, image: Image):
        """
        コンストラクタ

        Args:
            image (Image): Open して得られる Image インスタンス
        """
        info: Dict = image.info
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

    def todict(self) -> Dict[str, Any]:
        """
        Dict への変換

        Returns:
            Dict[str, Any]: Dict インスタンス
        """
        return asdict(self)


@dataclass
class PicStats:
    """
    画像情報 (パス, ディレクトリ名, ファイル名, メタデータ)
    """

    path: Path
    dir: Optional[str] = None
    name: Optional[str] = None
    info: Optional[PicInfo] = None

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

    def todict(self) -> Dict[str, Any]:
        """
        Dict への変換

        Returns:
            Dict[str, Any]: Dict インスタンス
        """
        return asdict(self)


@dataclass
class PicManager:
    """
    画像監視クラス
    """

    rootdir: Optional[Path] = None
    piclist: List[Dict[str, List[PicStats]]] = field(default_factory=list)
    crnt_picstats: Optional[PicStats] = None

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
            picstats: List[PicStats] = []
            for filename in filenames:
                if filename.lower().endswith(".png"):
                    path = Path(dirpath) / filename
                    picstats.append(PicStats.make(path))
            if picstats:
                dirname = Path(dirpath).name
                self.piclist.append({dirname: picstats})

    def get_picstats_list(self, dirname: str) -> List[PicStats]:
        """
        監視対象ディレクトリ内で指定のディレクトリ名に紐づく PicStats リストを取得する\n
        存在しない場合は空リストを返す

        Args:
            dirname (str): ディレクトリ名

        Returns:
            List[PicStats]: PicStats リスト
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

    def sweep_emptydir(self) -> None:
        pass

    def todict(self) -> Dict[str, Any]:
        """
        Dict への変換

        Returns:
            Dict[str, Any]: Dict インスタンス
        """
        return asdict(self)
