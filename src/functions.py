"""
共用関数
"""

from __future__ import annotations

import json
import re
from collections import deque
from enum import Enum
from pathlib import Path
from typing import Any

from taskmanager import TaskBlueprint


def json_default(obj: Any) -> str:
    """
    Enum 型を Enum.name() に統一する

    Args:
        obj (Any): オブジェクト

    Raises:
        TypeError: 型違反

    Returns:
        str: Enum.name()
    """
    if isinstance(obj, Enum):
        return obj.name
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, deque):
        return list(obj)
    if isinstance(obj, TaskBlueprint):
        return obj.todict()
    raise TypeError(f"{obj.__class__.__name__} is not JSON serializable")


def dump_json(data: dict, label: str) -> None:
    """
    指定の dict を json 形式でダンプする

    Args:
        data (dict): ダンプ対象
        label (str): 表示するラベル("label": {...})
    """
    print(f'"{label}":')
    print(json.dumps(data, ensure_ascii=False, indent=2, default=json_default))


def search_regex(s: str, regex: str, gridx: int = 1) -> str:
    """
    指定の正規表現にマッチする部分文字列を s から抜き出す\n
    抜き出す部分文字列は gridx 番目のグループに相当する(未指定時 1)

    Args:
        s (str): 全体文字列
        regex (str): 正規表現
        gridx (int, optional): 抜き出すグループインデックス

    Returns:
        str: 部分文字列
    """
    m = re.search(regex, s, flags=re.MULTILINE)
    if not m:
        # print(f'No match with "{regex}".')
        return None
    return m.group(gridx)
