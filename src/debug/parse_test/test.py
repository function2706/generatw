import re
from typing import Any, Literal

import yaml

# 定数
FIELD_TYPE_MAPS = "maps"
FIELD_TYPE_RANGES = "ranges"
SIDE_POSITIVE = "positive"
SIDE_NEGATIVE = "negative"

# 型エイリアス
PromptMap = dict[str, float]
PromptResult = dict[Literal["positive", "negative"], PromptMap]

PROMPT_RE = re.compile(
    r"""
    \(\s*
      (?P<token>[^:()\s]+)
      (?:\s*:\s*(?P<weight>[0-9.]+))?
    \s*\)
    |
    (?P<bare>[^,()\s]+)
    """,
    re.VERBOSE,
)


def parse_prompts(s: str) -> PromptMap:
    """
    "FOO,(nope:1.3)" -> {"FOO": 1.0, "nope": 1.3}
    """
    out: PromptMap = {}

    for m in PROMPT_RE.finditer(s):
        if m.group("bare"):
            token = m.group("bare")
            weight = 1.0
        else:
            token = m.group("token")
            weight = float(m.group("weight") or 1.0)

        out[token] = max(out.get(token, 0.0), weight)

    return out


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_field(field: dict) -> dict:
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
    if "any" in ignition:
        return {"mode": "any", "patterns": ignition["any"]}
    elif "all" in ignition:
        return {"mode": "all", "patterns": ignition["all"]}
    else:
        raise ValueError("ignition must contain any or all")


def collect_fields_recursive(node: dict, out: dict[str, dict]) -> None:
    if not isinstance(node, dict):
        return

    # この dict 自体が field 定義だった場合
    if "pattern" in node:
        pattern = node["pattern"]
        field = normalize_field(node)
        out[pattern] = field
        return

    # それ以外は再帰
    for v in node.values():
        collect_fields_recursive(v, out)


def normalize_rule(rule: dict[str, Any]) -> dict:
    rule_id = rule["id"]

    out: dict[str, Any] = {
        "id": rule_id,
        "ignition": normalize_ignition(rule["ignition"]),
        "fields": {},
    }

    for k, v in rule.items():
        if k in ("id", "ignition"):
            continue
        collect_fields_recursive(v, out["fields"])

    return out


def resolve_priorities(fields: dict[str, dict]) -> None:
    used: set[int] = set()

    # 指定済み priority
    for field in fields.values():
        p = field.get("priority")
        if p is not None:
            while p in used:
                p += 1
            field["priority"] = p
            used.add(p)

    # 未指定
    next_p = max(used, default=0) + 1
    for field in fields.values():
        if field.get("priority") is None:
            while next_p in used:
                next_p += 1
            field["priority"] = next_p
            used.add(next_p)
            next_p += 1


# -------------------------------------------------------------------------


def check_ignition(text: str, ignition: dict) -> bool:
    patterns = ignition["patterns"]
    mode = ignition["mode"]

    if mode == "any":
        return any(re.search(p, text) for p in patterns)
    elif mode == "all":
        return all(re.search(p, text) for p in patterns)
    else:
        raise ValueError(f"Unknown ignition mode: {mode}")


def merge_prompt_map(dst: PromptMap, src: PromptMap) -> None:
    """src を dst にマージ（weight は最大値を採用）"""
    for k, v in src.items():
        dst[k] = max(dst.get(k, 0.0), v)


def add_to_side(out: PromptResult, side: str, tokens: PromptMap) -> None:
    """指定した side (positive/negative) に tokens を追加"""
    out.setdefault(side, {})
    merge_prompt_map(out[side], tokens)


def handle_entry(out: PromptResult, entry: Any) -> None:
    """entry (文字列 or 辞書) を処理して out に追加"""
    if isinstance(entry, str):
        add_to_side(out, SIDE_POSITIVE, parse_prompts(entry))
    elif isinstance(entry, dict):
        for side in (SIDE_POSITIVE, SIDE_NEGATIVE):
            if side in entry:
                add_to_side(out, side, parse_prompts(entry[side]))


def handle_ranges_match(out: PromptResult, key: str, entry: Any, value: str) -> bool:
    """
    ranges タイプのマッチ処理。
    マッチしたら out に追加して True を返す。
    """
    if isinstance(entry, dict):
        coords = entry.get("coordinates", entry.get("coordinates", []))
        if value in coords:
            add_to_side(out, SIDE_POSITIVE, parse_prompts(key))
            if SIDE_NEGATIVE in entry:
                add_to_side(out, SIDE_NEGATIVE, parse_prompts(entry[SIDE_NEGATIVE]))
            return True
    elif isinstance(entry, list):
        if value in entry:
            handle_entry(out, key)
            return True
    return False


def process_match_value(
    value: str,
    field: dict[str, Any],
    out: PromptResult,
) -> None:
    """マッチした値を field の type に応じて処理"""
    field_type = field["type"]
    table = field["table"]
    matched = False

    if field_type == FIELD_TYPE_MAPS:
        if value in table:
            handle_entry(out, table[value])
            matched = True

    elif field_type == FIELD_TYPE_RANGES:
        for key, entry in table.items():
            if handle_ranges_match(out, key, entry, value):
                matched = True

    else:
        raise ValueError(f"Unknown field type: {field_type}")

    # default 処理
    if not matched and "default" in field:
        handle_entry(out, field["default"])


def eval_field(
    text: str,
    pattern: str,
    field: dict[str, Any],
) -> PromptResult:
    """
    戻り値:
    {
      "positive": {token: weight},
      "negative": {token: weight},
    }
    """
    try:
        matches = list(re.finditer(pattern, text))
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {pattern}") from e

    # マッチなし → default があればそれを返す
    if not matches:
        if "default" in field:
            return {SIDE_POSITIVE: parse_prompts(field["default"])}
        return {}

    grp = field.get("capturegrp", 0)
    out: PromptResult = {}

    # 各マッチを処理
    for m in matches:
        value = m.group(grp)
        process_match_value(value, field, out)

    return out


def make_prompt(text: str, rule: dict[str, Any]) -> tuple[str, str]:
    if not check_ignition(text, rule["ignition"]):
        return "", ""

    positive: PromptMap = {}
    negative: PromptMap = {}

    # priority 順にソート
    fields = sorted(
        rule["fields"].items(),
        key=lambda x: x[1]["priority"],
    )

    for pattern, field in fields:
        result = eval_field(text, pattern, field)

        if SIDE_POSITIVE in result:
            merge_prompt_map(positive, result[SIDE_POSITIVE])
        if SIDE_NEGATIVE in result:
            merge_prompt_map(negative, result[SIDE_NEGATIVE])

    def fmt(m: PromptMap) -> str:
        return ",".join(f"({k}:{v})" if v != 1.0 else k for k, v in m.items())

    return fmt(positive), fmt(negative)


# -------------------------------------------------------------------------

if __name__ == "__main__":
    data = load_yaml("src/debug/parse_test/test.yaml")
    rule = normalize_rule(data["rule"])
    resolve_priorities(rule["fields"])
    text = "today: 2026/02/05, Name2 (vibe: )foobarBarfugahogeHoge"
    pos, neg = make_prompt(text, rule)
    print("POS:", pos)
    print("NEG:", neg)
