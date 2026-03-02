"""
The World 用 Interpreter
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TypeAlias

from common.expr import Has
from parser.interpreter.interpreter import Interpreter, Memory, MemoryEntry, ScreenTable


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
    whole_lingeries = "whole_lingeries"
    upper_lingeries = "upper_lingeries"
    lower_lingeries = "lower_lingeries"
    socks = "socks"
    shoes = "shoes"
    equipments = "equipments"
    accessories = "accessories"


@dataclass
class FashionSet:
    name: MemoryEntry = field(default_factory=MemoryEntry)
    caps: MemoryEntry = field(default_factory=MemoryEntry)
    hands: MemoryEntry = field(default_factory=MemoryEntry)
    dresses: MemoryEntry = field(default_factory=MemoryEntry)
    kimonos: MemoryEntry = field(default_factory=MemoryEntry)
    outers: MemoryEntry = field(default_factory=MemoryEntry)
    upper_cloths: MemoryEntry = field(default_factory=MemoryEntry)
    lower_cloths: MemoryEntry = field(default_factory=MemoryEntry)
    lingeries: MemoryEntry = field(default_factory=MemoryEntry)
    whole_lingeries: MemoryEntry = field(default_factory=MemoryEntry)
    upper_lingeries: MemoryEntry = field(default_factory=MemoryEntry)
    lower_lingeries: MemoryEntry = field(default_factory=MemoryEntry)
    socks: MemoryEntry = field(default_factory=MemoryEntry)
    shoes: MemoryEntry = field(default_factory=MemoryEntry)
    equipments: MemoryEntry = field(default_factory=MemoryEntry)
    accessories: MemoryEntry = field(default_factory=MemoryEntry)


FashionList: TypeAlias = list[FashionSet]


class TheWorldInterpreter(Interpreter):
    """
    The World 用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath)

        self.name_on_main: MemoryEntry = MemoryEntry()
        self.fashion_list: FashionList = FashionList()

    @property
    def screen_table(self) -> ScreenTable:
        expr_no_upper_costumes = (
            ~Has((CategoryName.outers,))
            & ~Has((CategoryName.upper_cloths,))
            & ~Has((CategoryName.dresses,))
            & ~Has((CategoryName.kimonos,))
        )
        expr_no_lower_costumes = (
            ~Has((CategoryName.lower_cloths,))
            & ~Has((CategoryName.dresses,))
            & ~Has((CategoryName.kimonos,))
        )
        expr_no_costumes = expr_no_upper_costumes & expr_no_lower_costumes

        # 単項タプルの ',' を忘れないように!!
        return {
            ScreenName.main: (
                [
                    ((CategoryName.character, CategoryName.name_n), None),
                    ((CategoryName.character, CategoryName.vibe), None),
                    ((CategoryName.character, CategoryName.affection), None),
                    ((CategoryName.character, CategoryName.trust), None),
                    ((CategoryName.character, CategoryName.frustration), None),
                    ((CategoryName.character, CategoryName.angry), None),
                    ((CategoryName.character, CategoryName.in_heat), None),
                    ((CategoryName.character, CategoryName.mood), None),
                    ((CategoryName.character, CategoryName.reason), None),
                    ((CategoryName.character, CategoryName.upper_n), None),
                    ((CategoryName.character, CategoryName.upper_state), None),
                    ((CategoryName.character, CategoryName.lower_n), None),
                    ((CategoryName.character, CategoryName.lower_state), None),
                    ((CategoryName.caps,), None),
                    ((CategoryName.hands,), None),
                    ((CategoryName.dresses,), None),
                    ((CategoryName.kimonos,), None),
                    ((CategoryName.outers,), None),
                    ((CategoryName.upper_cloths,), None),
                    ((CategoryName.lower_cloths,), None),
                    ((CategoryName.lingeries,), expr_no_costumes),
                    ((CategoryName.whole_lingeries,), expr_no_costumes),
                    ((CategoryName.upper_lingeries,), expr_no_upper_costumes),
                    ((CategoryName.lower_lingeries,), expr_no_lower_costumes),
                    ((CategoryName.socks,), None),
                    ((CategoryName.shoes,), None),
                    ((CategoryName.equipments,), None),
                    ((CategoryName.accessories,), None),
                ],
                Has((CategoryName.character, CategoryName.name_n)),
                self.sync_on_main,
            ),
            ScreenName.status: (
                [
                    ((CategoryName.name_n,), None),
                    ((CategoryName.affection,), None),
                    ((CategoryName.trust,), None),
                    ((CategoryName.caps,), None),
                    ((CategoryName.hands,), None),
                    ((CategoryName.dresses,), None),
                    ((CategoryName.kimonos,), None),
                    ((CategoryName.outers,), None),
                    ((CategoryName.upper_cloths,), None),
                    ((CategoryName.lower_cloths,), None),
                    ((CategoryName.lingeries,), expr_no_costumes),
                    ((CategoryName.whole_lingeries,), expr_no_costumes),
                    ((CategoryName.upper_lingeries,), expr_no_upper_costumes),
                    ((CategoryName.lower_lingeries,), expr_no_lower_costumes),
                    ((CategoryName.socks,), None),
                    ((CategoryName.shoes,), None),
                    ((CategoryName.equipments,), None),
                    ((CategoryName.accessories,), None),
                ],
                Has((CategoryName.name_n,)),
                None,
            ),
            ScreenName.fashion: (
                [
                    ((CategoryName.character, CategoryName.name_n), None),
                    ((CategoryName.caps,), None),
                    ((CategoryName.hands,), None),
                    ((CategoryName.dresses,), None),
                    ((CategoryName.kimonos,), None),
                    ((CategoryName.outers,), None),
                    ((CategoryName.upper_cloths,), None),
                    ((CategoryName.lower_cloths,), None),
                    ((CategoryName.lingeries,), expr_no_costumes),
                    ((CategoryName.whole_lingeries,), expr_no_costumes),
                    ((CategoryName.upper_lingeries,), expr_no_upper_costumes),
                    ((CategoryName.lower_lingeries,), expr_no_lower_costumes),
                    ((CategoryName.socks,), None),
                    ((CategoryName.shoes,), None),
                    ((CategoryName.equipments,), None),
                    ((CategoryName.accessories,), None),
                ],
                Has((CategoryName.character, CategoryName.name_n)),
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
            Memory: 同期済み Memory
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
            Memory: 同期済み Memory
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

    def save_state(self) -> dict:
        """
        このインスタンスの状態を保存可能な形式で返す\n
        name_on_main と fashion_list を保存する

        Returns:
            dict: 状態を表す辞書
        """
        return {
            "name_on_main": deepcopy(self.name_on_main),
            "fashion_list": deepcopy(self.fashion_list),
        }

    def restore_state(self, state: dict) -> None:
        """
        指定の状態から記憶を復元する\n
        不正な状態が渡された場合は無視する(何もしない)

        Args:
            state (dict): 保存された状態
        """
        try:
            if "name_on_main" in state:
                self.name_on_main = deepcopy(state["name_on_main"])
            if "fashion_list" in state:
                self.fashion_list = deepcopy(state["fashion_list"])
        except Exception:
            # 不正な状態の場合は無視する
            pass
