"""
The World 用 Interpreter
"""

from __future__ import annotations

from pathlib import Path

from parser.interpreter.interpreter import Interpreter, PromptSet
from parser.prompter import CategoryPath, Prompt


class TheWorldInterpreter(Interpreter):
    """
    The World 用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath)

    @property
    def category_list(self) -> list[CategoryPath]:
        return [
            ("main", "character", "name"),
            ("main", "character", "vibe"),
            ("main", "character", "affection"),
            ("main", "character", "trust"),
            ("main", "character", "frustration"),
            ("main", "character", "angry"),
            ("main", "character", "in_heat"),
            ("main", "character", "mood"),
            ("main", "character", "reason"),
            ("main", "character", "upper"),
            ("main", "character", "upper_state"),
            ("main", "character", "lower"),
            ("main", "character", "lower_state"),
        ]

    def edit(self, prompt: Prompt) -> Prompt:
        # T.B.D., ここに状態保存やフラグなどの処理が追加で必要
        return super().edit(prompt)

    @staticmethod
    def is_enough_prompt(prompt_set: PromptSet) -> bool:
        """
        The World における十分性判定の基準
        1. main Screen
        1.1 ポジティブプロンプトに character > name Category が存在すること
        """
        has_name = False
        for prompt_parts in prompt_set.positive:
            if len(prompt_parts.path) <= 1:
                # common
                continue

            screen_id = prompt_parts.path[0]
            if screen_id == "main":
                if prompt_parts.path[1:] == ("character", "name"):
                    has_name = True

        return Interpreter.is_enough_prompt(prompt_set) and has_name
