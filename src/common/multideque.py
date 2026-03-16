"""
オブジェクトごとの FIFO を管理するキュー
"""

from __future__ import annotations

from collections import deque
from typing import TypeVarTuple

Ts = TypeVarTuple("Ts")


class MultiDeque[*Ts]:
    """
    オブジェクトごとの FIFO を管理するキュー\n
    multideque[A, B] のとき, A1,A2,...An,B1,B2,...,Bm という状態であるとして\n
    A を push すると A1,A2,...An,A,B1,B2,...,Bm\n
    B を push すると A1,A2,...An,B1,B2,...,Bm,B\n
    となり, pop すると常に左から抜き取る
    """

    def __init__(self, *types: type):
        """
        コンストラクタ

        Raises:
            ValueError: 型未指定
        """
        if not types:
            raise ValueError("At least one type must be specified")
        self._types: list[type] = list(types)
        self._queues: dict[type, deque[object]] = {t: deque() for t in types}

    def push(self, item: object) -> None:
        """
        優先ルールに従って push する

        Args:
            item (object): オブジェクト

        Raises:
            TypeError: 型不適
        """
        item_type = type(item)
        for t in item_type.__mro__:
            if t in self._queues:
                self._queues[t].append(item)
                return
        raise TypeError(f"Unsupported type: {item_type}")

    def pop(self) -> object:
        """
        優先ルールに従って pop する

        Raises:
            IndexError: 空キューからの pop

        Returns:
            object: オブジェクト
        """
        for t in self._types:
            q = self._queues[t]
            if q:
                return q.popleft()
        raise IndexError("pop from empty wdeque")

    def pop_type(self, t: type) -> object:
        """
        指定の型についての FIFO ルールで pop する

        Args:
            t (type): オブジェクト型

        Raises:
            TypeError: 型不適
            IndexError: 空キューからの pop

        Returns:
            object: オブジェクト
        """
        if t not in self._queues:
            raise TypeError(f"Unsupported type: {t}")
        q = self._queues[t]
        if not q:
            raise IndexError(f"pop from empty queue of type {t}")
        return q.popleft()

    def clear(self) -> None:
        """
        すべてのキューをクリアする
        """
        for q in self._queues.values():
            q.clear()

    def clear_type(self, t: type) -> None:
        """
        指定の型のキューをクリアする

        Args:
            t (type): オブジェクト型

        Raises:
            TypeError: 型不適
        """
        if t not in self._queues:
            raise TypeError(f"Unsupported type: {t}")
        self._queues[t].clear()

    def promote(self, t: type) -> None:
        """
        指定型を優先度の先頭へ移動

        Args:
            t (type): オブジェクト型

        Raises:
            TypeError: 型不適
        """
        if t not in self._types:
            raise TypeError(f"Unsupported type: {t}")
        self._types.remove(t)
        self._types.insert(0, t)

    def demote(self, t: type) -> None:
        """
        指定型を優先度の末尾へ移動

        Args:
            t (type): オブジェクト型

        Raises:
            TypeError: 型不適
        """
        if t not in self._types:
            raise TypeError(f"Unsupported type: {t}")
        self._types.remove(t)
        self._types.append(t)

    def swap(self, t1: type, t2: type) -> None:
        """
        2つの型の優先度を入れ替える

        Args:
            t1 (type): オブジェクト型
            t2 (type): オブジェクト型
        """
        i1 = self._types.index(t1)
        i2 = self._types.index(t2)
        self._types[i1], self._types[i2] = self._types[i2], self._types[i1]

    def __contains__(self, item: object) -> bool:
        """
        オブジェクトがいずれかのキューに含まれるか

        Args:
            item (object): オブジェクト

        Returns:
            bool: True: 含まれる, False: 含まれない
        """
        for q in self._queues.values():
            if item in q:
                return True
        return False

    def __len__(self) -> int:
        """
        キューの長さを得る

        Returns:
            int: 長さ
        """
        return sum(len(q) for q in self._queues.values())

    def __iter__(self):
        """
        イテレータ
        """
        for t in self._types:
            yield from self._queues[t]

    def __repr__(self) -> str:
        """
        再現可能な文字列化

        Returns:
            str: 文字列
        """
        merged = []
        for t in self._types:
            merged.extend(list(self._queues[t]))
        return repr(merged)
