import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

import yaml


@dataclass(frozen=True)
class KeyName:
    pattern = "pattern"
    priority = "priority"
    capturegrp = "capturegrp"
    lifetime = "lifetime"
    ruletype = "ruletype"
    maps = "maps"
    ranges = "ranges"
    default = "default"
    table = "table"
    positive = "positive"
    negative = "negative"
    conditions = "conditions"


class ValName:
    stable = "stable"
    volatile = "volatile"


@dataclass
class EasyToken:
    """
    '(foo:1.2)' -> (token='foo', weight=1.2)
    """

    token: str = ""
    weight: float = ""

    @classmethod
    def make(cls, original_token: str):
        m = re.fullmatch(r"\(?(\w+)(?::([0-9.]+))?\)?", original_token)
        if not m:
            return cls("", "")
        token, weight = m.groups()
        return cls(token=token, weight=1.0 if weight is None else float(weight))

    @property
    def tostr(self) -> str:
        return f"({self.token}:{self.weight})"


@dataclass
class PromptRule:
    """
    maps:
        {'xxx': {'positive': 'pos1,(pos2:1.2)', 'negative': 'neg1'}}
          -> (['xxx'], [(pos1, 1.0), (pos2, 1.2)], [(neg1, 1.0)])
        {'xxx': {'positive': 'pos1,(pos2:1.2)'}} -> (['xxx'], [(pos1, 1.0), (pos2, 1.2)], [])
        {'xxx': {'negative': 'neg1'} -> (['xxx'], [], [(neg1, 1.0)])}
        {'xxx': 'pos1,(pos2:1.2)'} -> (['xxx'], [(pos1, 1.0), (pos2, 1.2)], [])
    ranges:
        {'pos1,(pos2:1.2)': {'conditions': ['con1', 'con2'], 'negative': 'neg1'}}
          -> (['con1', 'con2'], [(pos1, 1.0), (pos2, 1.2)], [(neg1, 1.0)])
        {'pos1,(pos2:1.2)': ['con1', 'con2']}
          -> (['con1', 'con2'], [(pos1, 1.0), (pos2, 1.2)], [])
    default:
        プロンプトのパース規則は maps と同じ, subtext は空
    """

    subtext: list[str] = ""
    positive: list[EasyToken] = field(default_factory=list[EasyToken])
    negative: list[EasyToken] = field(default_factory=list[EasyToken])

    @classmethod
    def make(cls, key: str, val: str | dict | list, is_maps: bool = True):
        def parse_list(s: str | None) -> list[EasyToken]:
            if not s:
                return []
            parts = [p.strip() for p in s.split(",") if p.strip()]
            return [EasyToken.make(p) for p in parts]

        if key == KeyName.default:
            subtext = []
            if isinstance(val, str):
                positive = parse_list(val)
                negative = []
            elif isinstance(val, dict):
                positive = parse_list(val.get(KeyName.positive))
                negative = parse_list(val.get(KeyName.negative))
            else:
                raise ValueError
        elif is_maps:
            subtext = [key]
            if isinstance(val, str):
                # {'xxx': 'pos1,(pos2:1.2)'} 型
                positive = parse_list(val)
                negative = []
            elif isinstance(val, dict):
                positive = parse_list(val.get(KeyName.positive))
                negative = parse_list(val.get(KeyName.negative))
            else:
                raise ValueError
        else:
            positive = parse_list(key)
            if isinstance(val, list):
                # {'pos1,(pos2:1.2)': ['con1', 'con2']} 型
                subtext = val
                negative = []
            elif isinstance(val, dict):
                # {'pos1,(pos2:1.2)': {'conditions': ['con1', 'con2'], 'negative': 'neg1'}} 型
                subtext = val.get(KeyName.conditions, [])
                negative = parse_list(val.get(KeyName.negative))
            else:
                raise ValueError

        return cls(subtext=subtext, positive=positive, negative=negative)


@dataclass
class Field:
    """
    capturegrp, priority, is_stable は指定がなければ 0, -1(最低優先度), False(Volatile)
    """

    pattern: str = ""
    capturegrp: int = 0
    priority: int = -1
    is_stable: bool = False
    rules: list[PromptRule] = field(default_factory=list)
    default: PromptRule = field(default_factory=PromptRule)

    @classmethod
    def make(cls, field: dict[str, dict]):
        obj = cls()

        if KeyName.pattern in field:
            obj.pattern = field.get(KeyName.pattern)
        else:
            raise ValueError

        if KeyName.capturegrp in field:
            obj.capturegrp = int(field.get(KeyName.capturegrp))

        if KeyName.priority in field:
            obj.priority = int(field.get(KeyName.priority))

        if KeyName.lifetime in field and field.get(KeyName.lifetime) == ValName.stable:
            obj.is_stable = True

        if KeyName.maps in field:
            for key, val in field.get(KeyName.maps).items():
                obj.rules.append(PromptRule.make(key=key, val=val, is_maps=True))
        elif KeyName.ranges in field:
            for key, val in field.get(KeyName.ranges).items():
                obj.rules.append(PromptRule.make(key=key, val=val, is_maps=False))
        else:
            raise ValueError

        if KeyName.default in field:
            val = field.get(KeyName.default)
            obj.default = PromptRule.make(KeyName.default, val)

        return obj


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_field(field: dict) -> dict:
    result = {
        KeyName.capturegrp: field.get(KeyName.capturegrp, 0),
        KeyName.priority: field.get(KeyName.priority),
        KeyName.lifetime: field.get(KeyName.lifetime),
    }

    if KeyName.maps in field:
        result[KeyName.ruletype] = KeyName.maps
        result[KeyName.table] = field[KeyName.maps]
    elif KeyName.ranges in field:
        result[KeyName.ruletype] = KeyName.ranges
        result[KeyName.table] = field[KeyName.ranges]
    else:
        raise ValueError

    if KeyName.default in field:
        result[KeyName.default] = field[KeyName.default]

    return result


def normalize_ignition(ignition: dict) -> dict:
    """
    発火条件を正規化する

    Args:
        ignition (dict): YAMLから読み込んだ ignition 定義

    Raises:
        ValueError: any または all のいずれも定義されていない場合

    Returns:
        dict: 正規化された発火条件 (mode: "any"|"all", patterns: リスト)
    """
    if "any" in ignition:
        return {"mode": "any", "patterns": ignition["any"]}
    elif "all" in ignition:
        return {"mode": "all", "patterns": ignition["all"]}
    else:
        raise ValueError("ignition must contain any or all")


def collect_fields(node: dict, out: dict[str, dict]) -> None:
    """
    ネストされた YAML 構造から再帰的にフィールド定義を収集する\n
    pattern キーを持つオブジェクトをフィールドとして認識し,\n
    それ以外は再帰的に探索する

    Args:
        node (dict): 探索対象のノード
        out (dict[str, dict]): 収集結果を格納する辞書 (pattern 文字列がキー)
    """
    if not isinstance(node, dict):
        return

    if KeyName.pattern in node:
        pattern = node[KeyName.pattern]
        field = normalize_field(node)
        out[pattern] = field
        return

    for v in node.values():
        collect_fields(v, out)


def normalize_rule(rule: dict[str, Any]) -> dict:
    """
    ルール定義全体を正規化する

    Args:
        rule (dict[str, Any]): 正規化されたルール\n
                               (ignition, fields, common_positive, common_negativeを含む)

    Returns:
        dict: YAML から読み込んだルール定義
    """
    out: dict[str, Any] = {
        "ignition": normalize_ignition(rule["ignition"]),
        "fields": {},
    }

    if "POSITIVE" in rule:
        out["common_positive"] = rule["POSITIVE"]
    if "NEGATIVE" in rule:
        out["common_negative"] = rule["NEGATIVE"]

    for k, v in rule.items():
        if k in ("ignition", "POSITIVE", "NEGATIVE"):
            continue
        collect_fields(v, out["fields"])

    return out


yaml_dict = load_yaml("src/debug/parse_test/test.yaml")
print(json.dumps(yaml_dict, indent=2))

d = {
    "pattern": "mood:\\s([^\\)]*)\\s",
    "priority": 1,
    "capturegrp": 1,
    "lifetime": "stable",
    "ranges": {
        "spring": ["03", "04", "05", "06"],
        "summer": ["07", "08"],
        "autumn": ["09", "10"],
        "winter": {"conditions": ["11", "12", "01", "02"], "negative": "HOT"},
    },
    "default": "mood3",
}
r = Field.make(d)
print(json.dumps(asdict(r), indent=2))
