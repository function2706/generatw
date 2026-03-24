"""
テスト用 Interpreter
"""

from __future__ import annotations

from pathlib import Path

from common.expr import Expr
from parser.interpreter.interpreter import CategoryPath, Interpreter, ScreenConfig


class TestInterpreter(Interpreter):
    """
    テスト用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath, "KEY")

    def restore_screen_config(
        self,
        screen_id: str,
        cat_cfgs: dict[CategoryPath, tuple[Expr | None, bool]],
        sufficiency: Expr | None,
        request_cats: dict[str, list[CategoryPath]],
        takeover_cat: CategoryPath,
    ) -> None:
        """
        指定の Screen ID の ScreenConfig を更新する

        Args:
            screen_id (str): Screen ID
            pcatcfg (list[PrimitiveCategoryConfig]): PrimitiveCategoryConfig のリスト
            sufficiency (Expr): 充足条件
        """
        self.screen_table[screen_id] = ScreenConfig.set(
            cat_configs=cat_cfgs,
            sufficiency=sufficiency,
            request_cats=request_cats,
            takeover_cats=takeover_cat,
        )
