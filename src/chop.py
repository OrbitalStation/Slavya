from sys import stderr
from os.path import realpath
from functools import reduce
from typing import Optional, NoReturn
from src.codegen.evaluate import evaluate
from src.codegen.compile import ccompile
from src.data_types import *
from src import utils


@utils.mixin("evaluate", lambda self: reduce(lambda a, v: a | {v.name: evaluate(v.body)}, self.without_comments(), {}))
@utils.mixin("compile", lambda self, extra_code: ccompile(self.without_comments(), extra_code))
class Chopper:
    def __init__(self, file_name: str):
        self._file = realpath(file_name)
        self._line = 0
        self._string = ""
        self._full_string = ""
        self._column = 0
        self._statements_or_comments = []

    def iterate(self, lines):
        for line in lines:
            self.set(line)
            if line == "":
                continue
            self.statement_or_comment()

    def dump(self):
        print(*self._statements_or_comments, sep="\n")

    def set(self, string: str):
        self._line += 1
        self._string = self._full_string = string
        self._column = 0

    def statement_or_comment(self):
        if (c := self.comment()) is not None:
            self._statements_or_comments.append(c)
            return
        name = utils.or_else(self.identifier(), lambda: self.err("Expected an identifier"))
        _ = utils.or_else(self.token("="), lambda: self.err("Expected a token `=`"))
        body = self.expr()
        self._statements_or_comments.append(Statement(name, body))

    def without_comments(self):
        return filter(lambda soc: not isinstance(soc, Comment), self._statements_or_comments)

    def comment(self) -> Optional[Comment]:
        if self.token("*") is not None:
            return Comment(self._string)

    def identifier(self) -> Optional[str]:
        last_alnum = utils.find(utils.inverse_predicate(str.isalnum), self._string)
        if last_alnum == 0:
            return
        return self.cut(last_alnum if last_alnum != -1 else len(self._string))

    def token(self, tok: str) -> Optional[str]:
        if self._string.startswith(tok):
            return self.cut(len(tok))

    def expr(self, abstractions_arguments: Optional[tuple[Argument]] = None) -> Optional[Expr]:
        if abstractions_arguments is None:
            abstractions_arguments = ()
        args_for_call = []
        while len(self._string) > 0:
            if (x := self.abstraction(abstractions_arguments)) is not None:
                if len(args_for_call) != 0:
                    self.err("Cannot put an abstraction in the middle of a call")
                return x
            if (x := self.identifier()) is not None:
                if x == "axiom":
                    if (axiom := self.surrounded("[", "]")) is None:
                        self.err("Bad axiom syntax")
                    if axiom not in AXIOMS.keys():
                        self.err(f"Unknown axiom: `{axiom}`")
                    args_for_call.append(AXIOMS[axiom])
                elif (idx := utils.find(lambda e: e.name == x, abstractions_arguments)) != -1:
                    args_for_call.append(abstractions_arguments[idx])
                elif (idx := utils.find(lambda e: e.name == x, self._statements_or_comments)) != -1:
                    args_for_call.append(self._statements_or_comments[idx])
                else:
                    self.err(f"Unknown identifier: `{x}`")
            elif (x := self.surrounded("(", ")")) is not None:
                original = self._string
                self._string = x
                if (inner := self.expr(abstractions_arguments)) is None:
                    self.err("Invalid inner content")
                self._string = original
                args_for_call.append(inner)
            else:
                self.err("Expected expression")
        while len(args_for_call) > 1:
            arg = args_for_call.pop(1)
            args_for_call[0] = Application(args_for_call[0], arg)
        return args_for_call[0]

    def surrounded(self, opening: str, closing: str) -> Optional[str]:
        assert len(opening) == len(closing) == 1
        if self.token(opening) is None:
            return
        unclosed = 1
        offset = 0
        for ch in self._string:
            offset += 1
            if ch == opening:
                unclosed += 1
            elif ch == closing:
                unclosed -= 1
                if unclosed == 0:
                    break
        if unclosed != 0:
            self.err(f"Unclosed pair of `{opening}{closing}`")
        return self.cut(offset)[:-1].strip()

    def abstraction(self, abstractions_arguments) -> Optional[Abstraction]:
        backup = self.backup()
        if (argument := self.identifier()) is None:
            return
        if self.token("->") is None:
            self.rollback(backup)
            return
        argument = Argument(argument)
        if (body := self.expr(abstractions_arguments + (argument,))) is None:
            self.err("Expected a body after `->`")
        return Abstraction(argument, body)

    def rollback(self, backup: tuple[str, int]):
        self._string, self._column = backup

    def backup(self) -> tuple[str, int]:
        return self._string, self._column

    def cut(self, at: int) -> str:
        cut = self._string[:at]
        self._string = self._string[at:].strip()
        self._column += at
        return cut

    def err(self, description: str) -> NoReturn:
        location = f"At {self._file}:{self._line}:{self._column}"
        extract = self._full_string
        print(location + "\n\t" + extract + "\n" + description, file=stderr)
        exit(-1)
