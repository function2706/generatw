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

    def is_enough_prompt(self):
        return super().is_enough_prompt()
