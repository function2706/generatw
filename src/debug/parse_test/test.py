import re
from typing import Any

import yaml


def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_field(field: dict) -> dict:
    result = {
        "capturegrp": field.get("capturegrp", 0),
        "priority": field.get("priority"),
    }

    if "maps" in field:
        result["type"] = "maps"
        result["table"] = field["maps"]
    elif "ranges" in field:
        result["type"] = "ranges"
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


def eval_field(text: str, pattern: str, field: dict) -> list[str]:
    try:
        m = re.search(pattern, text)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern: {pattern}") from e
    if not m:
        if "default" in field:
            return [field["default"]]
        return []

    grp = field.get("capturegrp", 0)
    value = m.group(grp)

    if field["type"] == "maps":
        table = field["table"]
        if value in table:
            return [table[value]]
        elif "default" in field:
            return [field["default"]]
        return []

    elif field["type"] == "ranges":
        out: list[str] = []
        for prompt, values in field["table"].items():
            if value in values:
                out.append(prompt)
        if not out and "default" in field:
            return [field["default"]]
        return out

    else:
        raise ValueError(f"Unknown field type: {field['type']}")


def make_prompt(text: str, rule: dict) -> str:
    if not check_ignition(text, rule["ignition"]):
        return ""

    collected: list[tuple[int, str]] = []

    for pattern, field in rule["fields"].items():
        prompts = eval_field(text, pattern, field)
        for p in prompts:
            collected.append((field["priority"], p))

    collected.sort(key=lambda x: x[0])
    return ",".join(p for _, p in collected)


# -------------------------------------------------------------------------

if __name__ == "__main__":
    data = load_yaml("src/debug/parse_test/test.yaml")
    rule = normalize_rule(data["rule"])
    resolve_priorities(rule["fields"])
    text = "today: 2026/02/05, Name2 (vibe: )"
    print(make_prompt(text, rule))
