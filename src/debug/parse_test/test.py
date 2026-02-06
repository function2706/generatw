import re
from pathlib import Path
from typing import Any, Literal

import yaml

FIELD_TYPE_MAPS = "maps"
FIELD_TYPE_RANGES = "ranges"
SIDE_POSITIVE = "positive"
SIDE_NEGATIVE = "negative"

PromptMap = dict[str, float]
PromptResult = dict[Literal["positive", "negative"], PromptMap]


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


def resolve_priorities(fields: dict[str, dict]) -> None:
    """
    フィールドの priority 値を解決し, 重複を自動調整する\n
    未指定の priority には最大値 +1 を自動割り当てする\n
    重複した priority は +1 して調整される

    Args:
        fields (dict[str, dict]): 正規化されたフィールド辞書(破壊的に変更される)
    """
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


def check_ignition(text: str, ignition: dict) -> bool:
    """
    テキストが発火条件を満たすかチェックする

    Args:
        text (str): 検査対象のテキスト
        ignition (dict): 正規化された発火条件

    Raises:
        ValueError: 不明なignitionモードの場合

    Returns:
        bool: 発火条件を満たす場合 True
    """
    patterns = ignition["patterns"]
    mode = ignition["mode"]

    if mode == "any":
        return any(re.search(p, text) for p in patterns)
    elif mode == "all":
        return all(re.search(p, text) for p in patterns)
    else:
        raise ValueError(f"Unknown ignition mode: {mode}")


def merge_prompt_map(dst: PromptMap, src: PromptMap) -> None:
    """
    src を dst にマージする (weight は最大値を採用)

    Args:
        dst (PromptMap): マージ先(破壊的に変更される)
        src (PromptMap): マージ元
    """
    for k, v in src.items():
        dst[k] = max(dst.get(k, 0.0), v)


def add_to_side(out: PromptResult, side: str, tokens: PromptMap) -> None:
    """
    指定した side (positive/negative) に tokens を追加する

    Args:
        out (PromptResult): 追加先(破壊的に変更される)
        side (str): "positive" または "negative"
        tokens (PromptMap): 追加するトークンマップ
    """
    out.setdefault(side, {})
    merge_prompt_map(out[side], tokens)


def parse_prompts(s: str) -> PromptMap:
    """
    プロンプト文字列をパースしてトークンマップに変換する

    例:
        "foo,(bar:1.3)" -> {"foo": 1.0, "bar": 1.3}
        "blue hair,red eyes" -> {"blue hair": 1.0, "red eyes": 1.0}

    Args:
        s (str): プロンプト文字列

    Returns:
        PromptMap: トークンと重みのマップ
    """
    out: PromptMap = {}
    PROMPT_RE = re.compile(
        r"""
        \(\s*
        (?P<token>[^:()]+)
        (?:\s*:\s*(?P<weight>[0-9.]+))?
        \s*\)
        |
        (?P<bare>[^,()]+)
        """,
        re.VERBOSE,
    )

    for m in PROMPT_RE.finditer(s):
        if m.group("bare"):
            token = m.group("bare").strip()
            weight = 1.0
        else:
            token = m.group("token").strip()
            weight = float(m.group("weight") or 1.0)

        out[token] = max(out.get(token, 0.0), weight)

    return out


def handle_entry(out: PromptResult, entry: Any) -> None:
    """
    entry (文字列 or 辞書)を処理して out に追加する

    Args:
        out (PromptResult): 追加先(破壊的に変更される)
        entry (Any): 文字列 (positive のみ)または辞書 (positive/negative 分離)
    """
    if isinstance(entry, str):
        add_to_side(out, SIDE_POSITIVE, parse_prompts(entry))
    elif isinstance(entry, dict):
        for side in (SIDE_POSITIVE, SIDE_NEGATIVE):
            if side in entry:
                add_to_side(out, side, parse_prompts(entry[side]))


def handle_ranges_match(out: PromptResult, key: str, entry: Any, value: str) -> bool:
    """
    ranges タイプのマッチ処理を行う\n
    マッチした場合, キー自体が positive プロンプトとして使用され,\n
    negative が定義されていればそれも追加される

    Args:
        out (PromptResult): 追加先(破壊的に変更される)
        key (str): プロンプトキー (positive として使用される)
        entry (Any): range 定義 (coordinates と negative を含む辞書, またはリスト)
        value (str): マッチ対象の値

    Returns:
        bool: マッチした場合 True
    """
    if isinstance(entry, dict):
        coords = entry.get("conditions", [])
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


def process_match_value(value: str, field: dict[str, Any], out: PromptResult) -> None:
    """
    マッチした値をfieldのtypeに応じて処理する

    Args:
        value (str): 抽出された値
        field (dict[str, Any]): フィールド定義
        out (PromptResult): 追加先(破壊的に変更される)

    Raises:
        ValueError: 不明な field タイプの場合
    """
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


def eval_field(text: str, pattern: str, field: dict[str, Any]) -> PromptResult:
    """
    フィールドのパターンマッチングを行い, プロンプトを生成する

    Args:
        text (str): 検索対象のテキスト
        pattern (str): 正規表現パターン
        field (dict[str, Any]): フィールド定義

    Raises:
        ValueError: 不正な正規表現パターンの場合

    Returns:
        PromptResult: positive/negative のトークンマップを含む辞書
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


def make_prompt(text: str, rule: dict[str, dict]) -> tuple[str, str]:
    """
    テキストからプロンプトを生成する

    Args:
        text (str): 入力テキスト
        rule (dict[str, Any]): 正規化されたルール定義

    Returns:
        tuple[str, str]: (positive_prompt, negative_prompt) のタプル
    """
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

    pos_str = fmt(positive)
    neg_str = fmt(negative)

    if "common_positive" in rule:
        common_pos_str = fmt(parse_prompts(rule["common_positive"]))
        if pos_str and common_pos_str:
            pos_str = f"{pos_str},{common_pos_str}"
        elif common_pos_str:
            pos_str = common_pos_str
    if "common_negative" in rule:
        common_neg_str = fmt(parse_prompts(rule["common_negative"]))
        if neg_str and common_neg_str:
            neg_str = f"{neg_str},{common_neg_str}"
        elif common_neg_str:
            neg_str = common_neg_str

    return pos_str, neg_str


class ParseRulebook:
    def __init__(self, path: Path):
        self.rules: list[dict[str, dict]] = []

        data = load_yaml(path)
        for key in data:
            rule = normalize_rule(data[key])
            resolve_priorities(rule["fields"])
            self.rules.append(rule)

    def make_prompt(self, text: str) -> tuple[str, str]:
        for rule in self.rules:
            pos, neg = make_prompt(text, rule)
            if pos or neg:
                break

        return pos, neg


if __name__ == "__main__":
    text = "today: 2026/02/05, Name2 (vibe: )foobarBarFugahogeHogeBazbaz"
    text2 = "sub: WOW!! mood: Mood2 foobar"
    rulebook = ParseRulebook("src/debug/parse_test/test.yaml")
    pos, neg = rulebook.make_prompt(text)
    print("POS:", pos)
    print("NEG:", neg)
    pos, neg = rulebook.make_prompt(text2)
    print("POS:", pos)
    print("NEG:", neg)
