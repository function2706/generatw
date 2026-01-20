"""
ファイル生成クラス (ComfyUI 版)
"""

from __future__ import annotations

from typing import Any

from common.interfaces import MasterIF
from generator.generator import Generator


class ComfyUIGenerator(Generator[None]):
    """
    ファイル生成クラス (ComfyUI 版)\n
    タスク設計図をもとにサーバへ非同期にポストし, ファイル保存をする
    """

    def __init__(self, master: MasterIF):
        """
        コンストラクタ

        Args:
            master (MasterIF): Master インターフェース
        """
        super().__init__(master)

    def request_generate(self) -> tuple[Any, Any] | None:
        return

    def request_upscale(self) -> None:
        return

    def request_interrupt(self) -> None:
        return

    def request_progress(self) -> None:
        return None
