"""
テスト用 Interpreter
"""

from __future__ import annotations

from pathlib import Path

from parser.interpreter.interpreter import EnhancedCategory, Interpreter, ScreenTable


class TestInterpreter(Interpreter):
    """
    テスト用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath)
        self.screen_table_v: ScreenTable = {}

    def restore_enhanced_category_list(
        self, screen_id: str, encats: list[EnhancedCategory]
    ) -> None:
        """
        指定の Screen ID の list[EnhancedCategory] を更新する

        Args:
            encats (list[EnhancedCategory]): list[CategoryPath], Expr, Essential Checker のリスト
        """
        self.screen_table_v[screen_id] = (encats, None)

    @property
    def screen_table(self) -> ScreenTable:
        return self.screen_table_v
