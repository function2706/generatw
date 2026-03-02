"""
テスト用 Interpreter
"""

from __future__ import annotations

from pathlib import Path

from common.expr import Expr
from parser.interpreter.interpreter import EnhancedCategory, Interpreter, ScreenTable


class TestInterpreter(Interpreter):
    """
    テスト用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath)
        self.screen_table_v: ScreenTable = {}

    def restore_enhanced_category_list(
        self, screen_id: str, encats: list[EnhancedCategory], essential: Expr
    ) -> None:
        """
        指定の Screen ID の list[EnhancedCategory] を更新する

        Args:
            screen_id (str): Screen ID
            encats (list[EnhancedCategory]): list[CategoryPath], Expr, Essential Checker のリスト
            essential (Expr): 充足条件
        """
        self.screen_table_v[screen_id] = (encats, essential, None)

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

    @property
    def screen_table(self) -> ScreenTable:
        return self.screen_table_v
