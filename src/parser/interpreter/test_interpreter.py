"""
テスト用 Interpreter
"""

from __future__ import annotations

from pathlib import Path

from parser.interpreter.interpreter import CategoryList, Interpreter


class TestInterpreter(Interpreter):
    """
    テスト用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath)
        self.category_list_v: CategoryList = {}

    def restore_category_list(self, new_list: CategoryList) -> None:
        """
        カテゴリーリストを更新する

        Args:
            new_list (list[CategoryPath]): カテゴリーリスト
        """
        self.category_list_v = new_list

    @property
    def category_list(self) -> CategoryList:
        return self.category_list_v
