from __future__ import annotations
from pathlib import Path
from PIL import Image
from typing import Any
import json, os

# 画像のメタデータ
class PicInfo:
    # コンストラクタ
    def __init__(self, image: Image):
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

    # 等号定義
    def __eq__(self, other):
        return (isinstance(other, PicInfo)
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
                and self.parameters == other.parameters)

    # dict に成形する
    def to_dict(self) -> dict[str, Any]:
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

# 画像情報
class PicStats:
    # コンストラクタ
    def __init__(self, path: Path):
        self.path = path
        self.dir = Path(path.parent.name)
        self.name = Path(path.name)
        try:
            with Image.open(path) as image:
                self.info = PicInfo(image)
        except Exception as e:
            print(f"Error PicStats {path}: {e}")

    # 等号定義
    def __eq__(self, other):
        return (isinstance(other, PicStats)
                and self.path == other.path
                and self.dir == other.dir
                and self.name == other.name
                and self.info == other.info)

    # dict に成形する
    def to_dict(self) -> dict[str, Any]:
        dict = {}
        dict["path"] = str(self.path)
        dict["dir"] = str(self.dir)
        dict["name"] = str(self.name)
        dict["info"] = self.info.to_dict()
        return dict

# 画像監視クラス
class PicManager:
    # コンストラクタ
    def __init__(self, rootdir: Path):
        self.rootdir = rootdir
        self.piclist: list[dict[Path, list[PicStats]]] = []
        self.refresh_piclist()
        self.crnt_picstats: PicStats | None = None

    # 親ディレクトリ内の画像ファイルを PicStats の形で再帰的にリスト化する
    def refresh_piclist(self) -> None:
        self.piclist = []
        for dirpath, _, filenames in os.walk(self.rootdir):
            picstats: list[PicStats] = []
            for filename in filenames:
                if filename.lower().endswith(".png"):
                    path = Path(dirpath) / filename
                    picstats.append(PicStats(path))
            if picstats:
                dirname = Path(dirpath).name
                self.piclist.append({Path(dirname): picstats})

    # 指定のディレクトリ名を持つ PicStats リストを返す
    def get_picstats_list(self, dirname: Path) -> list[PicStats]:
        for d in self.piclist:
            if dirname in d:
                return d[dirname]
        return []

    # PicStats リストにおいて, 現在の次のものを返す
    def next_picstats(self) -> PicStats:
        picstats_list = self.get_picstats_list(self.crnt_picstats.dir)
        idx = picstats_list.index(self.crnt_picstats)
        return picstats_list[min(idx + 1, len(picstats_list) - 1)]

    # PicStats リストにおいて, 現在の前のものを返す
    def prev_picstats(self) -> PicStats:
        picstats_list = self.get_picstats_list(self.crnt_picstats.dir)
        idx = picstats_list.index(self.crnt_picstats)
        return picstats_list[max(idx - 1, 0)]

    def to_json(self) -> dict:
        serializable = []
        for d in self.piclist:
            for dirname, stats_list in d.items():
                serializable.append({
                    "dir": str(dirname),
                    "pics": [s.to_dict() for s in stats_list]
                })
        return json.dumps(serializable, ensure_ascii=False, indent=2)