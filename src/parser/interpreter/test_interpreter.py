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

    @property
    def category_list(self) -> list[CategoryPath]:
        return [
            ("sub", "map2"),
            ("main", "map1"),
            ("main", "map2"),
        ]
