"""
The World 用 Interpreter
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from common.expr import Has
from parser.interpreter.interpreter import Interpreter, ScreenConfig


class Scr(StrEnum):
    main = "main"
    action = "action"
    status = "status"
    fashion = "fashion"


class Cat(StrEnum):
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
    meta = "meta"
    time = "time"
    day = "day"
    night = "night"
    location = "location"
    indoors = "indoors"
    outdoors = "outdoors"
    type1 = "type1"
    type2 = "type2"
    type3 = "type3"
    weather = "weather"
    action = "action"
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


class TheWorldInterpreter(Interpreter):
    """
    The World 用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath, Cat.name_n)

        expr_no_upper_costumes = (
            ~Has((Cat.outers,))
            & ~Has((Cat.upper_cloths,))
            & ~Has((Cat.dresses,))
            & ~Has((Cat.kimonos,))
        )
        expr_no_lower_costumes = (
            ~Has((Cat.lower_cloths,)) & ~Has((Cat.dresses,)) & ~Has((Cat.kimonos,))
        )
        expr_no_costumes = expr_no_upper_costumes & expr_no_lower_costumes
        expr_outdoors = (
            Has((Cat.meta, Cat.location, Cat.outdoors, Cat.type1))
            | Has((Cat.meta, Cat.location, Cat.outdoors, Cat.type2))
            | Has((Cat.meta, Cat.location, Cat.outdoors, Cat.type3))
        )

        # 単項タプルの ',' を忘れないように!!
        self.screen_table = {
            Scr.main: ScreenConfig.set(
                cat_configs={
                    (Cat.action,): (None, True),
                    (Cat.character, Cat.name_n): (None, True),
                    (Cat.character, Cat.vibe): (None, False),
                    (Cat.character, Cat.affection): (None, False),
                    (Cat.character, Cat.trust): (None, False),
                    (Cat.character, Cat.frustration): (None, False),
                    (Cat.character, Cat.angry): (None, False),
                    (Cat.character, Cat.in_heat): (None, False),
                    (Cat.character, Cat.mood): (None, False),
                    (Cat.character, Cat.reason): (None, False),
                    (Cat.character, Cat.upper_n): (None, False),
                    (Cat.character, Cat.upper_state): (None, False),
                    (Cat.character, Cat.lower_n): (None, False),
                    (Cat.character, Cat.lower_state): (None, False),
                    (Cat.caps,): (None, True),
                    (Cat.hands,): (None, True),
                    (Cat.dresses,): (None, True),
                    (Cat.kimonos,): (None, True),
                    (Cat.outers,): (None, True),
                    (Cat.upper_cloths,): (None, True),
                    (Cat.lower_cloths,): (None, True),
                    (Cat.lingeries,): (expr_no_costumes, True),
                    (Cat.whole_lingeries,): (expr_no_costumes, True),
                    (Cat.upper_lingeries,): (expr_no_upper_costumes, True),
                    (Cat.lower_lingeries,): (expr_no_lower_costumes, True),
                    (Cat.socks,): (None, True),
                    (Cat.shoes,): (None, True),
                    (Cat.equipments,): (None, True),
                    (Cat.accessories,): (None, True),
                    (Cat.meta, Cat.time, Cat.day): (expr_outdoors, False),
                    (Cat.meta, Cat.time, Cat.night): (expr_outdoors, False),
                    (Cat.meta, Cat.location, Cat.indoors, Cat.type1): (None, True),
                    (Cat.meta, Cat.location, Cat.indoors, Cat.type2): (None, True),
                    (Cat.meta, Cat.location, Cat.indoors, Cat.type3): (None, False),
                    (Cat.meta, Cat.location, Cat.outdoors, Cat.type1): (None, True),
                    (Cat.meta, Cat.location, Cat.outdoors, Cat.type2): (None, True),
                    (Cat.meta, Cat.location, Cat.outdoors, Cat.type3): (None, False),
                    (Cat.meta, Cat.weather): (expr_outdoors, False),
                },
                sufficiency=Has((Cat.character, Cat.name_n)),
                request_cats={
                    Scr.action: [
                        (Cat.action,),
                    ],
                    Scr.fashion: [
                        (Cat.caps,),
                        (Cat.hands,),
                        (Cat.dresses,),
                        (Cat.kimonos,),
                        (Cat.outers,),
                        (Cat.upper_cloths,),
                        (Cat.lower_cloths,),
                        (Cat.lingeries,),
                        (Cat.whole_lingeries,),
                        (Cat.upper_lingeries,),
                        (Cat.lower_lingeries,),
                        (Cat.socks,),
                        (Cat.shoes,),
                        (Cat.equipments,),
                        (Cat.accessories,),
                    ],
                },
            ),
            Scr.action: ScreenConfig.set(
                cat_configs={
                    (Cat.action,): (None, True),
                    (Cat.character, Cat.name_n): (None, True),
                    (Cat.character, Cat.vibe): (None, False),
                    (Cat.character, Cat.affection): (None, False),
                    (Cat.character, Cat.trust): (None, False),
                    (Cat.character, Cat.frustration): (None, False),
                    (Cat.character, Cat.angry): (None, False),
                    (Cat.character, Cat.in_heat): (None, False),
                    (Cat.character, Cat.mood): (None, False),
                    (Cat.character, Cat.reason): (None, False),
                    (Cat.character, Cat.upper_n): (None, False),
                    (Cat.character, Cat.upper_state): (None, False),
                    (Cat.character, Cat.lower_n): (None, False),
                    (Cat.character, Cat.lower_state): (None, False),
                    (Cat.caps,): (None, True),
                    (Cat.hands,): (None, True),
                    (Cat.dresses,): (None, True),
                    (Cat.kimonos,): (None, True),
                    (Cat.outers,): (None, True),
                    (Cat.upper_cloths,): (None, True),
                    (Cat.lower_cloths,): (None, True),
                    (Cat.lingeries,): (expr_no_costumes, True),
                    (Cat.whole_lingeries,): (expr_no_costumes, True),
                    (Cat.upper_lingeries,): (expr_no_upper_costumes, True),
                    (Cat.lower_lingeries,): (expr_no_lower_costumes, True),
                    (Cat.socks,): (None, True),
                    (Cat.shoes,): (None, True),
                    (Cat.equipments,): (None, True),
                    (Cat.accessories,): (None, True),
                    (Cat.meta, Cat.time, Cat.day): (expr_outdoors, False),
                    (Cat.meta, Cat.time, Cat.night): (expr_outdoors, False),
                    (Cat.meta, Cat.location, Cat.indoors, Cat.type1): (None, True),
                    (Cat.meta, Cat.location, Cat.indoors, Cat.type2): (None, True),
                    (Cat.meta, Cat.location, Cat.indoors, Cat.type3): (None, False),
                    (Cat.meta, Cat.location, Cat.outdoors, Cat.type1): (None, True),
                    (Cat.meta, Cat.location, Cat.outdoors, Cat.type2): (None, True),
                    (Cat.meta, Cat.location, Cat.outdoors, Cat.type3): (None, False),
                    (Cat.meta, Cat.weather): (expr_outdoors, False),
                },
                sufficiency=Has((Cat.character, Cat.name_n)),
                request_cats={
                    Scr.main: [
                        (Cat.character, Cat.vibe),
                        (Cat.character, Cat.affection),
                        (Cat.character, Cat.trust),
                        (Cat.character, Cat.frustration),
                        (Cat.character, Cat.angry),
                        (Cat.character, Cat.in_heat),
                        (Cat.character, Cat.mood),
                        (Cat.character, Cat.reason),
                        (Cat.character, Cat.upper_n),
                        (Cat.character, Cat.upper_state),
                        (Cat.character, Cat.lower_n),
                        (Cat.character, Cat.lower_state),
                        (Cat.caps,),
                        (Cat.hands,),
                        (Cat.dresses,),
                        (Cat.kimonos,),
                        (Cat.outers,),
                        (Cat.upper_cloths,),
                        (Cat.lower_cloths,),
                        (Cat.lingeries,),
                        (Cat.whole_lingeries,),
                        (Cat.upper_lingeries,),
                        (Cat.lower_lingeries,),
                        (Cat.socks,),
                        (Cat.shoes,),
                        (Cat.equipments,),
                        (Cat.accessories,),
                        (Cat.meta, Cat.time, Cat.day),
                        (Cat.meta, Cat.time, Cat.night),
                        (Cat.meta, Cat.location, Cat.indoors, Cat.type1),
                        (Cat.meta, Cat.location, Cat.indoors, Cat.type2),
                        (Cat.meta, Cat.location, Cat.indoors, Cat.type3),
                        (Cat.meta, Cat.location, Cat.outdoors, Cat.type1),
                        (Cat.meta, Cat.location, Cat.outdoors, Cat.type2),
                        (Cat.meta, Cat.location, Cat.outdoors, Cat.type3),
                        (Cat.meta, Cat.weather),
                    ]
                },
                takeover_cats=[
                    (Cat.character, Cat.name_n),
                ],
            ),
            Scr.status: ScreenConfig.set(
                cat_configs={
                    (Cat.name_n,): (None, True),
                    (Cat.affection,): (None, True),
                    (Cat.trust,): (None, True),
                    (Cat.caps,): (None, True),
                    (Cat.hands,): (None, True),
                    (Cat.dresses,): (None, True),
                    (Cat.kimonos,): (None, True),
                    (Cat.outers,): (None, True),
                    (Cat.upper_cloths,): (None, True),
                    (Cat.lower_cloths,): (None, True),
                    (Cat.lingeries,): (expr_no_costumes, True),
                    (Cat.whole_lingeries,): (expr_no_costumes, True),
                    (Cat.upper_lingeries,): (expr_no_upper_costumes, True),
                    (Cat.lower_lingeries,): (expr_no_lower_costumes, True),
                    (Cat.socks,): (None, True),
                    (Cat.shoes,): (None, True),
                    (Cat.equipments,): (None, True),
                    (Cat.accessories,): (None, True),
                },
                sufficiency=Has((Cat.name_n,)),
            ),
            Scr.fashion: ScreenConfig.set(
                cat_configs={
                    (Cat.character, Cat.name_n): (None, True),
                    (Cat.caps,): (None, True),
                    (Cat.hands,): (None, True),
                    (Cat.dresses,): (None, True),
                    (Cat.kimonos,): (None, True),
                    (Cat.outers,): (None, True),
                    (Cat.upper_cloths,): (None, True),
                    (Cat.lower_cloths,): (None, True),
                    (Cat.lingeries,): (expr_no_costumes, True),
                    (Cat.whole_lingeries,): (expr_no_costumes, True),
                    (Cat.upper_lingeries,): (expr_no_upper_costumes, True),
                    (Cat.lower_lingeries,): (expr_no_lower_costumes, True),
                    (Cat.socks,): (None, True),
                    (Cat.shoes,): (None, True),
                    (Cat.equipments,): (None, True),
                    (Cat.accessories,): (None, True),
                },
                sufficiency=Has((Cat.character, Cat.name_n)),
                takeover_cats=[(Cat.character, Cat.name_n)],
            ),
        }
