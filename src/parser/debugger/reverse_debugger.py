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
        "Reverse-1": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "name"],
                            "tokens": [{"token": "houjuu nue", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "vibe"],
                            "tokens": [{"token": "expressionless", "weight": 0.8}],
                        },
                        {
                            "path": ["character", "fashion", "dresses"],
                            "tokens": [{"token": "one-piece dress", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "fashion", "socks"],
                            "tokens": [{"token": "thighhighs", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "posture", "posture_meat"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "tool", "tool_meat"],
                            "tokens": [{"token": "strap-on", "weight": 1.0}],
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
                            "path": ["character", "fashion", "socks"],
                            "tokens": [{"token": "barefoot", "weight": 1.0}],
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
                "POS": "houjuu nue,(expressionless:0.8),one-piece dress,thighhighs,looking at viewer,strap-on,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "barefoot,(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "essentiality": True,
            "reports": [],
        },
        "Reverse-2": {
            "dataclass": [
                {
                    "screen_id": "main",
                    "positive": [
                        {
                            "path": ["character", "vibe"],
                            "tokens": [{"token": "expressionless", "weight": 0.8}],
                        },
                        {
                            "path": ["character", "posture", "posture_meat"],
                            "tokens": [{"token": "looking at viewer", "weight": 1.0}],
                        },
                        {
                            "path": ["character", "tool", "tool_meat"],
                            "tokens": [{"token": "strap-on", "weight": 1.0}],
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
                "POS": "(expressionless:0.8),looking at viewer,strap-on,best quality,masterpiece,absurdres,1girl,solo",  # noqa: E501
                "NEG": "(amputee:1.1),(bad anatomy:1.1),(extra limbs:1.1),(missing limb:1.1),multiple heads,worst quality,low quality,motion lines,speed lines,3d,(shiny skin:1.2),worst detail,text,logo,cropped,deformed,blurry,extra digits,fewer digits,missing digits,bad hands,mutated hands,six toes,extra toes,fewer toes,missing toes,bad feet,mutated feet,extra feet,missing foot,bad leg,extra legs,missing leg,extra hands,missing hand,bad arm,extra arms,missing arm",  # noqa: E501
            },
            "essentiality": False,
            "reports": [
                {
                    "matched": "ぬ",
                    "pattern": "^\\s*(.+?)\\s\\[LV",
                    "capturegrp": 1,
                    "screen_id": "main",
                    "paths": [["character", "name"]],
                },
                {
                    "matched": "ンピース",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "main",
                    "paths": [
                        ["character", "fashion", "dresses"],
                        ["character", "fashion", "lower_lingeries"],
                        ["character", "fashion", "socks"],
                        ["character", "fashion", "upper_lingeries"],
                    ],
                },
                {
                    "matched": "ブジャー",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "main",
                    "paths": [
                        ["character", "fashion", "dresses"],
                        ["character", "fashion", "lower_lingeries"],
                        ["character", "fashion", "socks"],
                        ["character", "fashion", "upper_lingeries"],
                    ],
                },
                {
                    "matched": "パンィ",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "main",
                    "paths": [
                        ["character", "fashion", "dresses"],
                        ["character", "fashion", "lower_lingeries"],
                        ["character", "fashion", "socks"],
                        ["character", "fashion", "upper_lingeries"],
                    ],
                },
                {
                    "matched": "ニーソクス",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "main",
                    "paths": [
                        ["character", "fashion", "dresses"],
                        ["character", "fashion", "lower_lingeries"],
                        ["character", "fashion", "socks"],
                        ["character", "fashion", "upper_lingeries"],
                    ],
                },
            ],
        },
    }
}


def make_testcase(texts: list[str]):
    return {KeyName.yamlpath: "yamls/Reverse.yaml", KeyName.texts: texts}


def debug_r_interpreter() -> None:
    debugger = InterpreterDebugger()
    result = debugger.debug_cases(
        {
            "main": make_testcase(
                [
                    # No.1
                    "6日目(昼)　経過時間[0]\r\n"
                    "ぬえ [LV 3  EXP 529/540] がxxx [LV 3  EXP 278/540] を調教中\r\n"
                    "ぬえの状態:[通常]                                      xxxの状態:[通常]\r\n"
                    "---------------------------------------------------------------------------------------------------------------------\r\n"  # noqa E501
                    "ぬえの衣装：[ワンピース][ブラジャー][パンティ][ニーソックス]\r\n"
                    "xxxの衣装：[Ｔシャツ][トランクス][ソックス]\r\n"
                    "現在の姿勢：[xxx：楽にしている][ぬえ：xxxを観察]\r\n"
                    "使用中　[ペニスバンド]",
                    # No.2
                    "6日目(昼)　経過時間[0]\r\n"
                    "ぬ [LV 3  EXP 529/540] がxxx [LV 3  EXP 278/540] を調教中\r\n"
                    "ぬえの状態:[通常]                                      xxxの状態:[通常]\r\n"
                    "---------------------------------------------------------------------------------------------------------------------\r\n"  # noqa E501
                    "ぬえの衣装：[ンピース][ブジャー][パンィ][ニーソクス]\r\n"
                    "xxxの衣装：[Ｔシャツ][トランクス][ソックス]\r\n"
                    "現在の姿勢：[xxx：楽にしている][ぬえ：xxxを観察]\r\n"
                    "使用中　[ペニスバンド]",
                ],
            ),
        },
        with_texts=False,
    )
    print_result(result, CORRECT_RESULT)
