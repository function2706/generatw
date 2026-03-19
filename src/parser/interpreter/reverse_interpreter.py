"""
Reverse 用 Interpreter
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from common.expr import Has
from parser.interpreter.interpreter import Interpreter, Memory, MemoryEntry, ScreenConfig


class ScreenName(StrEnum):
    main = "main"
    action = "action"


class CategoryName(StrEnum):
    character = "character"
    name_n = "name"
    vibe = "vibe"
    fashion = "fashion"
    dresses = "dresses"
    upper_lingeries = "upper_lingeries"
    lower_lingeries = "lower_lingeries"
    socks = "socks"
    posture = "posture"
    posture_meat = "posture_meat"
    tool = "tool"
    tool_meat = "tool_meat"
    asking = "asking"
    rope = "rope"
    foot_licking = "foot_licking"


@dataclass
class FashionSet:
    dresses: MemoryEntry = field(default_factory=MemoryEntry)
    upper_lingeries: MemoryEntry = field(default_factory=MemoryEntry)
    lower_lingeries: MemoryEntry = field(default_factory=MemoryEntry)
    socks: MemoryEntry = field(default_factory=MemoryEntry)


class ReverseInterpreter(Interpreter):
    """
    Reverse 用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath)

        self.name_on_main: MemoryEntry = MemoryEntry()
        self.fashion_set: FashionSet = FashionSet()

        expr_no_upper_costumes = ~Has(
            (
                CategoryName.character,
                CategoryName.fashion,
                CategoryName.dresses,
            )
        )
        expr_no_lower_costumes = ~Has(
            (
                CategoryName.character,
                CategoryName.fashion,
                CategoryName.dresses,
            )
        )

        # 単項タプルの ',' を忘れないように!!
        self.screen_table = {
            ScreenName.main: ScreenConfig.set(
                primitive_category_configs=[
                    ((CategoryName.character, CategoryName.name_n), None, True),
                    ((CategoryName.character, CategoryName.vibe), None, False),
                    (
                        (CategoryName.character, CategoryName.fashion, CategoryName.dresses),
                        None,
                        True,
                    ),
                    (
                        (
                            CategoryName.character,
                            CategoryName.fashion,
                            CategoryName.upper_lingeries,
                        ),
                        expr_no_upper_costumes,
                        True,
                    ),
                    (
                        (
                            CategoryName.character,
                            CategoryName.fashion,
                            CategoryName.lower_lingeries,
                        ),
                        expr_no_lower_costumes,
                        True,
                    ),
                    (
                        (CategoryName.character, CategoryName.fashion, CategoryName.socks),
                        None,
                        True,
                    ),
                    (
                        (
                            CategoryName.character,
                            CategoryName.posture,
                            CategoryName.posture_meat,
                        ),
                        None,
                        False,
                    ),
                    (
                        (CategoryName.character, CategoryName.tool, CategoryName.tool_meat),
                        None,
                        False,
                    ),
                ],
                sufficiency=Has((CategoryName.character, CategoryName.name_n)),
                syncer=self.sync_on_main,
            ),
            ScreenName.action: ScreenConfig.set(
                primitive_category_configs=[
                    ((CategoryName.character, CategoryName.name_n), None, True),
                    ((CategoryName.asking,), None, False),
                    ((CategoryName.rope,), None, False),
                    ((CategoryName.foot_licking,), None, False),
                    (
                        (CategoryName.character, CategoryName.fashion, CategoryName.dresses),
                        None,
                        True,
                    ),
                    (
                        (
                            CategoryName.character,
                            CategoryName.fashion,
                            CategoryName.upper_lingeries,
                        ),
                        expr_no_upper_costumes,
                        True,
                    ),
                    (
                        (
                            CategoryName.character,
                            CategoryName.fashion,
                            CategoryName.lower_lingeries,
                        ),
                        expr_no_lower_costumes,
                        True,
                    ),
                    (
                        (CategoryName.character, CategoryName.fashion, CategoryName.socks),
                        None,
                        True,
                    ),
                    (
                        (
                            CategoryName.character,
                            CategoryName.posture,
                            CategoryName.posture_meat,
                        ),
                        None,
                        False,
                    ),
                    (
                        (CategoryName.character, CategoryName.tool, CategoryName.tool_meat),
                        None,
                        False,
                    ),
                ],
                sufficiency=Has((CategoryName.character, CategoryName.name_n)),
                syncer=self.sync_on_action,
            ),
        }

    def sync_on_main(self, memory: Memory) -> Memory:
        """
        main Screen の同期処理

        記憶: name, FashionSet\n
        想起: なし

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

        new_fashion_set = FashionSet()
        for entry in memory.entries:
            if len(entry.path) >= 3 and hasattr(new_fashion_set, entry.path[2]):
                # common 以外の全 Category を記録
                setattr(new_fashion_set, entry.path[2], entry)
        self.fashion_set = new_fashion_set

        # Load

        return memory

    def sync_on_action(self, memory: Memory) -> Memory:
        """
        action Screen の同期処理

        記憶: なし\n
        想起: 記憶中の name, FashionSet を付帯

        Args:
            memory (Memory): 同期する Memory

        Returns:
            Memory: 同期済み Memory
        """
        # Save

        # Load
        recalled = deepcopy(memory)
        recalled.entries.append(self.name_on_main)

        for field_name in FashionSet.__dataclass_fields__.keys():
            fashion: MemoryEntry = getattr(self.fashion_set, field_name)
            if fashion.pos_tokens or fashion.neg_tokens:
                recalled.entries.append(fashion)

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
            "fashion_set": deepcopy(self.fashion_set),
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
            if "fashion_set" in state:
                self.fashion_set = deepcopy(state["fashion_set"])
        except Exception:
            # 不正な状態の場合は無視する
            pass
