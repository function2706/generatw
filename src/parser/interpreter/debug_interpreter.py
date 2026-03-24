"""
デバッグ用 Interpreter
"""

from __future__ import annotations

from pathlib import Path

from parser.interpreter.interpreter import Interpreter, ScreenConfig


class DebugInterpreter(Interpreter):
    """
    デバッグ用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath, "name")

        self.screen_table = {
            "main": ScreenConfig.set(
                cat_configs={
                    ("character", "name"): (None, False),
                    ("character", "vibe"): (None, False),
                    ("character", "upper"): (None, False),
                    ("character", "lower"): (None, False),
                }
            )
        }
