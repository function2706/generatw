"""
The World 用 Parser
"""

from __future__ import annotations

from common.functions import BottleMail
from master.events import ParserEvent
from master.interfaces import MasterIF
from parser.parser import Parser, Prompt
from parser.prompter import CategoryPath

KEYWORD_THE_WORLD_PARSER = "TheWorldParser"
KEY_LIST: list[CategoryPath] = [
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


class TheWorldParser(Parser):
    """
    The World 用 Parser
    """

    def __init__(
        self,
        master: MasterIF,
        to_master: BottleMail[ParserEvent],
    ):
        super().__init__(master, to_master, KEY_LIST)

    def edit(self, prompt: Prompt) -> Prompt:
        return super().edit(prompt)

    def is_enough_prompt(self) -> bool:
        """
        The World における十分性判定の基準
        1. main Screen
        1.1 ポジティブプロンプトに character > name Category が存在すること
        """
        has_name = False
        for prompt_parts in self.crnt_prompt_set.positive:
            if len(prompt_parts.path) <= 1:
                # common
                continue

            screen_id = prompt_parts.path[0]
            if screen_id == "main":
                if prompt_parts.path[1:] == ("character", "name"):
                    has_name = True

        return super().is_enough_prompt() and has_name
