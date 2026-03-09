import os
import sys
from dataclasses import asdict, is_dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import pyperclip

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from common.expr import Expr, FalseExpr, Has, TrueExpr  # noqa: E402
from common.functions import dump_json  # noqa: E402
from parser.interpreter.test_interpreter import EnhancedCategory, TestInterpreter  # noqa: E402
from parser.parser import Parser  # noqa: E402

CORRECT_RESULT = {
    "CASE 'strip'": {
        "InterpreterTest-1: 'strip xxx'": {
            "dataclass": [
                {
                    "screen_id": "strip",
                    "positive": [
                        {"path": ["ok1"], "tokens": [{"token": "OK1", "weight": 1.0}]},
                        {"path": ["ok2"], "tokens": [{"token": "OK2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "strip_common_pos", "weight": 1.0}]},
                    ],
                    "negative": [
                        {"path": ["ok1"], "tokens": [{"token": "ok1", "weight": 1.0}]},
                        {"path": ["ok2"], "tokens": [{"token": "ok2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "strip_common_neg", "weight": 1.0}]},
                    ],
                }
            ],
            "string": {"POS": "OK1,OK2,strip_common_pos", "NEG": "ok1,ok2,strip_common_neg"},
            "essentiality": True,
            "reports": [],
        }
    },
    "CASE 'dedupe'": {
        "InterpreterTest-1: 'dedupe xxx'": {
            "dataclass": [
                {
                    "screen_id": "dedupe",
                    "positive": [
                        {"path": ["map1"], "tokens": [{"token": "MAP1", "weight": 1.0}]},
                        {
                            "path": ["map2"],
                            "tokens": [
                                {"token": "dedupe", "weight": 2.5},
                                {"token": "MAP2", "weight": 1.0},
                            ],
                        },
                        {
                            "path": ["map3"],
                            "tokens": [
                                {"token": "MAP3'", "weight": 1.0},
                                {"token": "MAP3", "weight": 1.0},
                            ],
                        },
                        {"path": ["map4"], "tokens": [{"token": "MAP4", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "dedupe_common_pos", "weight": 1.0}]},
                    ],
                    "negative": [
                        {
                            "path": ["map1"],
                            "tokens": [
                                {"token": "dedupe", "weight": 0.15},
                                {"token": "map1", "weight": 1.0},
                            ],
                        },
                        {"path": ["map2"], "tokens": [{"token": "map2", "weight": 1.0}]},
                        {"path": ["map3"], "tokens": [{"token": "map3", "weight": 1.0}]},
                        {"path": ["map4"], "tokens": [{"token": "map4", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "dedupe_common_neg", "weight": 1.0}]},
                    ],
                }
            ],
            "string": {
                "POS": "MAP1,(dedupe:2.5),MAP2,MAP3',MAP3,MAP4,dedupe_common_pos",
                "NEG": "(dedupe:0.15),map1,map2,map3,map4,dedupe_common_neg",
            },
            "essentiality": True,
            "reports": [],
        }
    },
    "CASE 'dedupe2'": {
        "InterpreterTest-1: 'dedupe xxx'": {
            "dataclass": [
                {
                    "screen_id": "dedupe",
                    "positive": [
                        {"path": ["map5"], "tokens": [{"token": "MAP5", "weight": 1.0}]},
                        {"path": ["map1"], "tokens": [{"token": "MAP1", "weight": 1.0}]},
                        {
                            "path": ["map2"],
                            "tokens": [
                                {"token": "dedupe", "weight": 2.5},
                                {"token": "MAP2", "weight": 1.0},
                            ],
                        },
                        {
                            "path": ["map3"],
                            "tokens": [
                                {"token": "MAP3'", "weight": 1.0},
                                {"token": "MAP3", "weight": 1.0},
                            ],
                        },
                        {"path": ["map4"], "tokens": [{"token": "MAP4", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "dedupe_common_pos", "weight": 1.0}]},
                    ],
                    "negative": [
                        {
                            "path": ["map5"],
                            "tokens": [
                                {"token": "map5", "weight": 1.0},
                                {"token": "dedupe", "weight": 0.15},
                                {"token": "map5'", "weight": 1.0},
                            ],
                        },
                        {"path": ["map1"], "tokens": [{"token": "map1", "weight": 1.0}]},
                        {"path": ["map2"], "tokens": [{"token": "map2", "weight": 1.0}]},
                        {"path": ["map3"], "tokens": [{"token": "map3", "weight": 1.0}]},
                        {"path": ["map4"], "tokens": [{"token": "map4", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "dedupe_common_neg", "weight": 1.0}]},
                    ],
                }
            ],
            "string": {
                "POS": "MAP5,MAP1,(dedupe:2.5),MAP2,MAP3',MAP3,MAP4,dedupe_common_pos",
                "NEG": "map5,(dedupe:0.15),map5',map1,map2,map3,map4,dedupe_common_neg",
            },
            "essentiality": True,
            "reports": [],
        }
    },
    "CASE 'dedupe3'": {
        "InterpreterTest-1: 'dedupe xxx'": {
            "dataclass": [
                {
                    "screen_id": "dedupe",
                    "positive": [
                        {"path": ["map5"], "tokens": [{"token": "MAP5", "weight": 1.0}]},
                        {"path": ["map1"], "tokens": [{"token": "MAP1", "weight": 1.0}]},
                        {
                            "path": ["map2"],
                            "tokens": [
                                {"token": "dedupe", "weight": 2.5},
                                {"token": "MAP2", "weight": 1.0},
                            ],
                        },
                        {"path": ["map4"], "tokens": [{"token": "MAP4", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "dedupe_common_pos", "weight": 1.0}]},
                    ],
                    "negative": [
                        {
                            "path": ["map5"],
                            "tokens": [
                                {"token": "map5", "weight": 1.0},
                                {"token": "dedupe", "weight": 0.5},
                                {"token": "map5'", "weight": 1.0},
                            ],
                        },
                        {"path": ["map1"], "tokens": [{"token": "map1", "weight": 1.0}]},
                        {"path": ["map2"], "tokens": [{"token": "map2", "weight": 1.0}]},
                        {"path": ["map4"], "tokens": [{"token": "map4", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "dedupe_common_neg", "weight": 1.0}]},
                    ],
                }
            ],
            "string": {
                "POS": "MAP5,MAP1,(dedupe:2.5),MAP2,MAP4,dedupe_common_pos",
                "NEG": "map5,(dedupe:0.5),map5',map1,map2,map4,dedupe_common_neg",
            },
            "essentiality": True,
            "reports": [],
        }
    },
    "CASE 'dedupe4'": {
        "InterpreterTest-1: 'dedupe xxx'": {
            "dataclass": [
                {
                    "screen_id": "dedupe",
                    "positive": [
                        {"path": ["map5"], "tokens": [{"token": "MAP5", "weight": 1.0}]},
                        {"path": ["map1"], "tokens": [{"token": "MAP1", "weight": 1.0}]},
                        {
                            "path": ["map2"],
                            "tokens": [
                                {"token": "dedupe", "weight": 2.5},
                                {"token": "MAP2", "weight": 1.0},
                            ],
                        },
                        {"path": ["map4"], "tokens": [{"token": "MAP4", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "dedupe_common_pos", "weight": 1.0}]},
                    ],
                    "negative": [
                        {
                            "path": ["map5"],
                            "tokens": [
                                {"token": "map5", "weight": 1.0},
                                {"token": "dedupe", "weight": 0.5},
                                {"token": "map5'", "weight": 1.0},
                            ],
                        },
                        {"path": ["map1"], "tokens": [{"token": "map1", "weight": 1.0}]},
                        {"path": ["map2"], "tokens": [{"token": "map2", "weight": 1.0}]},
                        {"path": ["map4"], "tokens": [{"token": "map4", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "dedupe_common_neg", "weight": 1.0}]},
                    ],
                }
            ],
            "string": {
                "POS": "MAP5,MAP1,(dedupe:2.5),MAP2,MAP4,dedupe_common_pos",
                "NEG": "map5,(dedupe:0.5),map5',map1,map2,map4,dedupe_common_neg",
            },
            "essentiality": True,
            "reports": [],
        }
    },
    "CASE 'sort'": {
        "InterpreterTest-1: 'sort xxx'": {
            "dataclass": [
                {
                    "screen_id": "sort",
                    "positive": [
                        {"path": ["map3"], "tokens": [{"token": "MAP3", "weight": 1.0}]},
                        {"path": ["map2"], "tokens": [{"token": "MAP2", "weight": 1.0}]},
                        {"path": ["map4"], "tokens": [{"token": "MAP4", "weight": 1.0}]},
                        {"path": ["map1"], "tokens": [{"token": "MAP1", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "sort_common_pos", "weight": 1.0}]},
                    ],
                    "negative": [
                        {"path": ["map3"], "tokens": [{"token": "map3", "weight": 1.0}]},
                        {"path": ["map2"], "tokens": [{"token": "map2", "weight": 1.0}]},
                        {"path": ["map4"], "tokens": [{"token": "map4", "weight": 1.0}]},
                        {"path": ["map1"], "tokens": [{"token": "map1", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "sort_common_neg", "weight": 1.0}]},
                    ],
                }
            ],
            "string": {
                "POS": "MAP3,MAP2,MAP4,MAP1,sort_common_pos",
                "NEG": "map3,map2,map4,map1,sort_common_neg",
            },
            "essentiality": True,
            "reports": [],
        }
    },
    "CASE 'essential'": {
        "InterpreterTest-1: 'essential BD'": {
            "dataclass": [
                {
                    "screen_id": "essential",
                    "positive": [
                        {"path": ["notneed1"], "tokens": [{"token": "NOTNEED1", "weight": 1.0}]},
                        {"path": ["notneed2"], "tokens": [{"token": "NOTNEED2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "essential_common_pos", "weight": 1.0}]},
                    ],
                    "negative": [
                        {"path": ["notneed1"], "tokens": [{"token": "notneed1", "weight": 1.0}]},
                        {"path": ["notneed2"], "tokens": [{"token": "notneed2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "essential_common_neg", "weight": 1.0}]},
                    ],
                }
            ],
            "string": {
                "POS": "NOTNEED1,NOTNEED2,essential_common_pos",
                "NEG": "notneed1,notneed2,essential_common_neg",
            },
            "essentiality": False,
            "reports": [],
        },
        "InterpreterTest-2: 'essential ABD'": {
            "dataclass": [
                {
                    "screen_id": "essential",
                    "positive": [
                        {"path": ["need1"], "tokens": [{"token": "NEED1", "weight": 1.0}]},
                        {"path": ["notneed1"], "tokens": [{"token": "NOTNEED1", "weight": 1.0}]},
                        {"path": ["notneed2"], "tokens": [{"token": "NOTNEED2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "essential_common_pos", "weight": 1.0}]},
                    ],
                    "negative": [
                        {"path": ["need1"], "tokens": [{"token": "need1", "weight": 1.0}]},
                        {"path": ["notneed1"], "tokens": [{"token": "notneed1", "weight": 1.0}]},
                        {"path": ["notneed2"], "tokens": [{"token": "notneed2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "essential_common_neg", "weight": 1.0}]},
                    ],
                }
            ],
            "string": {
                "POS": "NEED1,NOTNEED1,NOTNEED2,essential_common_pos",
                "NEG": "need1,notneed1,notneed2,essential_common_neg",
            },
            "essentiality": False,
            "reports": [],
        },
        "InterpreterTest-3: 'essential BCD'": {
            "dataclass": [
                {
                    "screen_id": "essential",
                    "positive": [
                        {"path": ["need2"], "tokens": [{"token": "NEED2", "weight": 1.0}]},
                        {"path": ["notneed1"], "tokens": [{"token": "NOTNEED1", "weight": 1.0}]},
                        {"path": ["notneed2"], "tokens": [{"token": "NOTNEED2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "essential_common_pos", "weight": 1.0}]},
                    ],
                    "negative": [
                        {"path": ["need2"], "tokens": [{"token": "need2", "weight": 1.0}]},
                        {"path": ["notneed1"], "tokens": [{"token": "notneed1", "weight": 1.0}]},
                        {"path": ["notneed2"], "tokens": [{"token": "notneed2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "essential_common_neg", "weight": 1.0}]},
                    ],
                }
            ],
            "string": {
                "POS": "NEED2,NOTNEED1,NOTNEED2,essential_common_pos",
                "NEG": "need2,notneed1,notneed2,essential_common_neg",
            },
            "essentiality": False,
            "reports": [],
        },
        "InterpreterTest-4: 'essential BDE'": {
            "dataclass": [
                {
                    "screen_id": "essential",
                    "positive": [
                        {"path": ["need3"], "tokens": [{"token": "NEED3", "weight": 1.0}]},
                        {"path": ["notneed1"], "tokens": [{"token": "NOTNEED1", "weight": 1.0}]},
                        {"path": ["notneed2"], "tokens": [{"token": "NOTNEED2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "essential_common_pos", "weight": 1.0}]},
                    ],
                    "negative": [
                        {"path": ["need3"], "tokens": [{"token": "need3", "weight": 1.0}]},
                        {"path": ["notneed1"], "tokens": [{"token": "notneed1", "weight": 1.0}]},
                        {"path": ["notneed2"], "tokens": [{"token": "notneed2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "essential_common_neg", "weight": 1.0}]},
                    ],
                }
            ],
            "string": {
                "POS": "NEED3,NOTNEED1,NOTNEED2,essential_common_pos",
                "NEG": "need3,notneed1,notneed2,essential_common_neg",
            },
            "essentiality": False,
            "reports": [],
        },
        "InterpreterTest-5: 'essential ABCDE'": {
            "dataclass": [
                {
                    "screen_id": "essential",
                    "positive": [
                        {"path": ["need1"], "tokens": [{"token": "NEED1", "weight": 1.0}]},
                        {"path": ["need2"], "tokens": [{"token": "NEED2", "weight": 1.0}]},
                        {"path": ["need3"], "tokens": [{"token": "NEED3", "weight": 1.0}]},
                        {"path": ["notneed1"], "tokens": [{"token": "NOTNEED1", "weight": 1.0}]},
                        {"path": ["notneed2"], "tokens": [{"token": "NOTNEED2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "essential_common_pos", "weight": 1.0}]},
                    ],
                    "negative": [
                        {"path": ["need1"], "tokens": [{"token": "need1", "weight": 1.0}]},
                        {"path": ["need2"], "tokens": [{"token": "need2", "weight": 1.0}]},
                        {"path": ["need3"], "tokens": [{"token": "need3", "weight": 1.0}]},
                        {"path": ["notneed1"], "tokens": [{"token": "notneed1", "weight": 1.0}]},
                        {"path": ["notneed2"], "tokens": [{"token": "notneed2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "essential_common_neg", "weight": 1.0}]},
                    ],
                }
            ],
            "string": {
                "POS": "NEED1,NEED2,NEED3,NOTNEED1,NOTNEED2,essential_common_pos",
                "NEG": "need1,need2,need3,notneed1,notneed2,essential_common_neg",
            },
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-6: 'essential ABXDE'": {
            "dataclass": [
                {
                    "screen_id": "essential",
                    "positive": [
                        {"path": ["need1"], "tokens": [{"token": "NEED1", "weight": 1.0}]},
                        {"path": ["need2"], "tokens": [{"token": "DEFAULT", "weight": 1.0}]},
                        {"path": ["need3"], "tokens": [{"token": "NEED3", "weight": 1.0}]},
                        {"path": ["notneed1"], "tokens": [{"token": "NOTNEED1", "weight": 1.0}]},
                        {"path": ["notneed2"], "tokens": [{"token": "NOTNEED2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "essential_common_pos", "weight": 1.0}]},
                    ],
                    "negative": [
                        {"path": ["need1"], "tokens": [{"token": "need1", "weight": 1.0}]},
                        {"path": ["need2"], "tokens": [{"token": "default", "weight": 1.0}]},
                        {"path": ["need3"], "tokens": [{"token": "need3", "weight": 1.0}]},
                        {"path": ["notneed1"], "tokens": [{"token": "notneed1", "weight": 1.0}]},
                        {"path": ["notneed2"], "tokens": [{"token": "notneed2", "weight": 1.0}]},
                        {"path": [], "tokens": [{"token": "essential_common_neg", "weight": 1.0}]},
                    ],
                }
            ],
            "string": {
                "POS": "NEED1,DEFAULT,NEED3,NOTNEED1,NOTNEED2,essential_common_pos",
                "NEG": "need1,default,need3,notneed1,notneed2,essential_common_neg",
            },
            "essentiality": True,
            "reports": [
                {
                    "matched": "X",
                    "pattern": "(C|X)",
                    "capturegrp": 0,
                    "screen_id": "essential",
                    "paths": [["need2"]],
                }
            ],
        },
    },
    "CASE 'expr1'": {
        "InterpreterTest-1: 'expr1 room city'": {
            "dataclass": [{"screen_id": "expr1", "positive": [], "negative": []}],
            "string": {"POS": "", "NEG": ""},
            "essentiality": False,
            "reports": [],
        },
        "InterpreterTest-2: 'expr1 city room'": {
            "dataclass": [{"screen_id": "expr1", "positive": [], "negative": []}],
            "string": {"POS": "", "NEG": ""},
            "essentiality": False,
            "reports": [],
        },
        "InterpreterTest-3: 'expr1 room sunny'": {
            "dataclass": [
                {
                    "screen_id": "expr1",
                    "positive": [
                        {
                            "path": ["location", "indoors"],
                            "tokens": [{"token": "room", "weight": 1.0}],
                        }
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "room", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-4: 'expr1 city sunny'": {
            "dataclass": [
                {
                    "screen_id": "expr1",
                    "positive": [
                        {
                            "path": ["location", "outdoors"],
                            "tokens": [{"token": "city", "weight": 1.0}],
                        },
                        {"path": ["weather"], "tokens": [{"token": "sunny", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "city,sunny", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
    },
    "CASE 'expr2'": {
        "InterpreterTest-1: 'expr2 checkHas'": {
            "dataclass": [{"screen_id": "expr2", "positive": [], "negative": []}],
            "string": {"POS": "", "NEG": ""},
            "essentiality": False,
            "reports": [],
        },
        "InterpreterTest-2: 'expr2 P checkHas'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["checkHas"], "tokens": [{"token": "checkHas", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,checkHas", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-3: 'expr2 PQR checkHas'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {"path": ["r"], "tokens": [{"token": "R", "weight": 1.0}]},
                        {"path": ["checkHas"], "tokens": [{"token": "checkHas", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,Q,R,checkHas", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-4: 'expr2 QR checkHas'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {"path": ["r"], "tokens": [{"token": "R", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "Q,R", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-5: 'expr2 checkAnd'": {
            "dataclass": [{"screen_id": "expr2", "positive": [], "negative": []}],
            "string": {"POS": "", "NEG": ""},
            "essentiality": False,
            "reports": [],
        },
        "InterpreterTest-6: 'expr2 P checkAnd'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [{"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]}],
                    "negative": [],
                }
            ],
            "string": {"POS": "P", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-7: 'expr2 Q checkAnd'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [{"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]}],
                    "negative": [],
                }
            ],
            "string": {"POS": "Q", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-8: 'expr2 PQ checkAnd'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {"path": ["checkAnd"], "tokens": [{"token": "checkAnd", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,Q,checkAnd", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-9: 'expr2 PQR checkAnd'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {"path": ["r"], "tokens": [{"token": "R", "weight": 1.0}]},
                        {"path": ["checkAnd"], "tokens": [{"token": "checkAnd", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,Q,R,checkAnd", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-10: 'expr2 checkOr'": {
            "dataclass": [{"screen_id": "expr2", "positive": [], "negative": []}],
            "string": {"POS": "", "NEG": ""},
            "essentiality": False,
            "reports": [],
        },
        "InterpreterTest-11: 'expr2 P checkOr'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["checkOr"], "tokens": [{"token": "checkOr", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,checkOr", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-12: 'expr2 Q checkOr'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {"path": ["checkOr"], "tokens": [{"token": "checkOr", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "Q,checkOr", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-13: 'expr2 PQ checkOr'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {"path": ["checkOr"], "tokens": [{"token": "checkOr", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,Q,checkOr", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-14: 'expr2 PQR checkOr'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {"path": ["r"], "tokens": [{"token": "R", "weight": 1.0}]},
                        {"path": ["checkOr"], "tokens": [{"token": "checkOr", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,Q,R,checkOr", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-15: 'expr2 checkNot'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["checkNot"], "tokens": [{"token": "checkNot", "weight": 1.0}]}
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "checkNot", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-16: 'expr2 P checkNot'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [{"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]}],
                    "negative": [],
                }
            ],
            "string": {"POS": "P", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-17: 'expr2 PQR checkNot'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {"path": ["r"], "tokens": [{"token": "R", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,Q,R", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-18: 'expr2 QR checkNot'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {"path": ["r"], "tokens": [{"token": "R", "weight": 1.0}]},
                        {"path": ["checkNot"], "tokens": [{"token": "checkNot", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "Q,R,checkNot", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-19: 'expr2 QR checkComplex'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {"path": ["r"], "tokens": [{"token": "R", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "Q,R", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-20: 'expr2 PQ checkComplex'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {
                            "path": ["checkComplex"],
                            "tokens": [{"token": "checkComplex", "weight": 1.0}],
                        },
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,Q,checkComplex", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-21: 'expr2 PR checkComplex'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["r"], "tokens": [{"token": "R", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,R", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-22: 'expr2 checkTrue'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["checkTrue"], "tokens": [{"token": "checkTrue", "weight": 1.0}]}
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "checkTrue", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-23: 'expr2 PQR checkTrue'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {"path": ["r"], "tokens": [{"token": "R", "weight": 1.0}]},
                        {"path": ["checkTrue"], "tokens": [{"token": "checkTrue", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,Q,R,checkTrue", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-24: 'expr2 checkFalse'": {
            "dataclass": [{"screen_id": "expr2", "positive": [], "negative": []}],
            "string": {"POS": "", "NEG": ""},
            "essentiality": False,
            "reports": [],
        },
        "InterpreterTest-25: 'expr2 PQR checkFalse'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {"path": ["r"], "tokens": [{"token": "R", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,Q,R", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-26: 'expr2 checkNone'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["checkNone"], "tokens": [{"token": "checkNone", "weight": 1.0}]}
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "checkNone", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-27: 'expr2 PQR checkNone'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                        {"path": ["r"], "tokens": [{"token": "R", "weight": 1.0}]},
                        {"path": ["checkNone"], "tokens": [{"token": "checkNone", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,Q,R,checkNone", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
    },
    "CASE 'essential & expr'": {
        "InterpreterTest-1: 'expr2'": {
            "dataclass": [{"screen_id": "expr2", "positive": [], "negative": []}],
            "string": {"POS": "", "NEG": ""},
            "essentiality": False,
            "reports": [],
        },
        "InterpreterTest-2: 'expr2 P'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [{"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]}],
                    "negative": [],
                }
            ],
            "string": {"POS": "P", "NEG": ""},
            "essentiality": False,
            "reports": [],
        },
        "InterpreterTest-3: 'expr2 Q'": {
            "dataclass": [{"screen_id": "expr2", "positive": [], "negative": []}],
            "string": {"POS": "", "NEG": ""},
            "essentiality": False,
            "reports": [],
        },
        "InterpreterTest-4: 'expr2 PQ'": {
            "dataclass": [
                {
                    "screen_id": "expr2",
                    "positive": [
                        {"path": ["p"], "tokens": [{"token": "P", "weight": 1.0}]},
                        {"path": ["q"], "tokens": [{"token": "Q", "weight": 1.0}]},
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "P,Q", "NEG": ""},
            "essentiality": True,
            "reports": [],
        },
    },
    "CASE 'report'": {
        "InterpreterTest-1: 'report rules_maps:MAPs;rules_maps:nMAPs;rules_maps:None;'": {
            "dataclass": [
                {
                    "screen_id": "report",
                    "positive": [
                        {"path": ["rules_maps"], "tokens": [{"token": "maps", "weight": 1.0}]}
                    ],
                    "negative": [
                        {"path": ["rules_maps"], "tokens": [{"token": "neg_maps", "weight": 1.0}]}
                    ],
                }
            ],
            "string": {"POS": "maps", "NEG": "neg_maps"},
            "essentiality": True,
            "reports": [
                {
                    "matched": "None",
                    "pattern": "rules_maps:(.+?);",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["rules_maps"]],
                }
            ],
        },
        "InterpreterTest-2: 'report rules_ranges:RANGEs;rules_ranges:nRANGEs;rules_ranges:None;'": {
            "dataclass": [
                {
                    "screen_id": "report",
                    "positive": [
                        {"path": ["rules_ranges"], "tokens": [{"token": "ranges", "weight": 1.0}]}
                    ],
                    "negative": [
                        {
                            "path": ["rules_ranges"],
                            "tokens": [{"token": "neg_ranges", "weight": 1.0}],
                        }
                    ],
                }
            ],
            "string": {"POS": "ranges", "NEG": "neg_ranges"},
            "essentiality": True,
            "reports": [
                {
                    "matched": "None",
                    "pattern": "rules_ranges:(.+?);",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["rules_ranges"]],
                }
            ],
        },
        "InterpreterTest-3: 'report rules_intervals:5;rules_intervals:-5;rules_intervals:100;'": {
            "dataclass": [
                {
                    "screen_id": "report",
                    "positive": [
                        {
                            "path": ["rules_intervals"],
                            "tokens": [{"token": "intervals", "weight": 1.0}],
                        }
                    ],
                    "negative": [
                        {
                            "path": ["rules_intervals"],
                            "tokens": [{"token": "neg_intervals", "weight": 1.0}],
                        }
                    ],
                }
            ],
            "string": {"POS": "intervals", "NEG": "neg_intervals"},
            "essentiality": True,
            "reports": [
                {
                    "matched": "100",
                    "pattern": "rules_intervals:(.+?);",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["rules_intervals"]],
                }
            ],
        },
        "InterpreterTest-4: 'report recurses:[REC1];recurses:[REC2];recurses:[REC3];'": {
            "dataclass": [
                {
                    "screen_id": "report",
                    "positive": [
                        {
                            "path": ["recurses", "recurses_parts_1"],
                            "tokens": [{"token": "recurses1", "weight": 1.0}],
                        }
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "recurses1", "NEG": ""},
            "essentiality": True,
            "reports": [
                {
                    "matched": "REC2",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["recurses", "recurses_parts_1"]],
                },
                {
                    "matched": "REC3",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["recurses", "recurses_parts_1"]],
                },
            ],
        },
        "InterpreterTest-5: 'report recurses:[{REC1}];recurses:[{REC2}];recurses:[{REC3}];'": {
            "dataclass": [
                {
                    "screen_id": "report",
                    "positive": [
                        {
                            "path": ["recurses", "recurses_parts_2", "recurses_parts_2'"],
                            "tokens": [{"token": "recurses2", "weight": 1.0}],
                        }
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "recurses2", "NEG": ""},
            "essentiality": True,
            "reports": [
                {
                    "matched": "{REC1}",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["recurses", "recurses_parts_1"]],
                },
                {
                    "matched": "REC1",
                    "pattern": "\\{([^\\{\\}]+?)\\}",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["recurses", "recurses_parts_2", "recurses_parts_2'"]],
                },
                {
                    "matched": "{REC2}",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["recurses", "recurses_parts_1"]],
                },
                {
                    "matched": "{REC3}",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["recurses", "recurses_parts_1"]],
                },
                {
                    "matched": "REC3",
                    "pattern": "\\{([^\\{\\}]+?)\\}",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["recurses", "recurses_parts_2", "recurses_parts_2'"]],
                },
            ],
        },
        "InterpreterTest-6: 'report recurses:[{(REC1)}];recurses:[{(REC2)}];recurses:[{(REC3)}];'": {  # noqa: E501
            "dataclass": [
                {
                    "screen_id": "report",
                    "positive": [
                        {
                            "path": [
                                "recurses",
                                "recurses_parts_3",
                                "recurses_parts_3'",
                                "recurses_parts_3''",
                            ],
                            "tokens": [{"token": "recurses3", "weight": 1.0}],
                        }
                    ],
                    "negative": [],
                }
            ],
            "string": {"POS": "recurses3", "NEG": ""},
            "essentiality": True,
            "reports": [
                {
                    "matched": "{(REC1)}",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["recurses", "recurses_parts_1"]],
                },
                {
                    "matched": "(REC1)",
                    "pattern": "\\{([^\\{\\}]+?)\\}",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["recurses", "recurses_parts_2", "recurses_parts_2'"]],
                },
                {
                    "matched": "REC1",
                    "pattern": "\\(([^\\(\\)]+?)\\)",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [
                        ["recurses", "recurses_parts_3", "recurses_parts_3'", "recurses_parts_3''"]
                    ],
                },
                {
                    "matched": "{(REC2)}",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["recurses", "recurses_parts_1"]],
                },
                {
                    "matched": "(REC2)",
                    "pattern": "\\{([^\\{\\}]+?)\\}",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["recurses", "recurses_parts_2", "recurses_parts_2'"]],
                },
                {
                    "matched": "REC2",
                    "pattern": "\\(([^\\(\\)]+?)\\)",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [
                        ["recurses", "recurses_parts_3", "recurses_parts_3'", "recurses_parts_3''"]
                    ],
                },
                {
                    "matched": "{(REC3)}",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["recurses", "recurses_parts_1"]],
                },
                {
                    "matched": "(REC3)",
                    "pattern": "\\{([^\\{\\}]+?)\\}",
                    "capturegrp": 1,
                    "screen_id": "report",
                    "paths": [["recurses", "recurses_parts_2", "recurses_parts_2'"]],
                },
            ],
        },
        "InterpreterTest-7: 'report no-report_maps:MAPs;no-report_maps:nMAPs;no-report_maps:None;'": {  # noqa: E501
            "dataclass": [
                {
                    "screen_id": "report",
                    "positive": [
                        {"path": ["no-report_maps"], "tokens": [{"token": "maps", "weight": 1.0}]}
                    ],
                    "negative": [
                        {
                            "path": ["no-report_maps"],
                            "tokens": [{"token": "neg_maps", "weight": 1.0}],
                        }
                    ],
                }
            ],
            "string": {"POS": "maps", "NEG": "neg_maps"},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-8: 'report no-report_ranges:RANGEs;no-report_ranges:nRANGEs;no-report_ranges:None;'": {  # noqa: E501
            "dataclass": [
                {
                    "screen_id": "report",
                    "positive": [
                        {
                            "path": ["no-report_ranges"],
                            "tokens": [{"token": "ranges", "weight": 1.0}],
                        }
                    ],
                    "negative": [
                        {
                            "path": ["no-report_ranges"],
                            "tokens": [{"token": "neg_ranges", "weight": 1.0}],
                        }
                    ],
                }
            ],
            "string": {"POS": "ranges", "NEG": "neg_ranges"},
            "essentiality": True,
            "reports": [],
        },
        "InterpreterTest-9: 'report no-report_intervals:5;no-report_intervals:-5;no-report_intervals:100;'": {  # noqa: E501
            "dataclass": [
                {
                    "screen_id": "report",
                    "positive": [
                        {
                            "path": ["no-report_intervals"],
                            "tokens": [{"token": "intervals", "weight": 1.0}],
                        }
                    ],
                    "negative": [
                        {
                            "path": ["no-report_intervals"],
                            "tokens": [{"token": "neg_intervals", "weight": 1.0}],
                        }
                    ],
                }
            ],
            "string": {"POS": "intervals", "NEG": "neg_intervals"},
            "essentiality": True,
            "reports": [],
        },
    },
}


def dict_diff(result: dict, correct: dict) -> dict[str, tuple[dict, dict]]:
    diff = {}
    all_keys = result.keys() | correct.keys()

    for k in all_keys:
        v1 = result.get(k)
        v2 = correct.get(k)
        if v1 != v2:
            diff[k] = ({"result": v1}, {"correct": v2})

    return diff


class KeyName(StrEnum):
    yamlpath = "yamlpath"
    texts = "texts"
    screen_id = "screen_id"
    enhanced_category_list = "enhanced_category_list"
    essential = "essential"


class InterpreterDebugger(Parser):
    def __init__(self):
        super().__init__(None, None)

    def debug_texts(
        self,
        texts: list[str],
        screen_id: str = None,
        encats: list[EnhancedCategory] = None,
        essential: Expr = None,
        with_texts: bool = True,
    ) -> dict[str, dict[str, Any]]:
        """
        展開中 yaml について texts 内のテキストを順に適用する\n
        TestInterpreter と紐づく YAML を展開中の場合に限りカテゴリーリストの指定を行える
        """
        if self.interpreter is None:
            raise Exception("Member 'interpreter' is None.")

        yamlname = self.interpreter.prompter.yamlpath.name.replace(".yaml", "")
        result: dict[str, dict[str, Any] | str] = {}
        for i, text in enumerate(texts):
            try:
                if (
                    isinstance(self.interpreter, TestInterpreter)
                    and screen_id is not None
                    and encats is not None
                ):
                    self.interpreter.restore_enhanced_category_list(screen_id, encats, essential)
                self.crnt_prompt, reports = self.interpreter.make_prompt(text)
                major = f"{yamlname}-{i + 1}: '{text}'" if with_texts else f"{yamlname}-{i + 1}"
                posneg = self.make_prompt_strs()
                if posneg is None:
                    pos = ""
                    neg = ""
                else:
                    pos, neg = posneg
                result[major] = {
                    "dataclass": (self.crnt_prompt,),
                    "string": {"POS": pos, "NEG": neg},
                    "essentiality": self.interpreter.check_essentiality_of(self.crnt_prompt),
                    "reports": reports,
                }
            except Exception as e:
                raise Exception(f"Error with '{text}'") from e
        return result

    def debug_cases(
        self,
        testcases: dict[str, dict[str, str | list | Expr]],
        with_texts: bool = True,
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """
        cases の Path の yaml を毎度展開し, それに紐づくテキストを順に適用する\n
        最も外側の str はパス重複解決のためのラベル
        """
        result: dict[str, dict[str, dict[str, Any]]] = {}
        for id, testcase in testcases.items():
            result_by_texts = {}
            texts = []
            screen_id = None
            encats = None
            essential = None
            for key, val in testcase.items():
                if key == KeyName.yamlpath:
                    yamlpath = val
                elif key == KeyName.texts:
                    texts = val
                elif key == KeyName.screen_id:
                    screen_id = val
                elif key == KeyName.enhanced_category_list:
                    encats = val
                elif key == KeyName.essential:
                    essential = val
            try:
                self.switch_interpreter(Path(yamlpath))
                result_by_texts = self.debug_texts(
                    texts=texts,
                    screen_id=screen_id,
                    encats=encats,
                    essential=essential,
                    with_texts=with_texts,
                )
            except Exception as e:
                raise Exception(f"Error on '{key}'") from e
            result[f"CASE '{id}'"] = result_by_texts
        return result

    def debug_clipboard(self) -> dict[str, dict[str, str]]:
        """
        展開中 yaml について現在のクリップボードのテキストを適用する
        """
        clipboard = pyperclip.paste()
        return self.debug_texts([clipboard], False)


def normalize(obj):
    if is_dataclass(obj):
        return normalize(asdict(obj))
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize(i) for i in obj]
    if isinstance(obj, tuple):
        return [normalize(i) for i in obj]
    if isinstance(obj, set):
        return sorted([normalize(i) for i in obj])

    return obj


def make_testcase(
    yamlpath: Path,
    texts: list[str],
    screen_id: str,
    encats: list[EnhancedCategory],
    essential: Expr,
):
    return {
        KeyName.yamlpath: yamlpath,
        KeyName.texts: texts,
        KeyName.screen_id: screen_id,
        KeyName.enhanced_category_list: encats,
        KeyName.essential: essential,
    }


def print_result(
    result: dict[str, dict[str, dict[str, Any]]], correct: dict[str, dict[str, dict[str, Any]]]
) -> None:
    normalized_result: dict[str, dict[str, dict[str, Any]]] = {}
    for key, test_result in result.items():
        normalized_result[key] = normalize(test_result)

    dump_json(normalized_result, "debug")
    print("---------------------------------------------------------------------------")
    for key, test_result in normalized_result.items():
        correct_result = correct.get(key)
        if correct_result is None:
            print(f"NEW - {key}")
        else:
            if test_result == correct_result:
                print(f"OK  - {key}")
                for key, val in test_result.items():
                    dump_json(val.get("string"), key)
            else:
                print(f"NG  - {key}")
                dump_json(dict_diff(test_result, correct_result))


def debug_interpreter() -> None:
    debugger = InterpreterDebugger()
    result = debugger.debug_cases(
        {
            "strip": make_testcase(
                yamlpath="yamls/testyamls/InterpreterTest.yaml",
                texts=["strip xxx"],
                screen_id="strip",
                encats=[
                    (("ok1",), None, True),
                    (("ok2",), None, True),
                ],
                essential=None,
            ),
            "dedupe": make_testcase(
                yamlpath="yamls/testyamls/InterpreterTest.yaml",
                texts=["dedupe xxx"],
                screen_id="dedupe",
                encats=[
                    (("map1",), None, True),
                    (("map2",), None, True),
                    (("map3",), None, True),
                    (("map4",), None, True),
                ],
                essential=None,
            ),
            "dedupe2": make_testcase(
                yamlpath="yamls/testyamls/InterpreterTest.yaml",
                texts=["dedupe xxx"],
                screen_id="dedupe",
                encats=[
                    (("map5",), None, True),
                    (("map1",), None, True),
                    (("map2",), None, True),
                    (("map3",), None, True),
                    (("map4",), None, True),
                ],
                essential=None,
            ),
            "dedupe3": make_testcase(
                yamlpath="yamls/testyamls/InterpreterTest.yaml",
                texts=["dedupe xxx"],
                screen_id="dedupe",
                encats=[
                    (("map5",), None, True),
                    (("map1",), None, True),
                    (("map2",), None, True),
                    (("map4",), None, True),
                ],
                essential=None,
            ),
            "dedupe4": make_testcase(
                yamlpath="yamls/testyamls/InterpreterTest.yaml",
                texts=["dedupe xxx"],
                screen_id="dedupe",
                encats=[
                    (("map5",), None, True),
                    (("map1",), None, True),
                    (("dummy"), None, True),
                    (("map2",), None, True),
                    (("map4",), None, True),
                ],
                essential=None,
            ),
            "sort": make_testcase(
                yamlpath="yamls/testyamls/InterpreterTest.yaml",
                texts=["sort xxx"],
                screen_id="sort",
                encats=[
                    (("map3",), None, True),
                    (("map2",), None, True),
                    (("map4",), None, True),
                    (("map1",), None, True),
                ],
                essential=None,
            ),
            "essential": make_testcase(
                yamlpath="yamls/testyamls/InterpreterTest.yaml",
                texts=[
                    "essential BD",
                    "essential ABD",
                    "essential BCD",
                    "essential BDE",
                    "essential ABCDE",
                    "essential ABXDE",  # default で満たす場合
                ],
                screen_id="essential",
                encats=[
                    (("need1",), None, True),
                    (("need2",), None, True),
                    (("need3",), None, True),
                    (("notneed1",), None, True),
                    (("notneed2",), None, True),
                ],
                essential=Has(("need1",)) & Has(("need2",)) & Has(("need3",)),
            ),
            "expr1": make_testcase(
                yamlpath="yamls/testyamls/InterpreterTest.yaml",
                texts=[
                    "expr1 room city",
                    "expr1 city room",
                    "expr1 room sunny",
                    "expr1 city sunny",
                ],
                screen_id="expr1",
                encats=[
                    (("location", "outdoors"), ~Has(("location", "indoors")), True),
                    (("location", "indoors"), ~Has(("location", "outdoors")), True),
                    (
                        ("weather",),
                        Has(("location", "outdoors")) | ~Has(("location", "indoors")),
                        True,
                    ),
                ],
                essential=None,
            ),
            "expr2": make_testcase(
                yamlpath="yamls/testyamls/InterpreterTest.yaml",
                texts=[
                    "expr2 checkHas",
                    "expr2 P checkHas",
                    "expr2 PQR checkHas",
                    "expr2 QR checkHas",
                    "expr2 checkAnd",
                    "expr2 P checkAnd",
                    "expr2 Q checkAnd",
                    "expr2 PQ checkAnd",
                    "expr2 PQR checkAnd",
                    "expr2 checkOr",
                    "expr2 P checkOr",
                    "expr2 Q checkOr",
                    "expr2 PQ checkOr",
                    "expr2 PQR checkOr",
                    "expr2 checkNot",
                    "expr2 P checkNot",
                    "expr2 PQR checkNot",
                    "expr2 QR checkNot",
                    "expr2 QR checkComplex",
                    "expr2 PQ checkComplex",
                    "expr2 PR checkComplex",
                    "expr2 checkTrue",
                    "expr2 PQR checkTrue",
                    "expr2 checkFalse",
                    "expr2 PQR checkFalse",
                    "expr2 checkNone",
                    "expr2 PQR checkNone",
                ],
                screen_id="expr2",
                encats=[
                    (("p",), TrueExpr(), True),
                    (("q",), TrueExpr(), True),
                    (("r",), TrueExpr(), True),
                    (("checkHas",), Has(("p",)), True),  # 単項
                    (("checkAnd",), Has(("p",)) & Has(("q",)), True),  # And
                    (("checkOr",), Has(("p",)) | Has(("q",)), True),  # Or
                    (("checkNot",), ~Has(("p",)), True),  # Not
                    (("checkComplex",), Has(("p",)) & (Has(("q",)) | ~Has(("r",))), True),  # 複合
                    (("checkTrue",), TrueExpr(), True),  # 恒真
                    (("checkFalse",), FalseExpr(), True),  # 恒偽
                    (("checkNone",), None, True),  # None = 恒真
                ],
                essential=None,
            ),
            "essential & expr": make_testcase(
                yamlpath="yamls/testyamls/InterpreterTest.yaml",
                texts=[
                    "expr2",  # ("q",) がないので False
                    "expr2 P",  # ("p",) はあるが ("q",) がないので False
                    "expr2 Q",  # ("p",) がないので ("q",) も適用されず False
                    "expr2 PQ",  # ("p",) があり ("q",) が適用されるので True
                ],
                screen_id="expr2",
                encats=[
                    (("p",), TrueExpr(), True),
                    (("q",), Has(("p",)), True),
                ],
                essential=Has(("q",)),
            ),
            "report": make_testcase(
                yamlpath="yamls/testyamls/InterpreterTest.yaml",
                texts=[
                    "report rules_maps:MAPs;rules_maps:nMAPs;rules_maps:None;",
                    "report rules_ranges:RANGEs;rules_ranges:nRANGEs;rules_ranges:None;",
                    "report rules_intervals:5;rules_intervals:-5;rules_intervals:100;",
                    "report recurses:[REC1];recurses:[REC2];recurses:[REC3];",
                    "report recurses:[{REC1}];recurses:[{REC2}];recurses:[{REC3}];",
                    "report recurses:[{(REC1)}];recurses:[{(REC2)}];recurses:[{(REC3)}];",
                    "report no-report_maps:MAPs;no-report_maps:nMAPs;no-report_maps:None;",  # noqa: E501
                    "report no-report_ranges:RANGEs;no-report_ranges:nRANGEs;no-report_ranges:None;",  # noqa: E501
                    "report no-report_intervals:5;no-report_intervals:-5;no-report_intervals:100;",  # noqa: E501
                ],
                screen_id="report",
                encats=[
                    (("rules_maps",), TrueExpr(), True),  # maps と neg 有効時
                    (("rules_ranges",), TrueExpr(), True),  # ranges と neg 有効時
                    (("rules_intervals",), TrueExpr(), True),  # interval と neg 有効時
                    (("recurses", "recurses_parts_1"), TrueExpr(), True),
                    (("recurses", "recurses_parts_2", "recurses_parts_2'"), TrueExpr(), True),
                    (
                        ("recurses", "recurses_parts_3", "recurses_parts_3'", "recurses_parts_3''"),
                        TrueExpr(),
                        True,
                    ),
                    (("no-report_maps",), TrueExpr(), False),  # maps, レポートしない
                    (("no-report_ranges",), TrueExpr(), False),  # ranges, レポートしない
                    (("no-report_intervals",), TrueExpr(), False),  # interval, レポートしない
                ],
                essential=None,
            ),
        }
    )
    print_result(result, CORRECT_RESULT)
