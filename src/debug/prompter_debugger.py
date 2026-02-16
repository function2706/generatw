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
    "CASE 'match'": {"testcase1-1: 'today Name2'": {"POS": "bar", "NEG": "baz", "FLAGS": []}},
    "CASE 'int or string'": {"testcase2-1: 'go id:10'": {"POS": "ten", "NEG": "", "FLAGS": []}},
    "CASE 'default'": {"testcase3-1: 'go v:B'": {"POS": "zzz", "NEG": "", "FLAGS": []}},
    "CASE 'no match'": {"testcase3-1: 'go nothing'": {"POS": "", "NEG": "", "FLAGS": []}},
    "CASE 'weight dedupe'": {"testcase4-1: 'go x'": {"POS": "(foo:1.5)", "NEG": "", "FLAGS": []}},
    "CASE 'stable push stable out'": {
        "testcase5-1: 'go v:A'": {"POS": "alpha", "NEG": "", "FLAGS": []},
        "testcase5-2: 'go v:B'": {"POS": "beta", "NEG": "", "FLAGS": []},
    },
    "CASE 'wetty'": {"testcase5-1: 'hello v:A'": {"POS": "", "NEG": "", "FLAGS": []}},
    "CASE 'ranges'": {
        "testcase6-1: 'go 8'": {"POS": "hot", "NEG": "cold", "FLAGS": []},
        "testcase6-2: 'go 5'": {"POS": "warm", "NEG": "cold", "FLAGS": []},
        "testcase6-3: 'go 2'": {"POS": "cool", "NEG": "", "FLAGS": []},
        "testcase6-4: 'go 9'": {"POS": "warm", "NEG": "", "FLAGS": []},
        "testcase6-5: 'go 1'": {"POS": "", "NEG": "heat", "FLAGS": []},
    },
    "CASE 'common'": {"testcase7-1: 'go x'": {"POS": "foo,common", "NEG": "", "FLAGS": []}},
    "CASE 'priority dedupe'": {
        "testcase8-1: 'go x'": {"POS": "first,second", "NEG": "", "FLAGS": []}
    },
    "CASE 'pos pop, neg vanish'": {
        "testcase9-1: 'go v:A'": {"POS": "apple", "NEG": "bad", "FLAGS": []},
        "testcase9-2: 'go v:B'": {"POS": "banana", "NEG": "", "FLAGS": []},
    },
    "CASE 'neg pop, pos vanish'": {
        "testcase10-1: 'go v:A'": {"POS": "apple", "NEG": "", "FLAGS": []},
        "testcase10-2: 'go v:B'": {"POS": "", "NEG": "bad", "FLAGS": []},
    },
    "CASE 'both vanish'": {
        "testcase11-1: 'go v:A'": {"POS": "apple", "NEG": "bad", "FLAGS": []},
        "testcase11-2: 'go v:B'": {"POS": "", "NEG": "", "FLAGS": []},
    },
    "CASE 'volatile vanish soon'": {
        "testcase12-1: 'go v:A'": {"POS": "apple", "NEG": "", "FLAGS": []},
        "testcase12-2: 'go nothing'": {"POS": "", "NEG": "", "FLAGS": []},
    },
    "CASE 'no match, default pop'": {
        "testcase13-1: 'go v:A'": {"POS": "apple", "NEG": "", "FLAGS": []},
        "testcase13-2: 'go v:B'": {"POS": "default", "NEG": "", "FLAGS": []},
    },
    "CASE 'empty token'": {"testcase14-1: 'go'": {"POS": "", "NEG": "", "FLAGS": []}},
    "CASE 'another rule kill nobody'": {
        "testcase15-1: 'go a:on b:on'": {"POS": "A,B", "NEG": "", "FLAGS": []},
        "testcase15-2: 'go b:off'": {"POS": "A", "NEG": "", "FLAGS": []},
        "testcase15-3: 'go a:off'": {"POS": "", "NEG": "", "FLAGS": []},
    },
    "CASE 'interval'": {
        "testcase16-1: 'go 20'": {"POS": "low,bad", "NEG": "good,high,ok", "FLAGS": []},
        "testcase16-2: 'go 50'": {"POS": "low,bad,middle", "NEG": "good,high", "FLAGS": []},
        "testcase16-3: 'go 55'": {"POS": "bad,middle", "NEG": "high", "FLAGS": []},
        "testcase16-4: 'go 97'": {"POS": "perfect", "NEG": "", "FLAGS": []},
        "testcase16-5: 'go 10'": {"POS": "low,bad", "NEG": "good,high,ok", "FLAGS": []},
        "testcase16-6: 'go 75'": {"POS": "average", "NEG": "", "FLAGS": []},
    },
    "CASE 'flag'": {
        "testcase17-1: 'environment: room, sunny'": {
            "POS": "room",
            "NEG": "",
            "FLAGS": ["indoors", "private"],
        },
        "testcase17-2: 'character: Light Style, Umbrella'": {
            "POS": "room,light style",
            "NEG": "",
            "FLAGS": ["indoors", "private"],
        },
        "testcase17-3: 'character: Casual Style'": {
            "POS": "room,casual style",
            "NEG": "",
            "FLAGS": ["indoors", "private"],
        },
        "testcase17-4: 'environment: office, rainy'": {
            "POS": "office",
            "NEG": "",
            "FLAGS": ["indoors", "public"],
        },
        "testcase17-5: 'character: Formal Style, Caps'": {
            "POS": "office,formal style",
            "NEG": "",
            "FLAGS": ["indoors", "public"],
        },
        "testcase17-6: 'environment: city, windy'": {
            "POS": "city,windy",
            "NEG": "",
            "FLAGS": ["cold", "outdoors", "public"],
        },
        "testcase17-7: 'character: CoolBiz Style, Caps'": {
            "POS": "city,windy",
            "NEG": "",
            "FLAGS": ["cold", "outdoors", "public"],
        },
    },
    "CASE 'flag formula'": {
        "testcase17-1: 'TEST testp'": {"POS": "p", "NEG": "", "FLAGS": ["p"]},
        "testcase17-2: 'TEST test1'": {"POS": "", "NEG": "", "FLAGS": ["p"]},
        "testcase17-3: 'TEST test2'": {"POS": "", "NEG": "", "FLAGS": ["p"]},
        "testcase17-4: 'TEST testq'": {"POS": "q", "NEG": "", "FLAGS": ["p", "q"]},
        "testcase17-5: 'TEST test1'": {"POS": "test1", "NEG": "", "FLAGS": ["p", "q"]},
        "testcase17-6: 'TEST test2'": {"POS": "test2", "NEG": "", "FLAGS": ["p", "q"]},
    },
    "CASE 'flag simple'": {
        "testcase17-1: 'TEST simple2'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase17-2: 'TEST simple1'": {"POS": "sim1", "NEG": "", "FLAGS": ["sim1"]},
        "testcase17-3: 'TEST simple2'": {"POS": "sim2", "NEG": "", "FLAGS": ["sim1"]},
    },
    "CASE 'flag circ'": {
        "testcase17-1: 'TEST circ1'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase17-2: 'TEST circ2'": {"POS": "", "NEG": "", "FLAGS": []},
    },
    "CASE 'flag self'": {
        "testcase17-1: 'TEST self1'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase17-2: 'TEST self2'": {"POS": "", "NEG": "", "FLAGS": []},
    },
    "CASE 'flag add-remove'": {
        "testcase17-1: 'TEST scene1'": {"POS": "scene1", "NEG": "", "FLAGS": ["s1"]},
        "testcase17-2: 'TEST scene2'": {"POS": "scene2", "NEG": "", "FLAGS": ["s2"]},
        "testcase17-3: 'TEST scene1'": {"POS": "scene1", "NEG": "", "FLAGS": ["s1", "s2"]},
        "testcase17-4: 'TEST Scene2'": {"POS": "scene2_p", "NEG": "", "FLAGS": ["s2", "s2_p"]},
        "testcase17-5: 'TEST scene3'": {"POS": "scene3", "NEG": "", "FLAGS": ["s2", "s2_p"]},
        "testcase17-6: 'TEST scene4'": {"POS": "", "NEG": "", "FLAGS": ["s2", "s2_p"]},
        "testcase17-7: 'TEST Scene3'": {
            "POS": "scene3_p",
            "NEG": "",
            "FLAGS": ["s2", "s2_p", "s3"],
        },
        "testcase17-8: 'TEST scene4'": {"POS": "scene4", "NEG": "", "FLAGS": ["s2", "s2_p", "s3"]},
    },
    "CASE 'flag ranges'": {
        "testcase17-1: 'TEST range4'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase17-2: 'TEST range7'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase17-3: 'TEST range1'": {"POS": "low", "NEG": "", "FLAGS": ["range_low"]},
        "testcase17-4: 'TEST range8'": {"POS": "", "NEG": "", "FLAGS": ["range_low"]},
        "testcase17-5: 'TEST range5'": {
            "POS": "middle",
            "NEG": "",
            "FLAGS": ["range_low", "range_middle"],
        },
        "testcase17-6: 'TEST range9'": {
            "POS": "high",
            "NEG": "",
            "FLAGS": ["range_low", "range_middle"],
        },
    },
    "CASE 'flag intervals'": {
        "testcase17-1: 'TEST interval4'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase17-2: 'TEST interval7'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase17-3: 'TEST interval1'": {"POS": "low", "NEG": "", "FLAGS": ["interval_low"]},
        "testcase17-4: 'TEST interval8'": {"POS": "", "NEG": "", "FLAGS": ["interval_low"]},
        "testcase17-5: 'TEST interval5'": {
            "POS": "middle",
            "NEG": "",
            "FLAGS": ["interval_low", "interval_middle"],
        },
        "testcase17-6: 'TEST interval9'": {
            "POS": "high",
            "NEG": "",
            "FLAGS": ["interval_low", "interval_middle"],
        },
    },
    "CASE 'flag default'": {
        "testcase17-1: 'TEST phase2'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase17-2: 'TEST phase3'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase17-3: 'TEST phase1'": {"POS": "p1", "NEG": "", "FLAGS": ["p1"]},
        "testcase17-4: 'TEST phase2'": {"POS": "default", "NEG": "", "FLAGS": ["default", "p1"]},
        "testcase17-5: 'TEST phase3'": {"POS": "default", "NEG": "", "FLAGS": ["default", "p1"]},
        "testcase17-6: 'TEST phase2'": {"POS": "p2", "NEG": "", "FLAGS": ["default", "p1"]},
    },
    "CASE 'flag stable'": {
        "testcase17-1: 'TEST volatile1'": {"POS": "volatile1", "NEG": "", "FLAGS": ["volatile1"]},
        "testcase17-2: 'TEST stable2'": {"POS": "", "NEG": "", "FLAGS": ["volatile1"]},
        "testcase17-3: 'TEST volatile1'": {"POS": "volatile1", "NEG": "", "FLAGS": ["volatile1"]},
        "testcase17-4: 'TEST stable1'": {
            "POS": "stable1",
            "NEG": "",
            "FLAGS": ["stable1", "volatile1"],
        },
        "testcase17-5: 'TEST volatile3'": {
            "POS": "stable1,volatile3",
            "NEG": "",
            "FLAGS": ["stable1"],
        },
        "testcase17-6: 'TEST volatile2'": {
            "POS": "volatile2",
            "NEG": "",
            "FLAGS": ["stable1", "volatile2"],
        },
    },
    "CASE 'essential'": {
        "testcase18-1: 'meta room day'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase18-2: 'main good crying'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase18-3: 'main name1 good'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase18-4: 'main name1 good age:35'": {
            "POS": "name1,adult,good,common main pos",
            "NEG": "common main neg",
            "FLAGS": [],
        },
        "testcase18-5: 'meta city morning'": {
            "POS": "name1,adult,city,morning,common meta pos",
            "NEG": "common meta neg",
            "FLAGS": [],
        },
        "testcase18-6: 'main smile'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase18-7: 'meta JPN morning room'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase18-8: 'main name2 bad age:70'": {
            "POS": "name2,old,bad,common main pos",
            "NEG": "common main neg",
            "FLAGS": [],
        },
        "testcase18-9: 'dummy'": {
            "POS": "name2,old,bad,common main pos",
            "NEG": "common main neg",
            "FLAGS": [],
        },
        "testcase18-10: 'meta room day'": {
            "POS": "name2,old,room,day,common meta pos",
            "NEG": "common meta neg",
            "FLAGS": [],
        },
        "testcase18-11: 'meta UK city'": {"POS": "", "NEG": "", "FLAGS": []},
        "testcase18-12: 'meta city night US'": {"POS": "", "NEG": "", "FLAGS": []},
    },
    "CASE 'same rule id'": {
        "testcase19-1: 'main name:hogemaru,vibe:good'": {
            "POS": "hogemaru,good",
            "NEG": "",
            "FLAGS": [],
        },
        "testcase19-2: 'meta city'": {"POS": "hogemaru,city", "NEG": "", "FLAGS": []},
        "testcase19-3: 'meta name:fugami,room'": {"POS": "fugami,room", "NEG": "", "FLAGS": []},
        "testcase19-4: 'main vibe:bad'": {"POS": "fugami,bad", "NEG": "", "FLAGS": []},
        "testcase19-5: 'main vibe:normal'": {"POS": "fugami", "NEG": "", "FLAGS": []},
        "testcase19-6: 'meta name:foota,vibe:good'": {"POS": "", "NEG": "", "FLAGS": []},
    },
    "CASE 'multiple match'": {
        "testcase20-1: 'go hello world foo bar'": {
            "POS": "hello_greeting,world_place,foo_item,bar_item",
            "NEG": "",
            "FLAGS": [],
        },
        "testcase20-2: 'go hello'": {"POS": "hello_greeting", "NEG": "", "FLAGS": []},
        "testcase20-3: 'go hello hello'": {"POS": "hello_greeting", "NEG": "", "FLAGS": []},
        "testcase20-4: 'go unknown'": {"POS": "", "NEG": "", "FLAGS": []},
    },
    "CASE 'same rule id multi'": {
        "testcase21-1: 'main name:alice'": {"POS": "alice", "NEG": "", "FLAGS": []},
        "testcase21-2: 'rule name:bob'": {"POS": "bob", "NEG": "", "FLAGS": []},
        "testcase21-3: 'rule name:charlie'": {"POS": "charlie", "NEG": "", "FLAGS": []},
        "testcase21-4: 'main name:bob'": {"POS": "bob", "NEG": "", "FLAGS": []},
        "testcase21-5: 'main name:bad'": {"POS": "", "NEG": "", "FLAGS": []},
    },
    "CASE 'complex 1'": {
        "test-1: 'today: 2026/02/05, Name2 (vibe: Vibe1)'": {
            "POS": "name2,feature2,vibe1,winter,common positive",
            "NEG": "NAME2,HOT,common negative",
            "FLAGS": [],
        },
        "test-2: 'sub: WOW!! mood: Mood2 , equip: Slacks foobar'": {
            "POS": "name2,feature2,vibe1,winter,mood2,pants,sub common positive",
            "NEG": "NAME2,HOT,MOOD2,skirt,sub common negative",
            "FLAGS": [],
        },
        "test-3: 'today: foobarBarFugahogeHogeBazbaz'": {
            "POS": "name2,feature2,vibe1,winter,mood2,fuga,(hoge:1.3),foo,(bar:1.3),baz,common positive",  # noqa: E501
            "NEG": "NAME2,HOT,MOOD2,FUGA,HOGE,FOO,(nope:1.4),BAR,nyome,BAZ,common negative",
            "FLAGS": [],
        },
        "test-4: 'sub: WOW!! mood: Mood1 , equip: Blouse point: 20'": {
            "POS": "name2,feature2,vibe1,winter,mood1,low,bad,sub common positive",
            "NEG": "NAME2,HOT,good,high,ok,sub common negative",
            "FLAGS": [],
        },
        "test-5: 'today: 2026/07/21, Name1 (vibe: ) foobarBarFugahogeHogeBazbaz'": {
            "POS": "mood1,name1,feature1,vibe3,fuga,(hoge:1.3),summer,foo,(bar:1.3),baz,common positive",  # noqa: E501
            "NEG": "FUGA,HOGE,FOO,(nope:1.4),BAR,nyome,BAZ,common negative",
            "FLAGS": [],
        },
    },
    "CASE 'complex 2'": {
        "test2-1: 'start name:alice boost month:04 tag:a tag:b miss:bad side'": {
            "POS": "(girl:1.5),spring,A,B,DEF,SIDE_P,commonA",
            "NEG": "snow,SIDE_N,commonN",
            "FLAGS": [],
        }
    },
    "CASE 'complex 3'": {
        "test3-1: 'today name:alice m:03 vibe:happy'": {
            "POS": "alice,spring,happy,main_common_p",
            "NEG": "main_common_n",
            "FLAGS": [],
        },
        "test3-2: 'today m:03'": {
            "POS": "alice,spring,main_common_p",
            "NEG": "main_common_n",
            "FLAGS": [],
        },
        "test3-3: 'today name:bob boost m:12'": {
            "POS": "bob,(alice:1.5),winter,main_common_p",
            "NEG": "cold,main_common_n",
            "FLAGS": [],
        },
        "test3-4: 'hello name:alice'": {
            "POS": "bob,(alice:1.5),winter,main_common_p",
            "NEG": "cold,main_common_n",
            "FLAGS": [],
        },
        "test3-5: 'sub go mood:good'": {
            "POS": "bob,winter,good,sub_common_p",
            "NEG": "cold,sub_common_n",
            "FLAGS": [],
        },
        "test3-6: 'sub go'": {
            "POS": "bob,winter,good,sub_common_p",
            "NEG": "cold,sub_common_n",
            "FLAGS": [],
        },
        "test3-7: 'sub go mood:bad'": {
            "POS": "bob,winter,sub_common_p",
            "NEG": "cold,BAD,sub_common_n",
            "FLAGS": [],
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

    def debug_texts(self, texts: list[str], with_texts: bool = True) -> dict[str, dict[str, str]]:
        """
        展開中 yaml について texts 内のテキストを順に適用する

        Args:
            texts (list[str]): テスト用テキスト
        """
        yamlname = self.prompter.yamlpath.name.replace(".yaml", "")
        result: dict[str, dict[str, str]] = {}
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

    def debug_clipboard(self) -> dict[str, dict[str, str]]:
        """
        展開中 yaml について現在のクリップボードのテキストを適用する
        """
        clipboard = pyperclip.paste()
        return self.debug_texts([clipboard], False)


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
                "yamls/testyamls/testcase15.yaml": [
                    "go a:on b:on",  # a, b ともにマッチ
                    "go b:off",  # b はマッチするもルールが存在せず消去, 次回継続なし
                    "go a:off",  # a はマッチし, ルールが存在するが空文字列なのでプロンプト化されず
                ]
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
            "flag": {
                "yamls/testyamls/testcase17.yaml": [
                    "environment: room, sunny",
                    "character: Light Style, Umbrella",
                    "character: Casual Style",
                    "environment: office, rainy",
                    "character: Formal Style, Caps",
                    "environment: city, windy",
                    "character: CoolBiz Style, Caps",
                ]
            },
            "flag formula": {
                "yamls/testyamls/testcase17.yaml": [
                    "TEST testp",
                    "TEST test1",
                    "TEST test2",
                    "TEST testq",
                    "TEST test1",
                    "TEST test2",
                ]
            },
            "flag simple": {
                "yamls/testyamls/testcase17.yaml": ["TEST simple2", "TEST simple1", "TEST simple2"]
            },
            "flag circ": {"yamls/testyamls/testcase17.yaml": ["TEST circ1", "TEST circ2"]},
            "flag self": {"yamls/testyamls/testcase17.yaml": ["TEST self1", "TEST self2"]},
            "flag add-remove": {
                "yamls/testyamls/testcase17.yaml": [
                    "TEST scene1",
                    "TEST scene2",
                    "TEST scene1",
                    "TEST Scene2",
                    "TEST scene3",
                    "TEST scene4",
                    "TEST Scene3",
                    "TEST scene4",
                ]
            },
            "flag ranges": {
                "yamls/testyamls/testcase17.yaml": [
                    "TEST range4",
                    "TEST range7",
                    "TEST range1",
                    "TEST range8",
                    "TEST range5",
                    "TEST range9",
                ]
            },
            "flag intervals": {
                "yamls/testyamls/testcase17.yaml": [
                    "TEST interval4",
                    "TEST interval7",
                    "TEST interval1",
                    "TEST interval8",
                    "TEST interval5",
                    "TEST interval9",
                ]
            },
            "flag default": {
                "yamls/testyamls/testcase17.yaml": [
                    "TEST phase2",
                    "TEST phase3",
                    "TEST phase1",
                    "TEST phase2",
                    "TEST phase3",
                    "TEST phase2",
                ]
            },
            "flag stable": {
                "yamls/testyamls/testcase17.yaml": [
                    "TEST volatile1",
                    "TEST stable2",
                    "TEST volatile1",
                    "TEST stable1",
                    "TEST volatile3",
                    "TEST volatile2",
                ]
            },
            "essential": {
                "yamls/testyamls/testcase18.yaml": [
                    "meta room day",  # meta の essential 未達成(共通プロンプトも非採用)
                    "main good crying",  # main の essential 未達成
                    "main name1 good",  # 同上
                    "main name1 good age:35",  # main の essential 達成, name1 と age が次回も継続
                    "meta city morning",  # meta の essential 達成, 前回継続分も持ち越し
                    "main smile",  # main 未達成, 継続分抹消
                    "meta JPN morning room",  # global essential の name がないので未達成
                    "main name2 bad age:70",  # main 達成
                    "dummy",  # 未点火, 継続分は持ち越し
                    "meta room day",  # name(global) + meta 達成, 未点火を挟んでも継続分は表示される
                    "meta UK city",  # meta 未達成
                    "meta city night US",  # もう name(global) がないので未達成扱い
                ]
            },
            "same rule id": {
                "yamls/testyamls/testcase19.yaml": [
                    "main name:hogemaru,vibe:good",  # name1 は stable なので引き継ぎ, priority は meta.name の 1 に統一されるので先頭 # noqa:E501
                    "meta city",  # name (global essential) が引き継がれているので達成, city は priority 未指定で最後尾 # noqa:E501
                    "meta name:fugami,room",  # ID=name で上書き, hogemaru -> fugami
                    "main vibe:bad",  # やはり name が引き継がれているので達成, name は stable な持ち越しなので先頭 # noqa:E501
                    "main vibe:normal",  # マッチするもルールがないので削除
                    "meta name:foota,vibe:good",  # name マッチせず, global essential 未達成
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
            "same rule id multi": {
                "yamls/testyamls/testcase21.yaml": [
                    "main name:alice",
                    "rule name:bob",
                    "rule name:charlie",
                    "main name:bob",
                    "main name:bad",
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
    print("---------------------------------------------------------------------------")
    for key, test_result in result.items():
        correct_result = CORRECT_RESULT.get(key)
        if correct_result is None:
            print(f"NEW - {key}")
        else:
            if test_result == correct_result:
                print(f"OK  - {key}")
            else:
                print(f"NG  - {key}")
                dump_json(dict_diff(test_result, correct_result), "diff")


debug()
