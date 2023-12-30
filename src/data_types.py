from typing import Any
from enum import IntEnum
from dataclasses import dataclass


__all__ = ["Expr", "Argument", "Abstraction", "Application", "Axiom", "AXIOMS", "Statement", "Comment", "TopLevel"]


# Stub; should really be `Expr`
_Expr = Any


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
    ANY = 0
    FUN = 1
    TY  = 2


AXIOMS = {
    "A": Axiom.ANY,
    "F": Axiom.FUN
}


@dataclass
class Statement:
    name: str
    body: _Expr


@dataclass
class Comment:
    source: str


Expr = Argument | Abstraction | Application | Axiom | Statement

type TopLevel = Statement | Comment
