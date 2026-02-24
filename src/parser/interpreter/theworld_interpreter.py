"""
The World 用 Interpreter
"""

from __future__ import annotations

from pathlib import Path

from parser.interpreter.interpreter import Interpreter
from parser.prompter import CategoryPath, Prompt


class TheWorldInterpreter(Interpreter):
    """
    The World 用 Interpreter
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
                    ("character", "affection"),
                    ("character", "trust"),
                    ("character", "frustration"),
                    ("character", "angry"),
                    ("character", "in_heat"),
                    ("character", "mood"),
                    ("character", "reason"),
                    ("character", "upper"),
                    ("character", "upper_state"),
                    ("character", "lower"),
                    ("character", "lower_state"),
                ],
            )
        ]

    def edit(self, prompt: Prompt) -> Prompt:
        # T.B.D., ここに状態保存やフラグなどの処理が追加で必要
        return super().edit(prompt)

    @staticmethod
    def is_enough_prompt(prompt: Prompt) -> bool:
        """
        The World における十分性判定の基準
        1. main Screen
        1.1 ポジティブプロンプトに character > name Category が存在すること
        """
        has_name = False
        if prompt.screen_id == "main":
            for prompt_parts in prompt.positive:
                if len(prompt_parts.path) == 0:
                    # common
                    continue

                if prompt_parts.path[0:] == ("character", "name"):
                    has_name = True

        return Interpreter.is_enough_prompt(prompt) and has_name
