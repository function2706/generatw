"""
テスト用 Parser
"""

from __future__ import annotations

from common.functions import BottleMail
from master.events import ParserEvent
from master.interfaces import MasterIF
from parser.parser import Parser, Prompt, PromptSet
from parser.prompter import CategoryPath

KEYWORD_TEST_PARSER = "TestParser"
KEY_LIST: list[CategoryPath] = [
    ("sub", "map2"),
    ("main", "map1"),
    ("main", "map2"),
]


class TestParser(Parser):
    """
    テスト用 Parser (edit で何もしない)
    """

    def __init__(
        self,
        master: MasterIF,
        to_master: BottleMail[ParserEvent],
    ):
        super().__init__(master, to_master, KEY_LIST)

    def edit(self, prompt: Prompt) -> Prompt:
        return super().edit(prompt)

    def is_enough_prompt(self, prompt_set: PromptSet | None = None):
        return super().is_enough_prompt(prompt_set)
