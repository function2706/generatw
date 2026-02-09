import os
import sys
from dataclasses import dataclass
from pathlib import Path

import pyperclip
import yaml

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from common.functions import dump_json  # noqa: E402
from parser.prompter import Prompter  # noqa: E402

CORRECT_RESULT = {
    "case-1": {"testcase1-1: 'today Name2'": {"POS": "bar", "NEG": "baz"}},
    "case-2": {"testcase2-1: 'go id:10'": {"POS": "ten", "NEG": ""}},
    "case-3": {"testcase3-1: 'go v:B'": {"POS": "zzz", "NEG": ""}},
    "case-4": {"testcase3-1: 'go nothing'": {"POS": "", "NEG": ""}},
    "case-5": {"testcase4-1: 'go x'": {"POS": "(foo:1.5)", "NEG": ""}},
    "case-6": {
        "testcase5-1: 'go v:A'": {"POS": "alpha", "NEG": ""},
        "testcase5-2: 'go v:B'": {"POS": "beta", "NEG": ""},
    },
    "case-7": {"testcase5-1: 'hello v:A'": {"POS": "", "NEG": ""}},
    "case-8": {"testcase6-1: 'go 8'": {"POS": "hot", "NEG": "cold"}},
    "case-9": {"testcase7-1: 'go x'": {"POS": "foo,common", "NEG": ""}},
    "case-10": {"testcase8-1: 'go x'": {"POS": "first,second", "NEG": ""}},
    "case-11": {
        "testcase9-1: 'go v:A'": {"POS": "apple", "NEG": "bad"},
        "testcase9-2: 'go v:B'": {"POS": "banana", "NEG": ""},
    },
    "case-12": {
        "testcase10-1: 'go v:A'": {"POS": "apple", "NEG": ""},
        "testcase10-2: 'go v:B'": {"POS": "", "NEG": "bad"},
    },
    "case-13": {
        "testcase11-1: 'go v:A'": {"POS": "apple", "NEG": "bad"},
        "testcase11-2: 'go v:B'": {"POS": "", "NEG": ""},
    },
    "case-14": {
        "testcase12-1: 'go v:A'": {"POS": "apple", "NEG": ""},
        "testcase12-2: 'go nothing'": {"POS": "", "NEG": ""},
    },
    "case-15": {
        "testcase13-1: 'go v:A'": {"POS": "apple", "NEG": ""},
        "testcase13-2: 'go v:B'": {"POS": "default", "NEG": ""},
    },
    "case-16": {"testcase14-1: 'go'": {"POS": "", "NEG": ""}},
    "case-17": {
        "testcase15-1: 'go a:on b:on'": {"POS": "A,B", "NEG": ""},
        "testcase15-2: 'go a:off'": {"POS": "B", "NEG": ""},
    },
    "case-18": {
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
        "test-4: 'sub: WOW!! mood: Mood1 , equip: Blouse '": {
            "POS": "name2,feature2,vibe1,winter,mood1,shirt,sub common positive",
            "NEG": "NAME2,HOT,sub common negative",
        },
        "test-5: 'today: 2026/07/21, Name1 (vibe: ) foobarBarFugahogeHogeBazbaz'": {
            "POS": "mood1,name1,feature1,vibe3,fuga,(hoge:1.3),summer,foo,(bar:1.3),baz,common positive",  # noqa: E501
            "NEG": "FUGA,HOGE,FOO,(nope:1.4),BAR,nyome,BAZ,common negative",
        },
    },
    "case-19": {
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
    "case-20": {
        "test2-1: 'start name:alice boost month:04 tag:a tag:b miss:bad side'": {
            "POS": "(girl:1.5),spring,A,B,DEF,SIDE_P,commonA",
            "NEG": "snow,SIDE_N,commonN",
        }
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

    def debug_texts(self, texts: list[str]) -> dict[str, dict[str, str]]:
        """
        展開中 yaml について texts 内のテキストを順に適用する

        Args:
            texts (list[str]): テスト用テキスト
        """
        yamlname = self.yamlpath.name.replace(".yaml", "")
        result: dict[str, dict[str, str]] = {}
        for i, text in enumerate(texts):
            pos, neg = self.prompter.toprompt(text)
            posneg = {"POS": pos, "NEG": neg}
            result[f"{yamlname}-{i + 1}: '{text}'"] = posneg
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
                self.set(Path(yamlpath))
                result_by_texts = self.debug_texts(texts)
            result[f"case-{id}"] = result_by_texts
        return result

    def debug_clipboard(self) -> None:
        """
        展開中 yaml について現在のクリップボードの内容を適用する
        """
        self.debug_texts([pyperclip.paste()])


def debug() -> None:
    debugger = PrompterDebugger()
    result = debugger.debug_cases(
        {
            "1": {"yamls/testyamls/testcase1.yaml": ["today Name2"]},
            "2": {"yamls/testyamls/testcase2.yaml": ["go id:10"]},
            "3": {"yamls/testyamls/testcase3.yaml": ["go v:B"]},
            "4": {"yamls/testyamls/testcase3.yaml": ["go nothing"]},
            "5": {"yamls/testyamls/testcase4.yaml": ["go x"]},
            "6": {"yamls/testyamls/testcase5.yaml": ["go v:A", "go v:B"]},
            "7": {"yamls/testyamls/testcase5.yaml": ["hello v:A"]},
            "8": {"yamls/testyamls/testcase6.yaml": ["go 8"]},
            "9": {"yamls/testyamls/testcase7.yaml": ["go x"]},
            "10": {"yamls/testyamls/testcase8.yaml": ["go x"]},
            "11": {"yamls/testyamls/testcase9.yaml": ["go v:A", "go v:B"]},
            "12": {"yamls/testyamls/testcase10.yaml": ["go v:A", "go v:B"]},
            "13": {"yamls/testyamls/testcase11.yaml": ["go v:A", "go v:B"]},
            "14": {"yamls/testyamls/testcase12.yaml": ["go v:A", "go nothing"]},
            "15": {"yamls/testyamls/testcase13.yaml": ["go v:A", "go v:B"]},
            "16": {"yamls/testyamls/testcase14.yaml": ["go"]},
            "17": {"yamls/testyamls/testcase15.yaml": ["go a:on b:on", "go a:off"]},
            "18": {
                "yamls/testyamls/test.yaml": [
                    "today: 2026/02/05, Name2 (vibe: Vibe1)",
                    "sub: WOW!! mood: Mood2 , equip: Slacks foobar",
                    "today: foobarBarFugahogeHogeBazbaz",
                    "sub: WOW!! mood: Mood1 , equip: Blouse ",
                    "today: 2026/07/21, Name1 (vibe: ) foobarBarFugahogeHogeBazbaz",
                ]
            },
            "19": {
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
            "20": {
                "yamls/testyamls/test2.yaml": [
                    "start name:alice boost month:04 tag:a tag:b miss:bad side"
                ]
            },
        }
    )
    dump_json(result, "debug")
    print(f"Result:{result == CORRECT_RESULT}")


debug()
