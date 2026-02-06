import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

import yaml

FIELD_TYPE_MAPS = "maps"
FIELD_TYPE_RANGES = "ranges"
SIDE_POSITIVE = "positive"
SIDE_NEGATIVE = "negative"


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
    """

    subtext: list[str] = ""
    positive: list[EasyToken] = field(default_factory=list[EasyToken])
    negative: list[EasyToken] = field(default_factory=list[EasyToken])

    @classmethod
    def make(cls, d: dict[str, Any], is_maps: bool = True):
        def parse_list(s: str | None) -> list[EasyToken]:
            if not s:
                return []
            parts = [p.strip() for p in s.split(",") if p.strip()]
            return [EasyToken.make(p) for p in parts]

        key, val = next(iter(d.items()))
        if is_maps:
            subtext = [key]
            if isinstance(val, str):
                # {'xxx': 'pos1,(pos2:1.2)'} 型
                positive = parse_list(val)
                negative = []
            elif isinstance(val, dict):
                positive = parse_list(val.get("positive"))
                negative = parse_list(val.get("negative"))
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
                subtext = val.get("conditions", [])
                negative = parse_list(val.get("negative"))
            else:
                raise ValueError

        return cls(subtext=subtext, positive=positive, negative=negative)


def load_yaml(path: str) -> dict:
    """
    YAML ファイルを読み込む

    Args:
        path (str): YAMLファイルのパス

    Returns:
        dict: パースされたYAMLデータ
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_field(field: dict) -> dict:
    """
    フィールド定義を正規化する

    Args:
        field (dict): YAML から読み込んだフィールド定義

    Raises:
        ValueError: maps または ranges のいずれも定義されていない場合

    Returns:
        dict: 正規化されたフィールド定義 (type, table, capturegrp, priority, default を含む)
    """
    result = {
        "capturegrp": field.get("capturegrp", 0),
        "priority": field.get("priority"),
    }

    if "maps" in field:
        result["type"] = FIELD_TYPE_MAPS
        result["table"] = field["maps"]
    elif "ranges" in field:
        result["type"] = FIELD_TYPE_RANGES
        result["table"] = field["ranges"]
    else:
        raise ValueError(f"Unknown field type: {field}")

    if "default" in field:
        result["default"] = field["default"]

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

    if "pattern" in node:
        pattern = node["pattern"]
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
rules: list[dict[str, dict]] = []
for key in yaml_dict:
    rule = normalize_rule(yaml_dict[key])
    print(json.dumps(rule, indent=2))
    rules.append(rule)

d = {"pos1,(pos2:1.2)": ["con1", "con2"]}
r = PromptRule.make(d, False)
print(asdict(r))
