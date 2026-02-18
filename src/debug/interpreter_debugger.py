import os
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import pyperclip

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from common.functions import dump_json  # noqa: E402
from parser.interpreter.test_interpreter import TestInterpreter  # noqa: E402
from parser.parser import Parser  # noqa: E402
from parser.prompter import CategoryPath  # noqa: E402

CORRECT_RESULT = {
    "CASE 'dedupe'": {
        "Dedupe-1: 'go xxx'": {
            "set": [
                {
                    "positive": [
                        {"path": ["sub", "map2"], "tokens": [{"token": "sub_MAP2", "weight": 1.0}]},
                        {
                            "path": ["main", "map1"],
                            "tokens": [{"token": "main_MAP1", "weight": 1.0}],
                        },
                        {
                            "path": ["sub", "map1"],
                            "tokens": [
                                {"token": "foo", "weight": 2.1},
                                {"token": "sub_MAP1", "weight": 1.0},
                            ],
                        },
                        {
                            "path": ["main", "map2"],
                            "tokens": [{"token": "main_MAP2", "weight": 1.0}],
                        },
                        {"path": ["main"], "tokens": [{"token": "common_pos", "weight": 1.0}]},
                    ],
                    "negative": [
                        {
                            "path": ["sub", "map2"],
                            "tokens": [
                                {"token": "foo", "weight": 0.3},
                                {"token": "main_map2", "weight": 1.0},
                            ],
                        },
                        {"path": ["sub", "map2"], "tokens": [{"token": "sub_map2", "weight": 1.0}]},
                        {
                            "path": ["main", "map1"],
                            "tokens": [{"token": "main_map1", "weight": 1.0}],
                        },
                        {"path": ["sub", "map1"], "tokens": [{"token": "sub_map1", "weight": 1.0}]},
                        {"path": ["main"], "tokens": [{"token": "common_neg", "weight": 1.0}]},
                    ],
                }
            ],
            "prompts": {
                "POS": "sub_MAP2,main_MAP1,(foo:2.1),sub_MAP1,main_MAP2,common_pos",
                "NEG": "(foo:0.3),main_map2,sub_map2,main_map1,sub_map1,common_neg",
            },
        }
    }
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


class InterpreterDebugger(Parser):
    def __init__(self):
        super().__init__(None, None)

    def debug_texts(
        self, texts: list[str], with_texts: bool = True, category_list: list[CategoryPath] = None
    ) -> dict[str, dict[str, Any]]:
        """
        展開中 yaml について texts 内のテキストを順に適用する\n
        TestInterpreter と紐づく YAML を展開中の場合に限りカテゴリーリストの指定を行える

        Args:
            texts (list[str]): テスト用テキスト
        """
        if self.interpreter is None:
            raise Exception("Member 'interpreter' is None.")

        yamlname = self.interpreter.prompter.yamlpath.name.replace(".yaml", "")
        result: dict[str, dict[str, Any] | str] = {}
        for i, text in enumerate(texts):
            try:
                if isinstance(self.interpreter, TestInterpreter):
                    self.interpreter.restore_category_list(category_list)
                self.crnt_prompt_set = self.interpreter.make_prompt_set(text)
                major = f"{yamlname}-{i + 1}: '{text}'" if with_texts else f"{yamlname}-{i + 1}"
                pos, neg = self.make_prompt_strs()
                result[major] = {
                    "set": (self.crnt_prompt_set,),
                    "prompts": {"POS": pos, "NEG": neg},
                }
            except Exception as e:
                raise Exception(f"Error with '{text}'") from e
        return result

    def debug_cases(
        self, cases: dict[str, dict[Path | str, list[str | CategoryPath]]]
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """
        cases の Path の yaml を毎度展開し, それに紐づくテキストを順に適用する\n
        最も外側の str はパス重複解決のためのラベル

        Args:
            testcases (dict[str, dict[Path | str, list[str | CategoryPath]]]): テストケース
        """
        result: dict[str, dict[str, dict[str, Any]]] = {}
        for id, texts_n_paths in cases.items():
            result_by_texts = {}
            category_list = []
            for key, val in texts_n_paths.items():
                if key == "category_list":
                    category_list = val
                else:
                    yamlpath = key
                    inputs = val
            try:
                self.switch_interpreter(Path(yamlpath))
                result_by_texts = self.debug_texts(texts=inputs, category_list=category_list)
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


def make_testcase(yamlpath: Path, inputs: list[str], category_list: list[CategoryPath]):
    return {yamlpath: inputs, "category_list": category_list}


def debug_interpreter() -> None:
    debugger = InterpreterDebugger()
    result = debugger.debug_cases(
        {
            "dedupe": make_testcase(
                "yamls/testyamls/Dedupe.yaml",
                ["go xxx"],  # dedupe
                [("sub", "map2"), ("main", "map1"), ("sub", "map1"), ("main", "map2")],
            )
        }
    )
    dump_json(result, "debug")
    print("---------------------------------------------------------------------------")
    for key, test_result in result.items():
        correct_result = CORRECT_RESULT.get(key)
        if correct_result is None:
            print(f"NEW - {key}")
        else:
            normalized_test_result = normalize(test_result)
            if normalized_test_result == correct_result:
                print(f"OK  - {key}")
                for key, val in test_result.items():
                    dump_json(val.get("prompts"), key)
            else:
                print(f"NG  - {key}")
                dump_json(dict_diff(normalized_test_result, correct_result))


debug_interpreter()
