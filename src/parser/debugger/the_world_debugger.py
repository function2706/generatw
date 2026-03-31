import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from parser.debugger.interpreter_debugger import (  # noqa: E402
    InterpreterDebugger,
    KeyName,
    print_result,
)

CORRECT_RESULT = {
    "CASE 'main'": {
        "The World-1": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "chen", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "angry"],
                            "tokens": [{"token": "jitome", "weight": 1.0}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [{"token": "in heat", "weight": 0.9}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "chen,looking at viewer,blush,jitome,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:0.9),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-2": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        }
                    ],
                    "negative": [
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        }
                    ],
                }
            ],
            "string": {
                "POS": "best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": False,
            "reports": [],
        },
        "The World-3": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "chen", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "angry"],
                            "tokens": [{"token": "jitome", "weight": 1.0}],
                        },
                        {
                            "path": ["meta", "location", "indoors", "type1"],
                            "tokens": [{"token": "room", "weight": 1.0}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [{"token": "in heat", "weight": 0.9}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "chen,looking at viewer,blush,jitome,room,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:0.9),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-4": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "chen", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "angry"],
                            "tokens": [{"token": "jitome", "weight": 1.0}],
                        },
                        {
                            "path": ["meta", "time", "day"],
                            "tokens": [{"token": "noon", "weight": 1.0}],
                        },
                        {
                            "path": ["meta", "location", "outdoors", "type1"],
                            "tokens": [{"token": "path", "weight": 1.0}],
                        },
                        {
                            "path": ["meta", "weather"],
                            "tokens": [{"token": "sunny", "weight": 1.0}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [{"token": "in heat", "weight": 0.9}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "chen,looking at viewer,blush,jitome,noon,path,sunny,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:0.9),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-5": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "angry"],
                            "tokens": [{"token": "jitome", "weight": 1.0}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [{"token": "in heat", "weight": 0.9}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "looking at viewer,blush,jitome,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:0.9),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": False,
            "reports": [
                {
                    "matched": "？",
                    "pattern": "^(.+?)\\s*(?:（[^）]+）)?\\s*\\(好感度",
                    "capturegrp": 1,
                    "screen_id": "main",
                    "paths": [["character", "name"]],
                },
                {
                    "matched": "中の道",
                    "pattern": "(.+?)\\s+清潔度:",
                    "capturegrp": 1,
                    "screen_id": "main",
                    "paths": [
                        ["meta", "location", "indoors", "type1"],
                        ["meta", "location", "outdoors", "type1"],
                    ],
                },
            ],
        },
    },
    "CASE 'status'": {
        "The World-1": {
            "dataclass": [
                {
                    "screen_id": "status",
                    "positive": [
                        {"path": ["name"], "tokens": [{"token": "chen", "weight": 1.0}]},
                        {
                            "path": ["affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {"path": ["upper_cloths"], "tokens": [{"token": "blouse", "weight": 1.0}]},
                        {"path": ["lower_cloths"], "tokens": [{"token": "skirt", "weight": 1.0}]},
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "shoes", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {"path": ["trust"], "tokens": [{"token": "disgusting", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "chen,looking at viewer,blouse,skirt,socks,shoes,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [
                {
                    "matched": "？？？？？",
                    "pattern": "装備:下着\\s*\\[(.+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "status",
                    "paths": [["lingeries"]],
                }
            ],
        },
        "The World-2": {
            "dataclass": [
                {
                    "screen_id": "status",
                    "positive": [
                        {"path": ["name"], "tokens": [{"token": "izayoi sakuya", "weight": 1.0}]},
                        {
                            "path": ["affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "maid headdress", "weight": 1.0}]},
                        {"path": ["dresses"], "tokens": [{"token": "maid apron", "weight": 1.0}]},
                        {"path": ["socks"], "tokens": [{"token": "garter straps", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "shoes", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {"path": ["trust"], "tokens": [{"token": "disgusting", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "izayoi sakuya,looking at viewer,maid headdress,maid apron,garter straps,shoes,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [
                {
                    "matched": "？？？？？",
                    "pattern": "装備:下着\\s*\\[(.+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "status",
                    "paths": [["lingeries"]],
                },
                {
                    "matched": "リボン",
                    "pattern": "装備:付属\\s*\\[(.+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "status",
                    "paths": [["equipments"]],
                },
            ],
        },
        "The World-3": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "chen", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "angry"],
                            "tokens": [{"token": "jitome", "weight": 1.0}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [{"token": "in heat", "weight": 0.9}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "chen,looking at viewer,blush,jitome,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:0.9),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-4": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "izayoi sakuya", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "angry"],
                            "tokens": [{"token": "jitome", "weight": 1.0}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [{"token": "in heat", "weight": 0.9}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "izayoi sakuya,looking at viewer,blush,jitome,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:0.9),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
    },
    "CASE 'fashion'": {
        "The World-1": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "remilia scarlet", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [
                                {"token": "in heat", "weight": 1.2},
                                {"token": "blush", "weight": 1.2},
                            ],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "remilia scarlet,looking at viewer,blush,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:1.2),(blush:1.2),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-2": {
            "dataclass": [
                {
                    "screen_id": "fashion",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "remilia scarlet", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "hat", "weight": 1.0}]},
                        {"path": ["upper_cloths"], "tokens": [{"token": "blouse", "weight": 1.0}]},
                        {
                            "path": ["lower_cloths"],
                            "tokens": [{"token": "long skirt", "weight": 1.0}],
                        },
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "shoes", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "full body", "weight": 1.0},
                                {"token": "white background", "weight": 1.0},
                                {"token": "contrapposto", "weight": 1.0},
                                {"token": "light smile", "weight": 1.0},
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        }
                    ],
                }
            ],
            "string": {
                "POS": "remilia scarlet,hat,blouse,long skirt,socks,shoes,full body,white background,contrapposto,light smile,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [
                {
                    "matched": "？？？？？",
                    "pattern": "装備:下着\\s*\\[(.+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "fashion",
                    "paths": [["lingeries"]],
                }
            ],
        },
        "The World-3": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "remilia scarlet", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "hat", "weight": 1.0}]},
                        {"path": ["upper_cloths"], "tokens": [{"token": "blouse", "weight": 1.0}]},
                        {
                            "path": ["lower_cloths"],
                            "tokens": [{"token": "long skirt", "weight": 1.0}],
                        },
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "shoes", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [
                                {"token": "in heat", "weight": 1.2},
                                {"token": "blush", "weight": 1.2},
                            ],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "remilia scarlet,looking at viewer,blush,hat,blouse,long skirt,socks,shoes,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:1.2),(blush:1.2),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-4": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "chen", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [
                                {"token": "in heat", "weight": 1.2},
                                {"token": "blush", "weight": 1.2},
                            ],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "chen,looking at viewer,blush,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:1.2),(blush:1.2),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-5": {
            "dataclass": [
                {
                    "screen_id": "fashion",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "chen", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "hair ribbon", "weight": 1.0}]},
                        {"path": ["upper_cloths"], "tokens": [{"token": "t-shirt", "weight": 1.0}]},
                        {"path": ["lower_cloths"], "tokens": [{"token": "shorts", "weight": 1.0}]},
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "boots", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "full body", "weight": 1.0},
                                {"token": "white background", "weight": 1.0},
                                {"token": "contrapposto", "weight": 1.0},
                                {"token": "light smile", "weight": 1.0},
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["caps"],
                            "tokens": [
                                {"token": "caps", "weight": 1.0},
                                {"token": "hat", "weight": 1.0},
                            ],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "chen,hair ribbon,t-shirt,shorts,socks,boots,full body,white background,contrapposto,light smile,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "caps,hat,(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [
                {
                    "matched": "？？？？？",
                    "pattern": "装備:下着\\s*\\[(.+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "fashion",
                    "paths": [["lingeries"]],
                }
            ],
        },
        "The World-6": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "chen", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "hair ribbon", "weight": 1.0}]},
                        {"path": ["upper_cloths"], "tokens": [{"token": "t-shirt", "weight": 1.0}]},
                        {"path": ["lower_cloths"], "tokens": [{"token": "shorts", "weight": 1.0}]},
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "boots", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [
                                {"token": "in heat", "weight": 1.2},
                                {"token": "blush", "weight": 1.2},
                            ],
                        },
                        {
                            "path": ["caps"],
                            "tokens": [
                                {"token": "caps", "weight": 1.0},
                                {"token": "hat", "weight": 1.0},
                            ],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "chen,looking at viewer,blush,hair ribbon,t-shirt,shorts,socks,boots,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:1.2),(blush:1.2),caps,hat,(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-7": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "remilia scarlet", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "hat", "weight": 1.0}]},
                        {"path": ["upper_cloths"], "tokens": [{"token": "blouse", "weight": 1.0}]},
                        {
                            "path": ["lower_cloths"],
                            "tokens": [{"token": "long skirt", "weight": 1.0}],
                        },
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "shoes", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [
                                {"token": "in heat", "weight": 1.2},
                                {"token": "blush", "weight": 1.2},
                            ],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "remilia scarlet,looking at viewer,blush,hat,blouse,long skirt,socks,shoes,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:1.2),(blush:1.2),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-8": {
            "dataclass": [
                {
                    "screen_id": "fashion",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "remilia scarlet", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "newsboy cap", "weight": 1.0}]},
                        {"path": ["upper_cloths"], "tokens": [{"token": "jacket", "weight": 1.0}]},
                        {"path": ["lower_cloths"], "tokens": [{"token": "pants", "weight": 1.0}]},
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "shoes", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "full body", "weight": 1.0},
                                {"token": "white background", "weight": 1.0},
                                {"token": "contrapposto", "weight": 1.0},
                                {"token": "light smile", "weight": 1.0},
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        }
                    ],
                }
            ],
            "string": {
                "POS": "remilia scarlet,newsboy cap,jacket,pants,socks,shoes,full body,white background,contrapposto,light smile,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [
                {
                    "matched": "？？？？？",
                    "pattern": "装備:下着\\s*\\[(.+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "fashion",
                    "paths": [["lingeries"]],
                }
            ],
        },
        "The World-9": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "remilia scarlet", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "newsboy cap", "weight": 1.0}]},
                        {"path": ["upper_cloths"], "tokens": [{"token": "jacket", "weight": 1.0}]},
                        {"path": ["lower_cloths"], "tokens": [{"token": "pants", "weight": 1.0}]},
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "shoes", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [
                                {"token": "in heat", "weight": 1.2},
                                {"token": "blush", "weight": 1.2},
                            ],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "remilia scarlet,looking at viewer,blush,newsboy cap,jacket,pants,socks,shoes,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:1.2),(blush:1.2),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-10": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "chen", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "hair ribbon", "weight": 1.0}]},
                        {"path": ["upper_cloths"], "tokens": [{"token": "t-shirt", "weight": 1.0}]},
                        {"path": ["lower_cloths"], "tokens": [{"token": "shorts", "weight": 1.0}]},
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "boots", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [
                                {"token": "in heat", "weight": 1.2},
                                {"token": "blush", "weight": 1.2},
                            ],
                        },
                        {
                            "path": ["caps"],
                            "tokens": [
                                {"token": "caps", "weight": 1.0},
                                {"token": "hat", "weight": 1.0},
                            ],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "chen,looking at viewer,blush,hair ribbon,t-shirt,shorts,socks,boots,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:1.2),(blush:1.2),caps,hat,(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
    },
    "CASE 'action'": {
        "The World-1": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "remilia scarlet", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [
                                {"token": "in heat", "weight": 1.2},
                                {"token": "blush", "weight": 1.2},
                            ],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "remilia scarlet,looking at viewer,blush,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:1.2),(blush:1.2),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-2": {
            "dataclass": [
                {
                    "screen_id": "fashion",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "remilia scarlet", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "hat", "weight": 1.0}]},
                        {"path": ["upper_cloths"], "tokens": [{"token": "blouse", "weight": 1.0}]},
                        {
                            "path": ["lower_cloths"],
                            "tokens": [{"token": "long skirt", "weight": 1.0}],
                        },
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "shoes", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "full body", "weight": 1.0},
                                {"token": "white background", "weight": 1.0},
                                {"token": "contrapposto", "weight": 1.0},
                                {"token": "light smile", "weight": 1.0},
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        }
                    ],
                }
            ],
            "string": {
                "POS": "remilia scarlet,hat,blouse,long skirt,socks,shoes,full body,white background,contrapposto,light smile,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [
                {
                    "matched": "？？？？？",
                    "pattern": "装備:下着\\s*\\[(.+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "fashion",
                    "paths": [["lingeries"]],
                }
            ],
        },
        "The World-3": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "remilia scarlet", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "hat", "weight": 1.0}]},
                        {"path": ["upper_cloths"], "tokens": [{"token": "blouse", "weight": 1.0}]},
                        {
                            "path": ["lower_cloths"],
                            "tokens": [{"token": "long skirt", "weight": 1.0}],
                        },
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "shoes", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [
                                {"token": "in heat", "weight": 1.2},
                                {"token": "blush", "weight": 1.2},
                            ],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "remilia scarlet,looking at viewer,blush,hat,blouse,long skirt,socks,shoes,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:1.2),(blush:1.2),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-4": {
            "dataclass": [
                {
                    "screen_id": "action",
                    "positive": [
                        {
                            "path": ["action"],
                            "tokens": [
                                {"token": "holding tea", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "remilia scarlet", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "hat", "weight": 1.0}]},
                        {"path": ["upper_cloths"], "tokens": [{"token": "blouse", "weight": 1.0}]},
                        {
                            "path": ["lower_cloths"],
                            "tokens": [{"token": "long skirt", "weight": 1.0}],
                        },
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "shoes", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [
                                {"token": "in heat", "weight": 1.2},
                                {"token": "blush", "weight": 1.2},
                            ],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "holding tea,1girl,solo,remilia scarlet,looking at viewer,blush,hat,blouse,long skirt,socks,shoes,best quality,masterpiece,absurdres",  # noqa: E501
                "NEG": "disgusting,(in heat:1.2),(blush:1.2),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-5": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "remilia scarlet", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "hat", "weight": 1.0}]},
                        {"path": ["upper_cloths"], "tokens": [{"token": "blouse", "weight": 1.0}]},
                        {
                            "path": ["lower_cloths"],
                            "tokens": [{"token": "long skirt", "weight": 1.0}],
                        },
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "shoes", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                                {"token": "1girl", "weight": 1.0},
                                {"token": "solo", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [
                                {"token": "in heat", "weight": 1.2},
                                {"token": "blush", "weight": 1.2},
                            ],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "remilia scarlet,looking at viewer,blush,hat,blouse,long skirt,socks,shoes,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "disgusting,(in heat:1.2),(blush:1.2),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": True,
            "reports": [],
        },
        "The World-6": {
            "dataclass": [
                {
                    "screen_id": "action",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "remilia scarlet", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "affection"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "frustration"],
                            "tokens": [{"token": "blush", "weight": 1.0}],
                        },
                        {"path": ["caps"], "tokens": [{"token": "hat", "weight": 1.0}]},
                        {"path": ["upper_cloths"], "tokens": [{"token": "blouse", "weight": 1.0}]},
                        {
                            "path": ["lower_cloths"],
                            "tokens": [{"token": "long skirt", "weight": 1.0}],
                        },
                        {"path": ["socks"], "tokens": [{"token": "socks", "weight": 1.0}]},
                        {"path": ["shoes"], "tokens": [{"token": "shoes", "weight": 1.0}]},
                        {
                            "path": [],
                            "tokens": [
                                {"token": "best quality", "weight": 1.0},
                                {"token": "masterpiece", "weight": 1.0},
                                {"token": "absurdres", "weight": 1.0},
                            ],
                        },
                    ],
                    "negative": [
                        {
                            "path": ["character", "trust"],
                            "tokens": [{"token": "disgusting", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "reason"],
                            "tokens": [
                                {"token": "in heat", "weight": 1.2},
                                {"token": "blush", "weight": 1.2},
                            ],
                        },
                        {
                            "path": [],
                            "tokens": [
                                {"token": "amputee", "weight": 1.1},
                                {"token": "bad anatomy", "weight": 1.1},
                                {"token": "extra limbs", "weight": 1.1},
                                {"token": "missing limb", "weight": 1.1},
                                {"token": "multiple heads", "weight": 1.0},
                                {"token": "worst quality", "weight": 1.0},
                                {"token": "low quality", "weight": 1.0},
                                {"token": "motion lines", "weight": 1.0},
                                {"token": "speed lines", "weight": 1.0},
                                {"token": "3d", "weight": 1.0},
                                {"token": "shiny skin", "weight": 1.2},
                                {"token": "worst detail", "weight": 1.0},
                                {"token": "text", "weight": 1.0},
                                {"token": "logo", "weight": 1.0},
                                {"token": "cropped", "weight": 1.0},
                                {"token": "deformed", "weight": 1.0},
                                {"token": "blurry", "weight": 1.0},
                                {"token": "extra digits", "weight": 1.0},
                                {"token": "fewer digits", "weight": 1.0},
                                {"token": "missing digits", "weight": 1.0},
                                {"token": "bad hands", "weight": 1.0},
                                {"token": "mutated hands", "weight": 1.0},
                                {"token": "six toes", "weight": 1.0},
                                {"token": "extra toes", "weight": 1.0},
                                {"token": "fewer toes", "weight": 1.0},
                                {"token": "missing toes", "weight": 1.0},
                                {"token": "bad feet", "weight": 1.0},
                                {"token": "mutated feet", "weight": 1.0},
                                {"token": "extra feet", "weight": 1.0},
                                {"token": "missing foot", "weight": 1.0},
                                {"token": "bad leg", "weight": 1.0},
                                {"token": "extra legs", "weight": 1.0},
                                {"token": "missing leg", "weight": 1.0},
                                {"token": "extra hands", "weight": 1.0},
                                {"token": "missing hand", "weight": 1.0},
                                {"token": "bad arm", "weight": 1.0},
                                {"token": "extra arms", "weight": 1.0},
                                {"token": "missing arm", "weight": 1.0},
                            ],
                        },
                    ],
                }
            ],
            "string": {
                "POS": "remilia scarlet,looking at viewer,blush,hat,blouse,long skirt,socks,shoes,best quality,masterpiece,absurdres",  # noqa: E501
                "NEG": "disgusting,(in heat:1.2),(blush:1.2),(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "sufficiency": False,
            "reports": [
                {
                    "matched": "コーヒーを淹れる",
                    "pattern": "[0-9]{3}\\n(.+?)\\n-+\\n.+\\n",
                    "capturegrp": 1,
                    "screen_id": "action",
                    "paths": [["action"]],
                }
            ],
        },
    },
}


def make_testcase(texts: list[str]):
    return {KeyName.yamlpath: "yamls/The World.yaml", KeyName.texts: texts}


def debug_tw_interpreter() -> None:
    debugger = InterpreterDebugger()
    result = debugger.debug_cases(
        {
            "main": make_testcase(
                [
                    # No.1
                    "夏の月 6日目(月)11時05分 ― 快晴 ― ☀　気温14.5℃　<食事可>\n"
                    "橙(好感度:Ex 114482, 信頼度:SS 13538,　欲求不満度:87％,)　怒り:！\n"
                    "ムード:             理性:★            危険日前日",
                    # No.2
                    "夏の月 7日目(火)七夕12時00分 (午の三つ-昼中-)― 快晴 ― ☀　気温20.0℃　<食事可>　",  # noqa: E501
                    # No.3
                    "夏の月 6日目(月)11時05分 ― 快晴 ― ☀　気温14.5℃　<食事可>\n"
                    "レミリア私室 清潔度:中\n"
                    "橙(好感度:Ex 114482, 信頼度:SS 13538,　欲求不満度:87％,)　怒り:！\n"
                    "ムード:             理性:★            危険日前日",
                    # No.4
                    "夏の月 6日目(月)11時05分 ― 快晴 ― ☀　気温14.5℃　<食事可>\n"
                    "中有の道 清潔度:中\n"
                    "橙(好感度:Ex 114482, 信頼度:SS 13538,　欲求不満度:87％,)　怒り:！\n"
                    "ムード:             理性:★            危険日前日",
                    # No.5
                    "夏の月 6日目(月)11時05分 ― 快晴 ― ☀　気温14.5℃　<食事可>\n"
                    "中の道 清潔度:中\n"
                    "？(好感度:Ex 114482, 信頼度:SS 13538,　欲求不満度:87％,)　怒り:！\n"
                    "ムード:             理性:★            危険日前日",
                ],
            ),
            "status": make_testcase(
                [
                    # No.1
                    "■橙(好感度: S 27235 信頼度: S 4994)\n"
                    "　装備:上衣　　[ブラウス]\n　装備:下衣　　[スカート]\n"
                    "　装備:下着　　[？？？？？]\n　装備:靴下　　[靴下]\n"
                    "　装備:靴　　　[靴]",
                    # No.2
                    "■十六夜 咲夜(好感度: A 5326 信頼度: A 1397)\n"
                    "　装備:頭　　　[ホワイトブリム]\n"
                    "装備:全身服　[エプロンドレス]\n"
                    "装備:下着　　[？？？？？]\n"
                    "装備:付属　　[リボン]\n"
                    "装備:靴下　　[ガーターストッキング]\n"
                    "装備:靴　　　[靴]",
                    # No.3
                    "夏の月 6日目(月)11時05分 ― 快晴 ― ☀　気温14.5℃　<食事可>\n"
                    "橙(好感度:Ex 114482, 信頼度:SS 13538,　欲求不満度:87％,)　怒り:！\n"
                    "ムード:             理性:★            危険日前日",
                    # No.4
                    "夏の月 6日目(月)11時05分 ― 快晴 ― ☀　気温14.5℃　<食事可>\n"
                    "十六夜 咲夜(好感度:Ex 114482, 信頼度:SS 13538,　欲求不満度:87％,)　怒り:！\n"
                    "ムード:             理性:★            危険日前日",
                ],
            ),
            "fashion": make_testcase(
                [
                    # No.1
                    "夏の月 7日目(火)七夕21時33分 ― 快晴 ― ☪　気温20.0℃　<食事可>\n"
                    "レミリア スカーレット(好感度: S 27183, 信頼度: S 4962,　欲求不満度:68％,)　怒り:  　　　　　\n"  # noqa E501
                    "ムード:             理性:★★★★★    ？？？ ",
                    # No.2
                    "　装備:頭　　　[帽子]\n　"
                    "　装備:上衣　　[ブラウス]\n"
                    "　装備:下衣　　[ロングスカート]\n"
                    "　装備:下着　　[？？？？？]\n"
                    "　装備:靴下　　[靴下]\n"
                    "　装備:靴　　　[靴]\n"
                    "レミリアのお着替え中",
                    # No.3
                    "夏の月 7日目(火)七夕21時33分 ― 快晴 ― ☪　気温20.0℃　<食事可>\n"
                    "レミリア スカーレット(好感度: S 27183, 信頼度: S 4962,　欲求不満度:68％,)　怒り:  　　　　　\n"  # noqa E501
                    "ムード:             理性:★★★★★    ？？？ ",
                    # No.4
                    "夏の月 7日目(火)七夕21時33分 ― 快晴 ― ☪　気温20.0℃　<食事可>\n"
                    "橙(好感度: S 27183, 信頼度: S 4962,　欲求不満度:68％,)　怒り:  　　　　　\n"  # noqa E501
                    "ムード:             理性:★★★★★    ？？？ ",
                    # No.5
                    "　装備:頭　　　[リボン]\n"
                    "　装備:上衣　　[Ｔシャツ]\n"
                    "　装備:下衣　　[ハーフパンツ]\n"
                    "　装備:下着　　[？？？？？]\n"
                    "　装備:靴下　　[靴下]\n"
                    "　装備:靴　　　[ブーツ]\n"
                    "橙のお着替え中",
                    # No.6
                    "夏の月 7日目(火)七夕21時33分 ― 快晴 ― ☪　気温20.0℃　<食事可>\n"
                    "橙(好感度: S 27183, 信頼度: S 4962,　欲求不満度:68％,)　怒り:  　　　　　\n"  # noqa E501
                    "ムード:             理性:★★★★★    ？？？ ",
                    # No.7
                    "夏の月 7日目(火)七夕21時33分 ― 快晴 ― ☪　気温20.0℃　<食事可>\n"
                    "レミリア スカーレット(好感度: S 27183, 信頼度: S 4962,　欲求不満度:68％,)　怒り:  　　　　　\n"  # noqa E501
                    "ムード:             理性:★★★★★    ？？？ ",
                    # No.8
                    "　装備:頭　　　[キャスケット]\n"
                    "　装備:上衣　　[上着]\n"
                    "　装備:下衣　　[ズボン]\n"
                    "　装備:下着　　[？？？？？]\n"
                    "　装備:靴下　　[靴下]\n"
                    "　装備:靴　　　[靴]\n"
                    "レミリアのお着替え中",
                    # No.9
                    "夏の月 7日目(火)七夕21時33分 ― 快晴 ― ☪　気温20.0℃　<食事可>\n"
                    "レミリア スカーレット(好感度: S 27183, 信頼度: S 4962,　欲求不満度:68％,)　怒り:  　　　　　\n"  # noqa E501
                    "ムード:             理性:★★★★★    ？？？ ",
                    # No.10
                    "夏の月 7日目(火)七夕21時33分 ― 快晴 ― ☪　気温20.0℃　<食事可>\n"
                    "橙(好感度: S 27183, 信頼度: S 4962,　欲求不満度:68％,)　怒り:  　　　　　\n"  # noqa E501
                    "ムード:             理性:★★★★★    ？？？ ",
                ],
            ),
            "action": make_testcase(
                [
                    # No.1
                    "夏の月 7日目(火)七夕21時33分 ― 快晴 ― ☪　気温20.0℃　<食事可>\n"
                    "レミリア スカーレット(好感度: S 27183, 信頼度: S 4962,　欲求不満度:68％,)　怒り:  　　　　　\n"  # noqa E501
                    "ムード:             理性:★★★★★    ？？？ ",
                    # No.2
                    "　装備:頭　　　[帽子]\n　"
                    "　装備:上衣　　[ブラウス]\n"
                    "　装備:下衣　　[ロングスカート]\n"
                    "　装備:下着　　[？？？？？]\n"
                    "　装備:靴下　　[靴下]\n"
                    "　装備:靴　　　[靴]\n"
                    "レミリアのお着替え中",
                    # No.3
                    "夏の月 7日目(火)七夕21時33分 ― 快晴 ― ☪　気温20.0℃　<食事可>\n"
                    "レミリア スカーレット(好感度: S 27183, 信頼度: S 4962,　欲求不満度:68％,)　怒り:  　　　　　\n"  # noqa E501
                    "ムード:             理性:★★★★★    ？？？ ",
                    # No.4
                    "301\n"
                    "お茶を淹れる\n"
                    "----------------------------------------------------------------------------------------------------------------------------------------------\n"
                    "あなたはお茶を淹れてレミリアに差し出した…\n",
                    # No.5
                    "夏の月 7日目(火)七夕21時33分 ― 快晴 ― ☪　気温20.0℃　<食事可>\n"
                    "レミリア スカーレット(好感度: S 27183, 信頼度: S 4962,　欲求不満度:68％,)　怒り:  　　　　　\n"  # noqa E501
                    "ムード:             理性:★★★★★    ？？？ ",
                    # No.6
                    "301\n"
                    "コーヒーを淹れる\n"
                    "----------------------------------------------------------------------------------------------------------------------------------------------\n"
                    "あなたはコーヒーを淹れてレミリアに差し出した…\n",
                ]
            ),
        },
        with_texts=False,
    )
    print_result(result, CORRECT_RESULT)
