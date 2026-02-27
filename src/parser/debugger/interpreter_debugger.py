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


class InterpreterDebugger(Parser):
    def __init__(self):
        super().__init__(None, None)

    def debug_texts(
        self,
        texts: list[str],
        screen_id: str = None,
        encats: list[EnhancedCategory] = None,
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
                    self.interpreter.restore_enhanced_category_list(screen_id, encats)
                self.crnt_prompt = self.interpreter.make_prompt(text)
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
                }
            except Exception as e:
                raise Exception(f"Error with '{text}'") from e
        return result

    def debug_cases(
        self,
        testcases: dict[str, dict[str, str | list]],
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
            for key, val in testcase.items():
                if key == KeyName.yamlpath:
                    yamlpath = val
                elif key == KeyName.texts:
                    texts = val
                elif key == KeyName.screen_id:
                    screen_id = val
                elif key == KeyName.enhanced_category_list:
                    encats = val
            try:
                self.switch_interpreter(Path(yamlpath))
                result_by_texts = self.debug_texts(
                    texts=texts,
                    screen_id=screen_id,
                    encats=encats,
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

    return obj


def make_testcase(yamlpath: Path, texts: list[str], screen_id: str, encats: list[EnhancedCategory]):
    return {
        KeyName.yamlpath: yamlpath,
        KeyName.texts: texts,
        KeyName.screen_id: screen_id,
        KeyName.enhanced_category_list: encats,
    }


def print_result(
    result: dict[str, dict[str, dict[str, Any]]], correct: dict[str, dict[str, dict[str, Any]]]
) -> None:
    dump_json(result, "debug")
    print("---------------------------------------------------------------------------")
    for key, test_result in result.items():
        correct_result = correct.get(key)
        if correct_result is None:
            print(f"NEW - {key}")
        else:
            normalized_test_result = normalize(test_result)
            if normalized_test_result == correct_result:
                print(f"OK  - {key}")
                for key, val in test_result.items():
                    dump_json(val.get("string"), key)
            else:
                print(f"NG  - {key}")
                dump_json(dict_diff(normalized_test_result, correct_result))


def debug_interpreter() -> None:
    debugger = InterpreterDebugger()
    result = debugger.debug_cases(
        {
            "strip": make_testcase(
                "yamls/testyamls/InterpreterTest.yaml",
                ["strip xxx"],
                "strip",
                [(("ok1",), None, False), (("ok2",), None, False)],
            ),
            "dedupe": make_testcase(
                "yamls/testyamls/InterpreterTest.yaml",
                ["dedupe xxx"],
                "dedupe",
                [
                    (("map1",), None, False),
                    (("map2",), None, False),
                    (("map3",), None, False),
                    (("map4",), None, False),
                ],
            ),
            "dedupe2": make_testcase(
                "yamls/testyamls/InterpreterTest.yaml",
                ["dedupe xxx"],
                "dedupe",
                [
                    (("map5",), None, False),
                    (("map1",), None, False),
                    (("map2",), None, False),
                    (("map3",), None, False),
                    (("map4",), None, False),
                ],
            ),
            "dedupe3": make_testcase(
                "yamls/testyamls/InterpreterTest.yaml",
                ["dedupe xxx"],
                "dedupe",
                [
                    (("map5",), None, False),
                    (("map1",), None, False),
                    (("map2",), None, False),
                    (("map4",), None, False),
                ],
            ),
            "dedupe4": make_testcase(
                "yamls/testyamls/InterpreterTest.yaml",
                ["dedupe xxx"],
                "dedupe",
                [
                    (("map5",), None, False),
                    (("map1",), None, False),
                    (("dummy"), None, False),
                    (("map2",), None, False),
                    (("map4",), None, False),
                ],
            ),
            "sort": make_testcase(
                "yamls/testyamls/InterpreterTest.yaml",
                ["sort xxx"],
                "sort",
                [
                    (("map3",), None, False),
                    (("map2",), None, False),
                    (("map4",), None, False),
                    (("map1",), None, False),
                ],
            ),
            "essential": make_testcase(
                "yamls/testyamls/InterpreterTest.yaml",
                [
                    "essential BD",
                    "essential ABD",
                    "essential BCD",
                    "essential BDE",
                    "essential ABCDE",
                ],
                "essential",
                [
                    (("need1",), None, True),
                    (("need2",), None, True),
                    (("need3",), None, True),
                    (("notneed1",), None, False),
                    (("notneed2",), None, False),
                ],
            ),
        }
    )
    print_result(result, CORRECT_RESULT)
