"""
共用クラス
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class GUIConfigs:
    """
    Displayer 外で参照する設定フォーマット
    """

    srv_ipaddr: str = ""
    srv_port: str = ""
    sd_steps: int = 0
    sd_batch_size: int = 0
    sd_width: int = 0
    sd_height: int = 0
    yamlpath: str | None = None
    backend: str = ""
    allow_edit_clipboard: bool = False
    print_new_clipboard: bool = False
    print_new_prompt_set: bool = False
    print_new_prompt: bool = False
    print_picinfo: bool = False
    print_event: bool = False

    @classmethod
    def fromjson(cls, path: Path) -> GUIConfigs:
        with open(path, "r", encoding="utf-8") as f:
            return cls(**json.load(f))

    def tojson(self, path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)
