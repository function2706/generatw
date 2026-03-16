"""
評価式と項の定義
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class Expr[Type](ABC):
    @abstractmethod
    def eval(self, objset: set[Type]) -> bool:
        raise NotImplementedError

    def __and__(self, other: Expr[Type]) -> Expr[Type]:
        return And(self, other)

    def __or__(self, other: Expr[Type]) -> Expr[Type]:
        return Or(self, other)

    def __invert__(self) -> Expr[Type]:
        return Not(self)


@dataclass(frozen=True)
class Has[Type](Expr[Type]):
    obj: Type

    def eval(self, objset: set[Type]) -> bool:
        return self.obj in objset


@dataclass(frozen=True)
class And[Type](Expr[Type]):
    left: Expr[Type]
    right: Expr[Type]

    def eval(self, objset: set[Type]) -> bool:
        return self.left.eval(objset) and self.right.eval(objset)


@dataclass(frozen=True)
class Or[Type](Expr[Type]):
    left: Expr[Type]
    right: Expr[Type]

    def eval(self, objset: set[Type]) -> bool:
        return self.left.eval(objset) or self.right.eval(objset)


@dataclass(frozen=True)
class Not[Type](Expr[Type]):
    expr: Expr[Type]

    def eval(self, objset: set[Type]) -> bool:
        return not self.expr.eval(objset)


@dataclass(frozen=True)
class TrueExpr[Type](Expr[Type]):
    def eval(self, objset: set[Type]) -> bool:
        return True


@dataclass(frozen=True)
class FalseExpr[Type](Expr[Type]):
    def eval(self, objset: set[Type]) -> bool:
        return False
