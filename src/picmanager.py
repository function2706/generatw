"""
画像管理クラス, 及びこれが包含するサブクラス群
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image, PngImagePlugin


class SDPngInfo(PngImagePlugin.PngInfo):
    """
    Stable Diffusion 特化の PngInfo
    """

    def __init__(self, infos: Any, idx: int):
        """
        コンストラクタ
        PNG に付与する PNG Info を生成する\n
        info 領域上のデータは "images" で削ぎ落とした時点でなくなるので, 再度の付与を行う\n
        info 領域上のデータは同時生成した画像群に関する配列構造のため, インデックスの指定も必要

        Args:
            infos (Any): info 領域上のデータ
            idx (int): 配列のインデックス
        """
        super().__init__()
        self.add_text("prompt", infos.get("all_prompts", [])[idx])
        self.add_text("negative_prompt", infos.get("all_negative_prompts", [])[idx])
        self.add_text("steps", str(infos.get("steps", 0)))
        self.add_text("sampler", infos.get("sampler_name", ""))
        self.add_text(
            "schedule_type",
            infos.get("extra_generation_params", {}).get("Schedule type", ""),
        )
        self.add_text("cfg_scale", str(infos.get("cfg_scale", 0)))
        self.add_text("seed", str(infos.get("all_seeds", [])[idx]))
        self.add_text("width", str(infos.get("width", 0)))
        self.add_text("height", str(infos.get("height", 0)))
        self.add_text("sd_model_name", infos.get("sd_model_name", ""))
        self.add_text("sd_model_hash", infos.get("sd_model_hash", ""))
        self.add_text("clip_skip", str(infos.get("clip_skip", 0)))
        self.add_text("parameters", infos.get("infotexts", [])[idx])


class PicInfo:
    """
    画像のメタデータ
    """

    def __init__(self, image: Image):
        """
        コンストラクタ

        Args:
            image (Image): Open して得られる Image インスタンス
        """
        self.prompt = image.info.get("prompt")
        self.negative_prompt = image.info.get("negative_prompt")
        self.steps = int(image.info.get("steps"))
        self.sampler = image.info.get("sampler")
        self.schedule_type = image.info.get("schedule_type")
        self.cfg_scale = float(image.info.get("cfg_scale"))
        self.seed = int(image.info.get("seed"))
        self.width = int(image.info.get("width"))
        self.height = int(image.info.get("height"))
        self.sd_model_name = image.info.get("sd_model_name")
        self.sd_model_hash = image.info.get("sd_model_hash")
        self.clip_skip = int(image.info.get("clip_skip"))
        self.parameters = image.info.get("parameters")

    def __eq__(self, other: PicInfo):
        """
        各値が指定の PicInfo のものと等しいか

        Args:
            other (PicInfo): 比較対象

        Returns:
            _type_: True: 等しい, False: 等しくない
        """
        return (
            isinstance(other, PicInfo)
            and self.prompt == other.prompt
            and self.negative_prompt == other.negative_prompt
            and self.steps == other.steps
            and self.sampler == other.sampler
            and self.schedule_type == other.schedule_type
            and self.cfg_scale == other.cfg_scale
            and self.seed == other.seed
            and self.width == other.width
            and self.height == other.height
            and self.sd_model_name == other.sd_model_name
            and self.sd_model_hash == other.sd_model_hash
            and self.clip_skip == other.clip_skip
            and self.parameters == other.parameters
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        このクラスを Dict[str, Any] に変形する

        Returns:
            Dict[str, Any]: 変形後インスタンス
        """
        dict = {}
        dict["prompt"] = self.prompt
        dict["negative_prompt"] = self.negative_prompt
        dict["steps"] = self.steps
        dict["sampler"] = self.sampler
        dict["schedule_type"] = self.schedule_type
        dict["cfg_scale"] = self.cfg_scale
        dict["seed"] = self.seed
        dict["width"] = self.width
        dict["height"] = self.height
        dict["sd_model_name"] = self.sd_model_name
        dict["sd_model_hash"] = self.sd_model_hash
        dict["clip_skip"] = self.clip_skip
        dict["parameters"] = self.parameters
        return dict


class PicStats:
    """
    画像情報 (パス, ディレクトリ名, ファイル名, メタデータ)
    """

    def __init__(self, path: Path):
        """
        コンストラクタ

        Args:
            path (Path): 画像のパス
        """
        self.path = path
        self.dir = path.parent.name
        self.name = path.name
        try:
            with Image.open(path) as image:
                self.info = PicInfo(image)
        except Exception as e:
            print(f"Error PicStats {path}: {e}")

    def __eq__(self, other: PicStats):
        """
        各値が指定の PicStats のものと等しいか

        Args:
            other (PicStats): 比較対象

        Returns:
            _type_: True: 等しい, False: 等しくない
        """
        return (
            isinstance(other, PicStats)
            and self.path == other.path
            and self.dir == other.dir
            and self.name == other.name
            and self.info == other.info
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        このクラスを Dict[str, Any] に変形する

        Returns:
            Dict[str, Any]: 変形後インスタンス
        """
        dict = {}
        dict["path"] = str(self.path)
        dict["dir"] = self.dir
        dict["name"] = self.name
        dict["info"] = self.info.to_dict()
        return dict


class PicManager:
    """
    画像監視クラス
    """

    def __init__(self, rootdir: Path):
        """
        コンストラクタ\n
        piclist は ディレクトリ名とそのディレクトリに属するファイル名群を各成分とするリスト\n
        注目中の画像を PicStats の形で記憶する(専ら表示中と同義)

        Args:
            rootdir (Path): 監視対象ディレクトリ
        """
        self.rootdir = rootdir
        self.piclist: List[Dict[str, List[PicStats]]] = []
        self.refresh_piclist()
        self.crnt_picstats: PicStats | None = None

    def finalize(self) -> None:
        """
        終了処理
        """
        return

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
                    picstats.append(PicStats(path))
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

    def next_picstats(self) -> PicStats:
        """
        PicStats リストにおいて, 注目中 PicStats の次のものを返す\n
        末尾を注目中である場合はそれ自体を返す

        Returns:
            PicStats: 次の PicStats
        """
        picstats_list = self.get_picstats_list(self.crnt_picstats.dir)
        idx = picstats_list.index(self.crnt_picstats)
        return picstats_list[min(idx + 1, len(picstats_list) - 1)]

    def prev_picstats(self) -> PicStats:
        """
        PicStats リストにおいて, 注目中 PicStats の前のものを返す\n
        先頭を注目中である場合はそれ自体を返す

        Returns:
            PicStats: 前の PicStats
        """
        picstats_list = self.get_picstats_list(self.crnt_picstats.dir)
        idx = picstats_list.index(self.crnt_picstats)
        return picstats_list[max(idx - 1, 0)]

    def to_json(self) -> Dict:
        """
        このクラスを json に成形する

        Returns:
            Dict: json
        """
        serializable = []
        for d in self.piclist:
            for dirname, stats_list in d.items():
                serializable.append({"dir": dirname, "pics": [s.to_dict() for s in stats_list]})
        return json.dumps(serializable, ensure_ascii=False, indent=2)
