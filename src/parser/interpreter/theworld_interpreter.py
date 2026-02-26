"""
The World 用 Interpreter
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TypeAlias

from parser.interpreter.interpreter import Interpreter, Memory, MemoryEntry, ScreenTable
from parser.prompter import Prompt


class ScreenName(StrEnum):
    main = "main"
    status = "status"
    fashion = "fashion"


class CategoryName(StrEnum):
    character = "character"
    name_n = "name"
    vibe = "vibe"
    affection = "affection"
    trust = "trust"
    frustration = "frustration"
    angry = "angry"
    in_heat = "in_heat"
    mood = "mood"
    reason = "reason"
    upper_n = "upper"
    upper_state = "upper_state"
    lower_n = "lower"
    lower_state = "lower_state"
    caps = "caps"
    hands = "hands"
    dresses = "dresses"
    kimonos = "kimonos"
    outers = "outers"
    upper_cloths = "upper_cloths"
    lower_cloths = "lower_cloths"
    lingeries = "lingeries"
    upper_lingeries = "upper_lingeries"
    lower_lingeries = "lower_lingeries"
    socks = "socks"
    shoes = "shoes"
    equipments = "equipments"


@dataclass
class FashionSet:
    name: MemoryEntry = field(default_factory=MemoryEntry)
    caps: MemoryEntry = field(default_factory=MemoryEntry)
    dresses: MemoryEntry = field(default_factory=MemoryEntry)
    outers: MemoryEntry = field(default_factory=MemoryEntry)
    upper_cloths: MemoryEntry = field(default_factory=MemoryEntry)
    lower_cloths: MemoryEntry = field(default_factory=MemoryEntry)
    lingeries: MemoryEntry = field(default_factory=MemoryEntry)
    upper_lingeries: MemoryEntry = field(default_factory=MemoryEntry)
    lower_lingeries: MemoryEntry = field(default_factory=MemoryEntry)
    socks: MemoryEntry = field(default_factory=MemoryEntry)
    shoes: MemoryEntry = field(default_factory=MemoryEntry)
    equipments: MemoryEntry = field(default_factory=MemoryEntry)


FashionList: TypeAlias = list[FashionSet]


class TheWorldInterpreter(Interpreter):
    """
    The World 用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath)

        self.name_on_main = MemoryEntry()
        self.fashion_list = FashionList()

    @property
    def screen_table(self) -> ScreenTable:
        # 単項タプルの ',' を忘れないように!!
        return {
            ScreenName.main: (
                [
                    ((CategoryName.character, CategoryName.name_n), None, True),
                    ((CategoryName.character, CategoryName.vibe), None, False),
                    ((CategoryName.character, CategoryName.affection), None, False),
                    ((CategoryName.character, CategoryName.trust), None, False),
                    ((CategoryName.character, CategoryName.frustration), None, False),
                    ((CategoryName.character, CategoryName.angry), None, False),
                    ((CategoryName.character, CategoryName.in_heat), None, False),
                    ((CategoryName.character, CategoryName.mood), None, False),
                    ((CategoryName.character, CategoryName.reason), None, False),
                    ((CategoryName.character, CategoryName.upper_n), None, False),
                    ((CategoryName.character, CategoryName.upper_state), None, False),
                    ((CategoryName.character, CategoryName.lower_n), None, False),
                    ((CategoryName.character, CategoryName.lower_state), None, False),
                    ((CategoryName.caps,), None, False),
                    ((CategoryName.hands,), None, False),
                    ((CategoryName.dresses,), None, False),
                    ((CategoryName.kimonos,), None, False),
                    ((CategoryName.outers,), None, False),
                    ((CategoryName.upper_cloths,), None, False),
                    ((CategoryName.lower_cloths,), None, False),
                    ((CategoryName.lingeries,), None, False),
                    ((CategoryName.upper_lingeries,), None, False),
                    ((CategoryName.lower_lingeries,), None, False),
                    ((CategoryName.socks,), None, False),
                    ((CategoryName.shoes,), None, False),
                    ((CategoryName.equipments,), None, False),
                ],
                self.sync_on_main,
            ),
            ScreenName.status: (
                [
                    ((CategoryName.name_n,), None, False),
                    ((CategoryName.affection,), None, False),
                    ((CategoryName.trust,), None, False),
                    ((CategoryName.caps,), None, False),
                    ((CategoryName.hands,), None, False),
                    ((CategoryName.dresses,), None, False),
                    ((CategoryName.kimonos,), None, False),
                    ((CategoryName.outers,), None, False),
                    ((CategoryName.upper_cloths,), None, False),
                    ((CategoryName.lower_cloths,), None, False),
                    ((CategoryName.lingeries,), None, False),
                    ((CategoryName.upper_lingeries,), None, False),
                    ((CategoryName.lower_lingeries,), None, False),
                    ((CategoryName.socks,), None, False),
                    ((CategoryName.shoes,), None, False),
                    ((CategoryName.equipments,), None, False),
                ],
                None,
            ),
            ScreenName.fashion: (
                [
                    ((CategoryName.character, CategoryName.name_n), None, False),
                    ((CategoryName.caps,), None, False),
                    ((CategoryName.hands,), None, False),
                    ((CategoryName.dresses,), None, False),
                    ((CategoryName.kimonos,), None, False),
                    ((CategoryName.outers,), None, False),
                    ((CategoryName.upper_cloths,), None, False),
                    ((CategoryName.lower_cloths,), None, False),
                    ((CategoryName.lingeries,), None, False),
                    ((CategoryName.upper_lingeries,), None, False),
                    ((CategoryName.lower_lingeries,), None, False),
                    ((CategoryName.socks,), None, False),
                    ((CategoryName.shoes,), None, False),
                    ((CategoryName.equipments,), None, False),
                ],
                self.sync_on_fashion,
            ),
        }

    def sync_on_main(self, memory: Memory) -> Memory:
        """
        main Screen の同期処理

        記憶: name (着せ替え画面用, 服装確認画面ではない)\n
        想起: 注目中の character (name) に紐づく FashionSet を付帯

        Args:
            memory (Memory): 同期する Memory

        Returns:
            Prompt: 同期済み Prompt
        """
        # Save
        for entry in memory.entries:
            if entry.path == (CategoryName.character, CategoryName.name_n):
                self.name_on_main = entry
                break

        # Load
        recalled = deepcopy(memory)
        for entry in memory.entries:
            if entry.path != (CategoryName.character, CategoryName.name_n):
                continue
            name = entry
            for fashion_set in self.fashion_list:
                if fashion_set.name != name:
                    continue
                for field_name in FashionSet.__dataclass_fields__.keys():
                    if field_name == CategoryName.name_n:
                        continue
                    fashion: MemoryEntry = getattr(fashion_set, field_name)
                    if fashion.pos_tokens or fashion.neg_tokens:
                        recalled.entries.append(fashion)
        return recalled

    def sync_on_fashion(self, memory: Memory) -> Memory:
        """
        fashion Screen の同期処理

        記憶: 各 Category + 記憶中の main Screen の name\n
        想起: 記憶中の name を付帯

        Args:
            memory (Memory): 同期する Memory

        Returns:
            Prompt: 同期済み Prompt
        """
        # Save
        new_fashion_set = FashionSet(name=self.name_on_main)
        for entry in memory.entries:
            if len(entry.path) > 0 and hasattr(new_fashion_set, entry.path[0]):
                # common 以外の全 Category を記録
                setattr(new_fashion_set, entry.path[0], entry)
        exists = False
        for idx, fashion_set in enumerate(self.fashion_list):
            if fashion_set.name == new_fashion_set.name:
                # すでにリストにある場合は更新
                self.fashion_list[idx] = new_fashion_set
                exists = True
                break
        if not exists:
            # なかった場合は新たに登録
            self.fashion_list.append(new_fashion_set)

        # Load
        recalled = deepcopy(memory)
        recalled.entries.append(self.name_on_main)
        return recalled

    @staticmethod
    def is_enough_prompt(prompt: Prompt) -> bool:
        """
        The World における十分性判定の基準
        1. main Screen
        1.1 ポジティブプロンプトに character > name Category が存在すること
        2. status Screen
        2.1 ポジティブプロンプトに name Category が存在すること
        3. fashion Screen
        3.1 ポジティブプロンプトに name Category が存在すること
        """
        has_name = False
        if prompt.screen_id == ScreenName.main:
            for prompt_parts in prompt.positive:
                if len(prompt_parts.path) == 0:
                    # common
                    continue
                if prompt_parts.path[0:] == (CategoryName.character, CategoryName.name_n):
                    has_name = True
        elif prompt.screen_id == ScreenName.status:
            for prompt_parts in prompt.positive:
                if len(prompt_parts.path) == 0:
                    # common
                    continue
                if prompt_parts.path[0:] == (CategoryName.name_n,):
                    has_name = True
        elif prompt.screen_id == ScreenName.fashion:
            for prompt_parts in prompt.positive:
                if len(prompt_parts.path) == 0:
                    # common
                    continue
                if prompt_parts.path[0:] == (CategoryName.character, CategoryName.name_n):
                    has_name = True

        return Interpreter.is_enough_prompt(prompt) and has_name
