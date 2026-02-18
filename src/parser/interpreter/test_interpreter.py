"""
テスト用 Interpreter
"""

from __future__ import annotations

from pathlib import Path

from parser.interpreter.interpreter import Interpreter
from parser.prompter import CategoryPath


class TestInterpreter(Interpreter):
    """
    テスト用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath)
        self.category_list_v = []

    def restore_category_list(self, new_list: list[CategoryPath]) -> None:
        """
        カテゴリーリストを更新する

        Args:
            new_list (list[CategoryPath]): カテゴリーリスト
        """
        self.category_list_v = new_list

    @property
    def category_list(self) -> list[CategoryPath]:
        return self.category_list_v
