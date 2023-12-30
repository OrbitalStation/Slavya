from typing import Callable, Any
from src.data_types import *
from src import utils
from src.parse.prelude import *


def top_level(info: Info, p: Parseable) -> TopLevel:
    if not utils.is_none1(xxx := comment(p)):
        comm, _ = xxx
        return comm
    seq, p2 = sequence(info, p, [
        utils.ignore1(identifier),
        utils.ignore1(utils.rpartial(token, "=")),
        utils.rpartial(expr, ())
    ])
    if isinstance(seq, int):
        err(info, p2, [
            "Expected an identifier",
            "Expected a token ` = `",
            "Expected an expression"
        ][seq])
    name, _, body = seq
    if not p2.is_empty():
        err(info, p2, f"Unexpected: `{p2.string}`")
    return Statement(name, body)


def token(p: Parseable, tok: str) -> With[str]:
    if p.string.startswith(tok):
        return p.cut(len(tok))
    return None, p


def identifier(p: Parseable) -> With[str]:
    if (last_alnum := utils.find(utils.inverse_predicate(str.isalnum), p.string)) == 0:
        return None, p
    return p.cut(last_alnum if last_alnum != -1 else len(p.string))


def comment(p: Parseable) -> With[Comment]:
    tok, p2 = token(p, "*")
    if tok is None:
        return None, p
    return Comment(p2.string), p2.empty()


def surrounded(info: Info, p: Parseable, opening: str, closing: str) -> With[str]:
    assert len(opening) == len(closing) == 1
    tok, p2 = token(p, opening)
    if tok is None:
        return None, p
    unclosed = 1
    offset = 0
    for ch in p2.string:
        offset += 1
        if ch == closing:
            unclosed -= 1
            if unclosed == 0:
                break
        elif ch == opening:
            unclosed += 1
    if unclosed != 0:
        err(info, p2, f"Unclosed pair of `{opening}{closing}`")
    string, p3 = p2.cut(offset)
    return string[:-1], p3


def expr(info: Info, p: Parseable, abstractions_arguments: tuple[Argument, ...]) -> With[Expr]:
    args_for_call = []
    while len(p.string) > 0:
        if not utils.is_none1(xxx := abstraction(info, p, abstractions_arguments)):
            abstr, p2 = xxx
            if len(args_for_call) > 0:
                err(info, p, "Cannot put an abstraction in the middle of a call")
            return abstr, p2
        if not utils.is_none1(xxx := identifier(p)):
            ident, p2 = xxx
            if ident == "axiom":
                if utils.is_none1(xxx := surrounded(info, p2, "[", "]")):
                    err(info, p2, "Bad axiom syntax")
                axiom, p3 = xxx
                if utils.is_none1(xxx := surrounded(info, Parseable(axiom), '"', '"')):
                    err(info, p2, "Bad axiom syntax")
                axiom, _ = xxx
                if axiom not in AXIOMS.keys():
                    err(info, p2, f"Unknown axiom: `{axiom}`")
                args_for_call.append(AXIOMS[axiom])
                p = p3
            elif (idx := utils.find(lambda e: e.name == ident, abstractions_arguments)) != -1:
                args_for_call.append(abstractions_arguments[idx])
                p = p2
            elif (idx := utils.find(lambda e: isinstance(e, Statement) and e.name == ident,
                                    info.top_level)) != -1:
                args_for_call.append(info.top_level[idx])
                p = p2
            else:
                err(info, p, f"Unknown identifier: `{ident}`")
        elif not utils.is_none1(xxx := surrounded(info, p, "(", ")")):
            inner, p2 = xxx
            if utils.is_none1(xxx := expr(info, Parseable(inner), abstractions_arguments)):
                err(info, Parseable(inner), "Invalid inner content")
            inner, _ = xxx
            args_for_call.append(inner)
            p = p2
        elif len(args_for_call) == 0:
            err(info, p, "Expected expression")
        else:
            break
    while len(args_for_call) > 1:
        arg = args_for_call.pop(1)
        args_for_call[0] = Application(args_for_call[0], arg)
    return args_for_call[0], p


def abstraction(info: Info, p: Parseable, abstractions_arguments: tuple[Argument, ...]) -> With[Abstraction]:
    seq, p2 = sequence(info, p, [
        utils.ignore1(identifier),
        utils.ignore1(utils.rpartial(token, ":")),
        utils.rpartial(expr, abstractions_arguments),
        utils.ignore1(utils.rpartial(token, "->"))
    ])
    if isinstance(seq, int):
        return None, p
    argument, _, ty, _ = seq
    argument = Argument(argument, ty)
    if utils.is_none1(xxx := expr(info, p2, abstractions_arguments + (argument,))):
        err(info, p2, "Expected a body after `->`")
    body, p3 = xxx
    return Abstraction(argument, body), p3


def sequence(info: Info, p: Parseable, seq: list[Callable[[Info, Parseable], With[Any]]]) \
        -> tuple[list[Any] | int, Parseable]:
    collected = []
    for parser in seq:
        parsed, newp = parser(info, p)
        if parsed is None:
            return len(collected), p
        collected.append(parsed)
        p = newp
    return collected, p
