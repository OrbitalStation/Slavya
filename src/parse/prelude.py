from dataclasses import dataclass
from typing import Optional, Self, NoReturn
from src.data_types import *
from sys import stderr
from src import utils


__all__ = ["Info", "Parseable", "With", "err"]


@dataclass
class Info:
    file: str
    line: int
    top_level: list[TopLevel]


@dataclass
class Parseable:
    full_string: str
    column: int = 0

    @property
    def string(self) -> str:
        return self.full_string[self.column:]

    def cut(self, at: int) -> tuple[str, Self]:
        return self.string[:at], Parseable(self.full_string,
                                           self.column + at + max(utils.find(" ".__ne__, self.string[at:]), 0))

    def empty(self) -> Self:
        return Parseable(self.full_string, len(self.full_string))

    def is_empty(self) -> bool:
        return self.column >= len(self.full_string)


type With[T] = tuple[Optional[T], Parseable]


def err(info: Info, p: Parseable, description: str) -> NoReturn:
    location = f"At {info.file}:{info.line}:{p.column}"
    print(location + "\n\t" + p.full_string + "\n" + description, file=stderr)
    exit(1)
