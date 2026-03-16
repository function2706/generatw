"""
テスト用 Interpreter
"""

from __future__ import annotations

from pathlib import Path

from common.expr import Expr
from parser.interpreter.interpreter import Interpreter, PrimitiveCategoryConfig, ScreenConfig


class TestInterpreter(Interpreter):
    """
    テスト用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath)

    def restore_screen_config(
        self, screen_id: str, pcatcfg: list[PrimitiveCategoryConfig], essential: Expr
    ) -> None:
        """
        指定の Screen ID の ScreenConfig を更新する

        Args:
            screen_id (str): Screen ID
            pcatcfg (list[PrimitiveCategoryConfig]): PrimitiveCategoryConfig のリスト
            essential (Expr): 充足条件
        """
        self.screen_table[screen_id] = ScreenConfig.set(
            primitive_category_configs=pcatcfg, essential_condition=essential, syncer=None
        )

    def save_state(self) -> dict:
        """
        このインスタンスの状態を保存可能な形式で返す\n
        TestInterpreter は記憶を持たない

        Returns:
            dict: 常に空の辞書
        """
        return {}

    def restore_state(self, state: dict) -> None:
        """
        指定の状態から記憶を復元する\n
        TestInterpreter は記憶がないため何もしない

        Args:
            state (dict): 保存された状態 (無視される)
        """
        return
