from typing import Any
from enum import IntEnum
from dataclasses import dataclass


__all__ = ["Expr", "Argument", "Abstraction", "Application", "Axiom", "AXIOMS", "Statement", "Comment", "TopLevel",
           "TypedTopLevel"]


# Stub; should really be `Expr`
type _Expr = Any


@dataclass
class Argument:
    name: str
    ty: _Expr


@dataclass
class Abstraction:
    argument: Argument
    body: _Expr


@dataclass
class Application:
    function: _Expr
    argument: _Expr


class Axiom(IntEnum):
    ANY    = 0
    FUN    = 1
    TY     = 2
    BOOL   = 3


AXIOMS = {
    "A": Axiom.ANY,
    "F": Axiom.FUN,
    "T": Axiom.TY
}


@dataclass
class Statement:
    name: str
    body: _Expr


@dataclass
class Comment:
    source: str


type Expr = Argument | Abstraction | Application | Axiom | Statement

type TopLevel = Statement | Comment


@dataclass
class Typed[T]:
    data: T
    ty: Expr


type TypedTopLevel = Typed[Statement] | Comment
