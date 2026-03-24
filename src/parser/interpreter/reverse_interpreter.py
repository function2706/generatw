"""
Reverse 用 Interpreter
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from common.expr import Has
from parser.interpreter.interpreter import Interpreter, ScreenConfig


class Scr(StrEnum):
    main = "main"
    action = "action"


class Cat(StrEnum):
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


class ReverseInterpreter(Interpreter):
    """
    Reverse 用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath, Cat.name_n)

        expr_no_upper_costumes = ~Has(
            (
                Cat.character,
                Cat.fashion,
                Cat.dresses,
            )
        )
        expr_no_lower_costumes = ~Has(
            (
                Cat.character,
                Cat.fashion,
                Cat.dresses,
            )
        )

        # 単項タプルの ',' を忘れないように!!
        self.screen_table = {
            Scr.main: ScreenConfig.set(
                cat_configs={
                    (Cat.character, Cat.name_n): (None, True),
                    (Cat.character, Cat.vibe): (None, False),
                    (Cat.character, Cat.fashion, Cat.dresses): (None, True),
                    (Cat.character, Cat.fashion, Cat.upper_lingeries): (
                        expr_no_upper_costumes,
                        True,
                    ),
                    (Cat.character, Cat.fashion, Cat.lower_lingeries): (
                        expr_no_lower_costumes,
                        True,
                    ),
                    (Cat.character, Cat.fashion, Cat.socks): (None, True),
                    (Cat.character, Cat.posture, Cat.posture_meat): (None, False),
                    (Cat.character, Cat.tool, Cat.tool_meat): (None, False),
                },
                sufficiency=Has((Cat.character, Cat.name_n)),
            ),
            Scr.action: ScreenConfig.set(
                cat_configs={
                    (Cat.character, Cat.name_n): (None, True),
                    (Cat.character, Cat.vibe): (None, False),
                    (Cat.asking,): (None, False),
                    (Cat.rope,): (None, False),
                    (Cat.foot_licking,): (None, False),
                    (Cat.character, Cat.fashion, Cat.dresses): (None, True),
                    (Cat.character, Cat.fashion, Cat.upper_lingeries): (
                        expr_no_upper_costumes,
                        True,
                    ),
                    (Cat.character, Cat.fashion, Cat.lower_lingeries): (
                        expr_no_lower_costumes,
                        True,
                    ),
                    (Cat.character, Cat.fashion, Cat.socks): (None, True),
                    (Cat.character, Cat.posture, Cat.posture_meat): (None, False),
                    (Cat.character, Cat.tool, Cat.tool_meat): (None, False),
                },
                sufficiency=Has((Cat.character, Cat.name_n)),
                takeover_cats=[(Cat.character, Cat.name_n)],
                request_cats={
                    Scr.main: [
                        (Cat.character, Cat.vibe),
                        (Cat.character, Cat.fashion, Cat.dresses),
                        (Cat.character, Cat.fashion, Cat.upper_lingeries),
                        (Cat.character, Cat.fashion, Cat.lower_lingeries),
                        (Cat.character, Cat.fashion, Cat.socks),
                    ]
                },
            ),
        }
