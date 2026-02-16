import os
import sys
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any

import pyperclip
import yaml

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from common.functions import dump_json  # noqa: E402
from parser.prompter import Prompter  # noqa: E402

CORRECT_RESULT = {
    "CASE 'match'": {
        "testcase1-1: 'today Name2'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["character", "name"],
                        "positive": [{"token": "bar", "weight": 1.0}],
                        "negative": [{"token": "baz", "weight": 1.0}],
                    }
                ],
            }
        ]
    },
    "CASE 'int or string'": {
        "testcase2-1: 'go id:10'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["f", "test"],
                        "positive": [{"token": "ten", "weight": 1.0}],
                        "negative": [],
                    }
                ],
            }
        ]
    },
    "CASE 'default'": {
        "testcase3-1: 'go v:B'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["f", "test"],
                        "positive": [{"token": "zzz", "weight": 1.0}],
                        "negative": [],
                    }
                ],
            }
        ]
    },
    "CASE 'no match'": {"testcase3-1: 'go nothing'": [{"screen_id": "main", "category": []}]},
    "CASE 'ranges'": {
        "testcase6-1: 'go 8'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["t", "r"],
                        "positive": [{"token": "hot", "weight": 1.0}],
                        "negative": [{"token": "cold", "weight": 1.0}],
                    }
                ],
            }
        ],
        "testcase6-2: 'go 5'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["t", "r"],
                        "positive": [{"token": "warm", "weight": 1.0}],
                        "negative": [{"token": "cold", "weight": 1.0}],
                    }
                ],
            }
        ],
        "testcase6-3: 'go 2'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["t", "r"],
                        "positive": [{"token": "cool", "weight": 1.0}],
                        "negative": [],
                    }
                ],
            }
        ],
        "testcase6-4: 'go 9'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["t", "r"],
                        "positive": [{"token": "warm", "weight": 1.0}],
                        "negative": [],
                    }
                ],
            }
        ],
        "testcase6-5: 'go 1'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["t", "r"],
                        "positive": [],
                        "negative": [{"token": "heat", "weight": 1.0}],
                    }
                ],
            }
        ],
    },
    "CASE 'common'": {
        "testcase7-1: 'go x'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["t", "a"],
                        "positive": [{"token": "foo", "weight": 1.0}],
                        "negative": [],
                    },
                    {"path": [], "positive": [{"token": "common", "weight": 1.0}], "negative": []},
                ],
            }
        ]
    },
    "CASE 'empty token'": {"testcase14-1: 'go'": [{"screen_id": "main", "category": []}]},
    "CASE 'interval'": {
        "testcase16-1: 'go 20'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["s1"],
                        "positive": [
                            {"token": "low", "weight": 1.0},
                            {"token": "bad", "weight": 1.0},
                        ],
                        "negative": [
                            {"token": "good", "weight": 1.0},
                            {"token": "high", "weight": 1.0},
                            {"token": "ok", "weight": 1.0},
                        ],
                    }
                ],
            }
        ],
        "testcase16-2: 'go 50'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["s1"],
                        "positive": [
                            {"token": "low", "weight": 1.0},
                            {"token": "bad", "weight": 1.0},
                            {"token": "middle", "weight": 1.0},
                        ],
                        "negative": [
                            {"token": "good", "weight": 1.0},
                            {"token": "high", "weight": 1.0},
                        ],
                    }
                ],
            }
        ],
        "testcase16-3: 'go 55'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["s1"],
                        "positive": [
                            {"token": "bad", "weight": 1.0},
                            {"token": "middle", "weight": 1.0},
                        ],
                        "negative": [{"token": "high", "weight": 1.0}],
                    }
                ],
            }
        ],
        "testcase16-4: 'go 97'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["s1"],
                        "positive": [{"token": "perfect", "weight": 1.0}],
                        "negative": [],
                    }
                ],
            }
        ],
        "testcase16-5: 'go 10'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["s1"],
                        "positive": [
                            {"token": "low", "weight": 1.0},
                            {"token": "bad", "weight": 1.0},
                        ],
                        "negative": [
                            {"token": "good", "weight": 1.0},
                            {"token": "high", "weight": 1.0},
                            {"token": "ok", "weight": 1.0},
                        ],
                    }
                ],
            }
        ],
        "testcase16-6: 'go 75'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["s1"],
                        "positive": [{"token": "average", "weight": 1.0}],
                        "negative": [],
                    }
                ],
            }
        ],
    },
    "CASE 'multiple match'": {
        "testcase20-1: 'go hello world foo bar'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["t", "word"],
                        "positive": [
                            {"token": "hello_greeting", "weight": 1.0},
                            {"token": "world_place", "weight": 1.0},
                            {"token": "foo_item", "weight": 1.0},
                            {"token": "bar_item", "weight": 1.0},
                        ],
                        "negative": [],
                    }
                ],
            }
        ],
        "testcase20-2: 'go hello'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["t", "word"],
                        "positive": [{"token": "hello_greeting", "weight": 1.0}],
                        "negative": [],
                    }
                ],
            }
        ],
        "testcase20-3: 'go hello hello'": [
            {
                "screen_id": "main",
                "category": [
                    {
                        "path": ["t", "word"],
                        "positive": [
                            {"token": "hello_greeting", "weight": 1.0},
                            {"token": "hello_greeting", "weight": 1.0},  # dedupe しない!!
                        ],
                        "negative": [],
                    }
                ],
            }
        ],
        "testcase20-4: 'go unknown'": [{"screen_id": "main", "category": []}],
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


@dataclass
class PrompterDebugger:
    yamldict: dict = None
    prompter: Prompter = None

    @classmethod
    def make(cls, yamlpath: Path | str):
        obj = cls()
        obj.set(Path(yamlpath))
        return obj

    def set(self, yamlpath: Path):
        with open(yamlpath, "r", encoding="utf-8") as f:
            self.yamldict = yaml.safe_load(f)
        self.prompter = Prompter.make(yamlpath)

    def dump_yamldict(self) -> None:
        dump_json(self.yamldict, self.prompter.yamlpath.name.replace(".yaml", ""))

    def dump_normalized_yamldict(self) -> None:
        dump_json(
            self.prompter.todict(), f"normalized {self.prompter.yamlpath.name.replace('.yaml', '')}"
        )

    def debug_texts(self, texts: list[str], with_texts: bool = True) -> dict[str, dict[str, Any]]:
        """
        展開中 yaml について texts 内のテキストを順に適用する

        Args:
            texts (list[str]): テスト用テキスト
        """
        yamlname = self.prompter.yamlpath.name.replace(".yaml", "")
        result: dict[str, dict[str, Any]] = {}
        for i, text in enumerate(texts):
            try:
                deliverable = self.prompter.to_deliverable(text)
                if with_texts:
                    result[f"{yamlname}-{i + 1}: '{text}'"] = deliverable
                else:
                    result[f"{yamlname}-{i + 1}"] = deliverable
            except Exception as e:
                raise Exception(f"Error with '{text}'") from e
        return result

    def debug_cases(
        self, cases: dict[str, dict[Path | str, list[str]]]
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """
        cases の Path の yaml を毎度展開し, それに紐づくテキストを順に適用する\n
        最も外側の str はパス重複解決のためのラベル

        Args:
            testcases (dict[str, dict[Path, list[str]]]): テストケース
        """
        result: dict[str, dict[str, dict[str, Any]]] = {}
        for id, texts_n_paths in cases.items():
            result_by_texts = {}
            for yamlpath, texts in texts_n_paths.items():
                try:
                    self.set(Path(yamlpath))
                    result_by_texts = self.debug_texts(texts)
                except Exception as e:
                    raise Exception(f"Error on '{yamlpath}'") from e
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


def debug() -> None:
    debugger = PrompterDebugger()
    result = debugger.debug_cases(
        {
            "match": {"yamls/testyamls/testcase1.yaml": ["today Name2"]},
            "int or string": {"yamls/testyamls/testcase2.yaml": ["go id:10"]},
            "default": {"yamls/testyamls/testcase3.yaml": ["go v:B"]},
            "no match": {"yamls/testyamls/testcase3.yaml": ["go nothing"]},
            "ranges": {"yamls/testyamls/testcase6.yaml": ["go 8", "go 5", "go 2", "go 9", "go 1"]},
            "common": {"yamls/testyamls/testcase7.yaml": ["go x"]},
            "empty token": {"yamls/testyamls/testcase14.yaml": ["go"]},
            "interval": {
                "yamls/testyamls/testcase16.yaml": [
                    "go 20",
                    "go 50",
                    "go 55",
                    "go 97",
                    "go 10",
                    "go 75",
                ]
            },
            "multiple match": {
                "yamls/testyamls/testcase20.yaml": [
                    "go hello world foo bar",
                    "go hello",
                    "go hello hello",
                    "go unknown",
                ]
            },
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
            else:
                print(f"NG  - {key}")
                dump_json(dict_diff(normalized_test_result, correct_result), "diff")


debug()
