import os
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from common.functions import dump_json  # noqa: E402
from parser.prompter import Prompter  # noqa: E402

CORRECT_RESULT = {
    "CASE 'match'": {"testcase1-1: 'today Name2'": {"POS": "bar", "NEG": "baz"}},
    "CASE 'int or string'": {"testcase2-1: 'go id:10'": {"POS": "ten", "NEG": ""}},
    "CASE 'default'": {"testcase3-1: 'go v:B'": {"POS": "zzz", "NEG": ""}},
    "CASE 'no match'": {"testcase3-1: 'go nothing'": {"POS": "", "NEG": ""}},
    "CASE 'weight dedupe'": {"testcase4-1: 'go x'": {"POS": "(foo:1.5)", "NEG": ""}},
    "CASE 'stable push stable out'": {
        "testcase5-1: 'go v:A'": {"POS": "alpha", "NEG": ""},
        "testcase5-2: 'go v:B'": {"POS": "beta", "NEG": ""},
    },
    "CASE 'wetty'": {"testcase5-1: 'hello v:A'": {"POS": "", "NEG": ""}},
    "CASE 'ranges'": {
        "testcase6-1: 'go 8'": {"POS": "hot", "NEG": "cold"},
        "testcase6-2: 'go 5'": {"POS": "warm", "NEG": "cold"},
        "testcase6-3: 'go 2'": {"POS": "cool", "NEG": ""},
        "testcase6-4: 'go 9'": {"POS": "warm", "NEG": ""},
        "testcase6-5: 'go 1'": {"POS": "", "NEG": "heat"},
    },
    "CASE 'common'": {"testcase7-1: 'go x'": {"POS": "foo,common", "NEG": ""}},
    "CASE 'priority dedupe'": {"testcase8-1: 'go x'": {"POS": "first,second", "NEG": ""}},
    "CASE 'pos pop, neg vanish'": {
        "testcase9-1: 'go v:A'": {"POS": "apple", "NEG": "bad"},
        "testcase9-2: 'go v:B'": {"POS": "banana", "NEG": ""},
    },
    "CASE 'neg pop, pos vanish'": {
        "testcase10-1: 'go v:A'": {"POS": "apple", "NEG": ""},
        "testcase10-2: 'go v:B'": {"POS": "", "NEG": "bad"},
    },
    "CASE 'both vanish'": {
        "testcase11-1: 'go v:A'": {"POS": "apple", "NEG": "bad"},
        "testcase11-2: 'go v:B'": {"POS": "", "NEG": ""},
    },
    "CASE 'volatile vanish soon'": {
        "testcase12-1: 'go v:A'": {"POS": "apple", "NEG": ""},
        "testcase12-2: 'go nothing'": {"POS": "", "NEG": ""},
    },
    "CASE 'no match, default pop'": {
        "testcase13-1: 'go v:A'": {"POS": "apple", "NEG": ""},
        "testcase13-2: 'go v:B'": {"POS": "default", "NEG": ""},
    },
    "CASE 'empty token'": {"testcase14-1: 'go'": {"POS": "", "NEG": ""}},
    "CASE 'another rule kill nobody'": {
        "testcase15-1: 'go a:on b:on'": {"POS": "A,B", "NEG": ""},
        "testcase15-2: 'go a:off'": {"POS": "B", "NEG": ""},
    },
    "CASE 'interval'": {
        "testcase16-1: 'go 20'": {"POS": "low,bad", "NEG": "good,high,ok"},
        "testcase16-2: 'go 50'": {"POS": "low,bad,middle", "NEG": "good,high"},
        "testcase16-3: 'go 55'": {"POS": "bad,middle", "NEG": "high"},
        "testcase16-4: 'go 97'": {"POS": "perfect", "NEG": ""},
        "testcase16-5: 'go 10'": {"POS": "low,bad", "NEG": "good,high,ok"},
        "testcase16-6: 'go 75'": {"POS": "average", "NEG": ""},
    },
    "CASE 'complex 1'": {
        "test-1: 'today: 2026/02/05, Name2 (vibe: Vibe1)'": {
            "POS": "name2,feature2,vibe1,winter,common positive",
            "NEG": "NAME2,HOT,common negative",
        },
        "test-2: 'sub: WOW!! mood: Mood2 , equip: Slacks foobar'": {
            "POS": "name2,feature2,vibe1,winter,mood2,pants,sub common positive",
            "NEG": "NAME2,HOT,MOOD2,skirt,sub common negative",
        },
        "test-3: 'today: foobarBarFugahogeHogeBazbaz'": {
            "POS": "name2,feature2,vibe1,winter,mood2,fuga,(hoge:1.3),foo,(bar:1.3),baz,common positive",  # noqa: E501
            "NEG": "NAME2,HOT,MOOD2,FUGA,HOGE,FOO,(nope:1.4),BAR,nyome,BAZ,common negative",
        },
        "test-4: 'sub: WOW!! mood: Mood1 , equip: Blouse point: 20'": {
            "POS": "name2,feature2,vibe1,winter,mood1,low,bad,sub common positive",
            "NEG": "NAME2,HOT,good,high,ok,sub common negative",
        },
        "test-5: 'today: 2026/07/21, Name1 (vibe: ) foobarBarFugahogeHogeBazbaz'": {
            "POS": "mood1,name1,feature1,vibe3,fuga,(hoge:1.3),summer,foo,(bar:1.3),baz,common positive",  # noqa: E501
            "NEG": "FUGA,HOGE,FOO,(nope:1.4),BAR,nyome,BAZ,common negative",
        },
    },
    "CASE 'complex 2'": {
        "test2-1: 'start name:alice boost month:04 tag:a tag:b miss:bad side'": {
            "POS": "(girl:1.5),spring,A,B,DEF,SIDE_P,commonA",
            "NEG": "snow,SIDE_N,commonN",
        }
    },
    "CASE 'complex 3'": {
        "test3-1: 'today name:alice m:03 vibe:happy'": {
            "POS": "alice,spring,happy,main_common_p",
            "NEG": "main_common_n",
        },
        "test3-2: 'today m:03'": {"POS": "alice,spring,main_common_p", "NEG": "main_common_n"},
        "test3-3: 'today name:bob boost m:12'": {
            "POS": "bob,(alice:1.5),winter,main_common_p",
            "NEG": "cold,main_common_n",
        },
        "test3-4: 'hello name:alice'": {"POS": "bob,winter", "NEG": "cold"},
        "test3-5: 'sub go mood:good'": {
            "POS": "bob,winter,good,sub_common_p",
            "NEG": "cold,sub_common_n",
        },
        "test3-6: 'sub go'": {"POS": "bob,winter,good,sub_common_p", "NEG": "cold,sub_common_n"},
        "test3-7: 'sub go mood:bad'": {
            "POS": "bob,winter,sub_common_p",
            "NEG": "cold,BAD,sub_common_n",
        },
    },
}


@dataclass
class PrompterDebugger:
    yamlpath: Path = None
    yamldict: dict = None
    prompter: Prompter = None

    @classmethod
    def make(cls, yamlpath: Path | str):
        obj = cls()
        obj.set(Path(yamlpath))
        return obj

    def set(self, yamlpath: Path):
        self.yamlpath = yamlpath
        with open(yamlpath, "r", encoding="utf-8") as f:
            self.yamldict = yaml.safe_load(f)
        self.prompter = Prompter.make(yamlpath)

    def dump_yamldict(self) -> None:
        dump_json(self.yamldict, self.yamlpath.name.replace(".yaml", ""))

    def dump_normalized_yamldict(self) -> None:
        dump_json(self.prompter.todict(), f"normalized {self.yamlpath.name.replace('.yaml', '')}")

    def debug_texts(self, texts: list[str]) -> dict[str, dict[str, str]]:
        """
        展開中 yaml について texts 内のテキストを順に適用する

        Args:
            texts (list[str]): テスト用テキスト
        """
        yamlname = self.yamlpath.name.replace(".yaml", "")
        result: dict[str, dict[str, str]] = {}
        for i, text in enumerate(texts):
            try:
                pos, neg = self.prompter.toprompt(text)
                posneg = {"POS": pos, "NEG": neg}
                result[f"{yamlname}-{i + 1}: '{text}'"] = posneg
            except Exception as e:
                raise Exception(f"Error with '{text}'") from e
        return result

    def debug_cases(
        self, cases: dict[str, dict[Path | str, list[str]]]
    ) -> dict[str, dict[str, dict[str, str]]]:
        """
        cases の Path の yaml を毎度展開し, それに紐づくテキストを順に適用する\n
        最も外側の str はパス重複解決のためのラベル

        Args:
            testcases (dict[str, dict[Path, list[str]]]): テストケース
        """
        result: dict[str, dict[str, dict[str, str]]] = {}
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


def debug() -> None:
    debugger = PrompterDebugger()
    result = debugger.debug_cases(
        {
            "match": {"yamls/testyamls/testcase1.yaml": ["today Name2"]},
            "int or string": {"yamls/testyamls/testcase2.yaml": ["go id:10"]},
            "default": {"yamls/testyamls/testcase3.yaml": ["go v:B"]},
            "no match": {"yamls/testyamls/testcase3.yaml": ["go nothing"]},
            "weight dedupe": {"yamls/testyamls/testcase4.yaml": ["go x"]},
            "stable push stable out": {"yamls/testyamls/testcase5.yaml": ["go v:A", "go v:B"]},
            "wetty": {"yamls/testyamls/testcase5.yaml": ["hello v:A"]},
            "ranges": {"yamls/testyamls/testcase6.yaml": ["go 8", "go 5", "go 2", "go 9", "go 1"]},
            "common": {"yamls/testyamls/testcase7.yaml": ["go x"]},
            "priority dedupe": {"yamls/testyamls/testcase8.yaml": ["go x"]},
            "pos pop, neg vanish": {"yamls/testyamls/testcase9.yaml": ["go v:A", "go v:B"]},
            "neg pop, pos vanish": {"yamls/testyamls/testcase10.yaml": ["go v:A", "go v:B"]},
            "both vanish": {"yamls/testyamls/testcase11.yaml": ["go v:A", "go v:B"]},
            "volatile vanish soon": {"yamls/testyamls/testcase12.yaml": ["go v:A", "go nothing"]},
            "no match, default pop": {"yamls/testyamls/testcase13.yaml": ["go v:A", "go v:B"]},
            "empty token": {"yamls/testyamls/testcase14.yaml": ["go"]},
            "another rule kill nobody": {
                "yamls/testyamls/testcase15.yaml": ["go a:on b:on", "go a:off"]
            },
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
            "complex 1": {
                "yamls/testyamls/test.yaml": [
                    "today: 2026/02/05, Name2 (vibe: Vibe1)",
                    "sub: WOW!! mood: Mood2 , equip: Slacks foobar",
                    "today: foobarBarFugahogeHogeBazbaz",
                    "sub: WOW!! mood: Mood1 , equip: Blouse point: 20",
                    "today: 2026/07/21, Name1 (vibe: ) foobarBarFugahogeHogeBazbaz",
                ]
            },
            "complex 2": {
                "yamls/testyamls/test2.yaml": [
                    "start name:alice boost month:04 tag:a tag:b miss:bad side"
                ]
            },
            "complex 3": {
                "yamls/testyamls/test3.yaml": [
                    "today name:alice m:03 vibe:happy",
                    "today m:03",
                    "today name:bob boost m:12",
                    "hello name:alice",
                    "sub go mood:good",
                    "sub go",
                    "sub go mood:bad",
                ]
            },
        }
    )
    dump_json(result, "debug")
    for key, test_result in result.items():
        correct_result = CORRECT_RESULT.get(key)
        if correct_result is None:
            print("NEW - ", end="")
        else:
            if test_result == correct_result:
                print("OK  - ", end="")
            else:
                print("NG  - ", end="")
        print(f"{key}")


debug()
