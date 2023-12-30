from typing import Any
from enum import IntEnum
from dataclasses import dataclass


Expr = Any


@dataclass
class Argument:
    name: str
    ty: Expr


@dataclass
class Abstraction:
    argument: Argument
    body: Expr


@dataclass
class Application:
    function: Expr
    argument: Expr


class Axiom(IntEnum):
    ANY = 0


AXIOMS = {
    "A": Axiom.ANY
}


@dataclass
class Statement:
    name: str
    body: Expr


@dataclass
class Comment:
    source: str


type TopLevel = Statement | Comment
