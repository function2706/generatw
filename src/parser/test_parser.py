"""
テスト用 Parser
"""

from __future__ import annotations

from common.functions import BottleMail
from master.events import ParserEvent
from master.interfaces import MasterIF
from parser.parser import Parser, PromptSet
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

    def edit(self, prompt_base: PromptSet) -> PromptSet:
        return prompt_base

    def is_enough_prompt(self):
        return True
