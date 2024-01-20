from typing import Callable
import src.data_types as dt
from os import system
from src import utils
from copy import copy


def compile_and_run(text: str, mod_name: str = "main"):
    open(f"./compiled/src/{mod_name}.rs", "wt").write(text)
    system(f"cd compiled && cargo run -r -q")


def rs_template(code: str):
    return f"""
#![allow(unused_variables, non_upper_case_globals, dead_code)]
mod heart;
use heart::*;
{code}
    """


class ModifiedName:
    """
    A disgusting hack used to prevent double name modification in `src.codegen.typecheck.compile_typed` function
    Replace with something better as soon as a solution is found
    """

    def __init__(self, value, how):
        if isinstance(value, ModifiedName):
            self.value = value.value
        elif isinstance(value, str):
            self.value = how(value)

    def __str__(self):
        return self.value

    def __repr__(self):
        return repr(self.value)

    def __eq__(self, other):
        return str(self) == str(other)

    def __add__(self, other):
        return str(self) + str(other)

    def __hash__(self):
        return hash(str(self))


def modify_general(prefix: str):
    def inner(ident: str | ModifiedName) -> ModifiedName:
        return ModifiedName(ident, lambda name: f"{prefix}_{name}")
    return inner


modify_arg    = modify_general("a")
modify_static = modify_general("f")
modify_type   = modify_general("t")


def get_bound_arguments(expr: dt.Expr, arguments: tuple[ModifiedName, ...]) -> set[ModifiedName]:
    match type(expr):
        case dt.Argument:
            modified = modify_arg(expr.name)
            return {modified} if modified in arguments else set()
        case dt.Abstraction:
            return get_bound_arguments(expr.body, arguments)
        case dt.Application:
            return get_bound_arguments(expr.function, arguments) | get_bound_arguments(expr.argument, arguments)
        case dt.Axiom | dt.Statement:
            return set()


def get_used_statements(expr: dt.Expr, stmts: list[dt.TopLevel], is_final: bool = False) -> set[int]:
    match type(expr):
        case dt.Argument:
            return set()
        case dt.Abstraction:
            arg = set() if is_final else get_used_statements(expr.argument.ty, stmts)
            return arg | get_used_statements(expr.body, stmts)
        case dt.Application:
            return get_used_statements(expr.function, stmts) | get_used_statements(expr.argument, stmts)
        case dt.Axiom:
            return set()
        case dt.Statement:
            if is_final:
                return {utils.find(lambda s: isinstance(s, dt.Typed) and s.data.name == expr.name, stmts)}
            return {utils.find(lambda s: isinstance(s, dt.Statement) and s.name == expr.name, stmts)}


def visit_expr(
        root: dt.Expr | dt.Typed[dt.Statement],
        node_filter: Callable[[dt.Expr | dt.Typed[dt.Statement]], bool],
        node_transformer: Callable[[dt.Expr | dt.Typed[dt.Statement]], dt.Expr | dt.Typed[dt.Statement]]
) -> dt.Expr | dt.Typed[dt.Statement]:
    to_check = []
    match type(root):
        case dt.Abstraction:
            to_check.append(("body", root.body))
        case dt.Application:
            to_check.extend([("function", root.function), ("argument", root.argument)])

    cp = copy(root)
    for attr, node in to_check:
        setattr(cp, attr, visit_expr(node, node_filter, node_transformer))
    if node_filter(cp):
        cp = node_transformer(cp)
    return cp
