"""
共用クラス
"""

from __future__ import annotations

from dataclasses import dataclass


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
    allow_edit_clipboard: bool = False
    print_new_clipboard: bool = False
    print_new_stats: bool = False
    print_picinfo: bool = False
    print_event: bool = False
