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
    ANY    = 0
    FUN    = 1
    TY     = 2

    # The following axioms cannot be obtained via `axiom["..."]`,
    #   but in difference to CHURCH_BOOL, CHURCH_TRUE, etc.
    #   that are present only in `heart.rs` we need to reference them
    #   in python code also, so that's why they are in here
    RET_TY = 3


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


Expr = Argument | Abstraction | Application | Axiom | Statement

type TopLevel = Statement | Comment
