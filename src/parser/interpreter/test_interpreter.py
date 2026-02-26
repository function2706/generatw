"""
テスト用 Interpreter
"""

from __future__ import annotations

from pathlib import Path

from parser.interpreter.interpreter import CategoryList, Interpreter, ScreenTable


class TestInterpreter(Interpreter):
    """
    テスト用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath)
        self.screen_table_v: ScreenTable = {}

    def restore_category_list(self, screen_id: str, cat_list: CategoryList) -> None:
        """
        指定の Screen ID の CategoryList を更新する

        Args:
            cat_list (CategoryList): CategoryList
        """
        self.screen_table[screen_id] = (cat_list, None)

    @property
    def screen_table(self) -> ScreenTable:
        return self.screen_table_v
