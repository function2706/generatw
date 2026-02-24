"""
デバッグ用 Interpreter
"""

from __future__ import annotations

from pathlib import Path

from parser.interpreter.interpreter import Interpreter
from parser.prompter import CategoryPath


class DebugInterpreter(Interpreter):
    """
    デバッグ用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath)

    @property
    def category_list(self) -> list[tuple[str, list[CategoryPath]]]:
        return [
            (
                "main",
                [
                    ("character", "name"),
                    ("character", "vibe"),
                    ("character", "upper"),
                    ("character", "lower"),
                ],
            )
        ]
