"""
共用関数
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from collections import deque
from copy import deepcopy
from enum import Enum, auto
from pathlib import Path
from typing import Any, Generic, TypeVar


class FrontEnd(Enum):
    """
    フロントエンド識別子
    """

    reverse = auto()
    the_world = auto()


class BackEnd(Enum):
    """
    バックエンド識別子
    """

    a1111 = auto()
    comfy_ui = auto()


def xxxDEBUGxxx() -> None:
    """
    行を表示
    """
    frame = inspect.currentframe().f_back
    print(f"Through {frame.f_lineno}@{frame.f_code.co_name}")


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


def dirname_by_prompts(pos_prompt: str, neg_prompt: str) -> str:
    """
    プロンプトからディレクトリ名を生成する\n
    ディレクトリ名は MD5 (32byte Ascii) として得られる

    Args:
        pos_prompt (str): ポジティブプロンプト
        neg_prompt (str): ネガティブプロンプト

    Returns:
        str: ディレクトリ名
    """
    dirpath_raw: str = pos_prompt + neg_prompt
    return hashlib.md5(dirpath_raw.encode()).hexdigest()


Message = TypeVar("Message")


class BottleMail(Generic[Message]):
    def __init__(self):
        self._q: deque[Message] = deque()

    def enclose(self, msg: Message) -> None:
        self._q.append(deepcopy(msg))

    def pickup(self) -> Message:
        return self._q.popleft()

    def __len__(self) -> int:
        return len(self._q)
