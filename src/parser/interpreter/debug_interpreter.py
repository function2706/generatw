"""
デバッグ用 Interpreter
"""

from __future__ import annotations

from pathlib import Path

from parser.interpreter.interpreter import CategoryList, Interpreter


class DebugInterpreter(Interpreter):
    """
    デバッグ用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath)

    @property
    def category_list(self) -> CategoryList:
        return {
            "main": [
                ("character", "name"),
                ("character", "vibe"),
                ("character", "upper"),
                ("character", "lower"),
            ]
        }
