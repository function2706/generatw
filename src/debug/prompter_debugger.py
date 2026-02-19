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
from parser.test_parser import TestParser  # noqa: E402

CORRECT_RESULT = {
    "CASE 'empty definition'": {"Empty-1: 'go'": {"POS": [], "NEG": []}},
    "CASE 'ignition'": {
        "All-1: 'foobarbaz'": {"POS": [], "NEG": []},
        "All-2: 'main name: Hogemaru,'": {
            "POS": [
                [
                    {"path": ["main", "name"], "tokens": [{"token": "hogemaru", "weight": 1.0}]},
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [{"path": ["main"], "tokens": [{"token": "common main negative", "weight": 1.0}]}]
            ],
        },
        "All-3: 'main meta name: Fugami,weather: sunny,'": {
            "POS": [
                [
                    {"path": ["main", "name"], "tokens": [{"token": "fugami", "weight": 1.2}]},
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ],
                [
                    {"path": ["meta", "weather"], "tokens": [{"token": "sunny", "weight": 1.0}]},
                    {"path": ["meta"], "tokens": [{"token": "common meta", "weight": 1.0}]},
                ],
            ],
            "NEG": [
                [{"path": ["main"], "tokens": [{"token": "common main negative", "weight": 1.0}]}]
            ],
        },
    },
    "CASE 'match'": {
        "All-1: 'main vibe: good,'": {
            "POS": [
                [{"path": ["main"], "tokens": [{"token": "common main positive", "weight": 1.0}]}]
            ],
            "NEG": [
                [{"path": ["main"], "tokens": [{"token": "common main negative", "weight": 1.0}]}]
            ],
        },
        "All-2: 'sub vibe: good,'": {"POS": [], "NEG": []},
        "All-3: 'main season: 02,name: Foota,'": {
            "POS": [
                [
                    {
                        "path": ["main", "name"],
                        "tokens": [
                            {"token": "foota", "weight": 1.0},
                            {"token": "boy", "weight": 1.1},
                        ],
                    },
                    {
                        "path": ["main", "season"],
                        "tokens": [
                            {"token": "winter", "weight": 1.0},
                            {"token": "cool", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {"path": ["main", "name"], "tokens": [{"token": "barta", "weight": 1.0}]},
                    {
                        "path": ["main", "season"],
                        "tokens": [{"token": "scorching heat", "weight": 1.0}],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-4: 'main name: Hogemaru,name: Fugami,'": {
            "POS": [
                [
                    {
                        "path": ["main", "name"],
                        "tokens": [
                            {"token": "hogemaru", "weight": 1.0},
                            {"token": "fugami", "weight": 1.2},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [{"path": ["main"], "tokens": [{"token": "common main negative", "weight": 1.0}]}]
            ],
        },
    },
    "CASE 'hit'": {
        "All-1: 'meta weather: snowy,'": {
            "POS": [
                [
                    {"path": ["meta", "weather"], "tokens": [{"token": "cloudy", "weight": 1.0}]},
                    {"path": ["meta"], "tokens": [{"token": "common meta", "weight": 1.0}]},
                ]
            ],
            "NEG": [],
        },
        "All-2: 'meta location: office,'": {
            "POS": [[{"path": ["meta"], "tokens": [{"token": "common meta", "weight": 1.0}]}]],
            "NEG": [],
        },
        "All-3: 'sub like: Carrot,'": {
            "POS": [[{"path": ["sub", "like"], "tokens": [{"token": "nothing", "weight": 1.0}]}]],
            "NEG": [],
        },
        "All-4: 'sub ability: Toughness,'": {"POS": [], "NEG": []},
    },
    "CASE 'nest'": {
        "All-1: 'main upper: T Shirt,lower: Pants,'": {
            "POS": [
                [
                    {
                        "path": ["main", "fashion", "upper"],
                        "tokens": [{"token": "t-shirt", "weight": 1.0}],
                    },
                    {
                        "path": ["main", "fashion", "lower"],
                        "tokens": [{"token": "pants", "weight": 1.0}],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [{"path": ["main"], "tokens": [{"token": "common main negative", "weight": 1.0}]}]
            ],
        }
    },
    "CASE 'capture'": {
        "All-1: 'sub WoW!'": {
            "POS": [[{"path": ["sub", "whole"], "tokens": [{"token": "WoW", "weight": 1.0}]}]],
            "NEG": [],
        },
        "All-2: 'sub ng: Dummy,'": {"POS": [], "NEG": []},
        "All-3: 'sub grade: 1,'": {
            "POS": [[{"path": ["sub", "grade"], "tokens": [{"token": "grade 1", "weight": 1.0}]}]],
            "NEG": [],
        },
        "All-4: 'sub grade: 2,'": {
            "POS": [[{"path": ["sub", "grade"], "tokens": [{"token": "grade 2", "weight": 1.0}]}]],
            "NEG": [],
        },
    },
    "CASE 'weight-tokens'": {
        "All-1: 'main name: Foota,'": {
            "POS": [
                [
                    {
                        "path": ["main", "name"],
                        "tokens": [
                            {"token": "foota", "weight": 1.0},
                            {"token": "boy", "weight": 1.1},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {"path": ["main", "name"], "tokens": [{"token": "barta", "weight": 1.0}]},
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        }
    },
    "CASE 'default'": {
        "All-1: 'meta weather: snowy,'": {
            "POS": [
                [
                    {"path": ["meta", "weather"], "tokens": [{"token": "cloudy", "weight": 1.0}]},
                    {"path": ["meta"], "tokens": [{"token": "common meta", "weight": 1.0}]},
                ]
            ],
            "NEG": [],
        },
        "All-2: 'main season: 13,'": {
            "POS": [
                [
                    {"path": ["main", "season"], "tokens": [{"token": "ordinary", "weight": 1.0}]},
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {"path": ["main", "season"], "tokens": [{"token": "storm", "weight": 1.0}]},
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-3: 'main name: HogetaFugao,'": {
            "POS": [
                [
                    {"path": ["main", "name"], "tokens": [{"token": "smith", "weight": 1.0}]},
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [{"path": ["main"], "tokens": [{"token": "common main negative", "weight": 1.0}]}]
            ],
        },
        "All-4: 'main vitality: 1000,'": {
            "POS": [
                [{"path": ["main"], "tokens": [{"token": "common main positive", "weight": 1.0}]}]
            ],
            "NEG": [
                [
                    {"path": ["main", "vitality"], "tokens": [{"token": "special", "weight": 1.0}]},
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
    },
    "CASE 'common'": {
        "All-1: 'common1'": {
            "POS": [[{"path": ["common1"], "tokens": [{"token": "common1", "weight": 1.0}]}]],
            "NEG": [],
        },
        "All-2: 'common2'": {
            "POS": [[{"path": ["common2"], "tokens": [{"token": "common2", "weight": 1.0}]}]],
            "NEG": [],
        },
        "All-3: 'common3'": {
            "POS": [],
            "NEG": [[{"path": ["common3"], "tokens": [{"token": "common3", "weight": 1.0}]}]],
        },
        "All-4: 'common4'": {
            "POS": [[{"path": ["common4"], "tokens": [{"token": "common4-pos", "weight": 1.0}]}]],
            "NEG": [[{"path": ["common4"], "tokens": [{"token": "common4-neg", "weight": 1.0}]}]],
        },
    },
    "CASE 'ranges'": {
        "All-1: 'main season: 04'": {
            "POS": [
                [
                    {
                        "path": ["main", "season"],
                        "tokens": [
                            {"token": "spring", "weight": 1.0},
                            {"token": "cool", "weight": 1.0},
                            {"token": "H1", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {
                        "path": ["main", "season"],
                        "tokens": [
                            {"token": "scorching heat", "weight": 1.0},
                            {"token": "H2", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-2: 'main season: 08'": {
            "POS": [
                [
                    {
                        "path": ["main", "season"],
                        "tokens": [
                            {"token": "summer", "weight": 1.0},
                            {"token": "H1", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {
                        "path": ["main", "season"],
                        "tokens": [
                            {"token": "cold", "weight": 1.0},
                            {"token": "H2", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-3: 'main season: 08'": {
            "POS": [
                [
                    {
                        "path": ["main", "season"],
                        "tokens": [
                            {"token": "summer", "weight": 1.0},
                            {"token": "H1", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {
                        "path": ["main", "season"],
                        "tokens": [
                            {"token": "cold", "weight": 1.0},
                            {"token": "H2", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-4: 'main season: 07'": {
            "POS": [
                [
                    {
                        "path": ["main", "season"],
                        "tokens": [
                            {"token": "summer", "weight": 1.0},
                            {"token": "H1", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {
                        "path": ["main", "season"],
                        "tokens": [
                            {"token": "cold", "weight": 1.0},
                            {"token": "H2", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-5: 'main season: 01'": {
            "POS": [
                [
                    {
                        "path": ["main", "season"],
                        "tokens": [
                            {"token": "winter", "weight": 1.1},
                            {"token": "snow", "weight": 1.0},
                            {"token": "cool", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {
                        "path": ["main", "season"],
                        "tokens": [{"token": "scorching heat", "weight": 1.0}],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-6: 'main season: 09'": {
            "POS": [
                [
                    {
                        "path": ["main", "season"],
                        "tokens": [
                            {"token": "summer", "weight": 1.0},
                            {"token": "cool", "weight": 1.0},
                            {"token": "H1", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {
                        "path": ["main", "season"],
                        "tokens": [
                            {"token": "cold", "weight": 1.0},
                            {"token": "scorching heat", "weight": 1.0},
                            {"token": "H2", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-7: 'main season: 13'": {
            "POS": [
                [
                    {"path": ["main", "season"], "tokens": [{"token": "ordinary", "weight": 1.0}]},
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {"path": ["main", "season"], "tokens": [{"token": "storm", "weight": 1.0}]},
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-8: 'sub rwd: c,'": {"POS": [], "NEG": []},
    },
    "CASE 'intervals'": {
        "All-1: 'main vitality: 100,'": {
            "POS": [
                [
                    {"path": ["main", "vitality"], "tokens": [{"token": "perfect", "weight": 1.0}]},
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [{"path": ["main"], "tokens": [{"token": "common main negative", "weight": 1.0}]}]
            ],
        },
        "All-2: 'main vitality: 50,'": {
            "POS": [
                [
                    {
                        "path": ["main", "vitality"],
                        "tokens": [
                            {"token": "low", "weight": 1.0},
                            {"token": "bad", "weight": 1.0},
                            {"token": "middle", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {
                        "path": ["main", "vitality"],
                        "tokens": [
                            {"token": "good", "weight": 1.0},
                            {"token": "high", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-3: 'main vitality: 95,'": {
            "POS": [
                [
                    {"path": ["main", "vitality"], "tokens": [{"token": "perfect", "weight": 1.0}]},
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [{"path": ["main"], "tokens": [{"token": "common main negative", "weight": 1.0}]}]
            ],
        },
        "All-4: 'main vitality: 20,'": {
            "POS": [
                [
                    {
                        "path": ["main", "vitality"],
                        "tokens": [
                            {"token": "low", "weight": 1.0},
                            {"token": "bad", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {
                        "path": ["main", "vitality"],
                        "tokens": [
                            {"token": "good", "weight": 1.0},
                            {"token": "high", "weight": 1.0},
                            {"token": "ok", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-5: 'main vitality: 30,'": {
            "POS": [
                [
                    {
                        "path": ["main", "vitality"],
                        "tokens": [
                            {"token": "low", "weight": 1.0},
                            {"token": "bad", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {
                        "path": ["main", "vitality"],
                        "tokens": [
                            {"token": "good", "weight": 1.0},
                            {"token": "high", "weight": 1.0},
                            {"token": "ok", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-6: 'main vitality: 20,'": {
            "POS": [
                [
                    {
                        "path": ["main", "vitality"],
                        "tokens": [
                            {"token": "low", "weight": 1.0},
                            {"token": "bad", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {
                        "path": ["main", "vitality"],
                        "tokens": [
                            {"token": "good", "weight": 1.0},
                            {"token": "high", "weight": 1.0},
                            {"token": "ok", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-7: 'main vitality: 40,'": {
            "POS": [
                [
                    {
                        "path": ["main", "vitality"],
                        "tokens": [
                            {"token": "low", "weight": 1.0},
                            {"token": "bad", "weight": 1.0},
                            {"token": "middle", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main positive", "weight": 1.0}],
                    },
                ]
            ],
            "NEG": [
                [
                    {
                        "path": ["main", "vitality"],
                        "tokens": [
                            {"token": "good", "weight": 1.0},
                            {"token": "high", "weight": 1.0},
                            {"token": "ok", "weight": 1.0},
                        ],
                    },
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-8: 'main vitality: 1000,'": {
            "POS": [
                [{"path": ["main"], "tokens": [{"token": "common main positive", "weight": 1.0}]}]
            ],
            "NEG": [
                [
                    {"path": ["main", "vitality"], "tokens": [{"token": "special", "weight": 1.0}]},
                    {
                        "path": ["main"],
                        "tokens": [{"token": "common main negative", "weight": 1.0}],
                    },
                ]
            ],
        },
        "All-9: 'sub iwd: 100,'": {"POS": [], "NEG": []},
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
                pos, neg = self.prompter.to_prompt(text)
                posneg = {"POS": pos, "NEG": neg}
                if with_texts:
                    result[f"{yamlname}-{i + 1}: '{text}'"] = posneg
                else:
                    result[f"{yamlname}-{i + 1}"] = posneg
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


def debug_prompter() -> None:
    debugger = PrompterDebugger()
    result = debugger.debug_cases(
        {
            "empty definition": {
                "yamls/testyamls/Empty.yaml": ["go"]  # 空定義
            },
            "ignition": {
                "yamls/testyamls/All.yaml": [
                    "foobarbaz",  # Screen 発火なし
                    "main name: Hogemaru,",  # Screen 発火
                    "main meta name: Fugami,weather: sunny,",  # 複数 Screen 発火
                ]
            },
            "match": {
                "yamls/testyamls/All.yaml": [
                    "main vibe: good,",  # マッチなし, common あり
                    "sub vibe: good,",  # マッチなし, common なし
                    "main season: 02,name: Foota,",  # マッチ順序
                    "main name: Hogemaru,name: Fugami,",  # 複数マッチ
                ]
            },
            "hit": {
                "yamls/testyamls/All.yaml": [
                    "meta weather: snowy,",  # ヒットせず, default あり, common あり
                    "meta location: office,",  # ヒットせず, default なし, common あり
                    "sub like: Carrot,",  # ヒットせず, default あり, common なし
                    "sub ability: Toughness,",  # ヒットせず, default なし, common なし
                ]
            },
            "nest": {
                "yamls/testyamls/All.yaml": [
                    "main upper: T Shirt,lower: Pants,",  # 多階層 Rule
                ]
            },
            "capture": {
                "yamls/testyamls/All.yaml": [
                    "sub WoW!",  # 全体キャプチャ
                    "sub ng: Dummy,",  # キャプチャ範囲逸脱
                    "sub grade: 1,",  # キーが文字列の数値
                    "sub grade: 2,",  # キーが数値
                ]
            },
            "weight-tokens": {
                "yamls/testyamls/All.yaml": [
                    "main name: Foota,",  # 重み付き複数トークン
                ]
            },
            "default": {
                "yamls/testyamls/All.yaml": [
                    "meta weather: snowy,",  # 省略形
                    "main season: 13,",  # 両方記述
                    "main name: HogetaFugao,",  # positive のみ
                    "main vitality: 1000,",  # negative のみ
                ]
            },
            "common": {
                "yamls/testyamls/All.yaml": [
                    "common1",  # 省略形
                    "common2",  # positive のみ
                    "common3",  # negative のみ
                    "common4",  # 両方記述
                ]
            },
            "ranges": {
                "yamls/testyamls/All.yaml": [
                    "main season: 04",  # 省略形
                    "main season: 08",  # positive のみ
                    "main season: 08",  # negative のみ
                    "main season: 07",  # 両方記述 (positive)
                    "main season: 01",  # 両方記述 (negative)
                    "main season: 09",  # 複数ヒット
                    "main season: 13",  # ヒットせず, defaultあり
                    "sub rwd: c,",  # ヒットせず, default なし
                ]
            },
            "intervals": {
                "yamls/testyamls/All.yaml": [
                    "main vitality: 100,",  # 境界値
                    "main vitality: 50,",  # 省略形
                    "main vitality: 95,",  # positive のみ
                    "main vitality: 20,",  # negative のみ
                    "main vitality: 30,",  # 両方記述 (positive)
                    "main vitality: 20,",  # 両方記述 (negative)
                    "main vitality: 40,",  # 複数ヒット
                    "main vitality: 1000,",  # ヒットせず, defaultあり
                    "sub iwd: 100,",  # ヒットせず, default なし
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


def debug_parser() -> None:
    parser = TestParser(
        None,
        None,
    )
    parser.prompter = Prompter.make("yamls/Dedupe.yaml")
    parser.crnt_prompt_set = parser.make_prompt_set("go xxx")
    pos, neg = parser.make_prompt_strs()
    print(pos)
    print(neg)


debug_prompter()
# debug_parser()
