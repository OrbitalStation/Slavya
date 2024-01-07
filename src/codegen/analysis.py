import src.data_types as dt
from os import system
from src import utils


# TODO: Switch to `cargo`
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


def get_used_statements(expr: dt.Expr, stmts) -> set[int]:
    from src.codegen.typecheck import Typed

    match type(expr):
        case dt.Argument:
            return get_used_statements(expr.ty, stmts)
        case dt.Abstraction:
            return get_used_statements(expr.argument.ty, stmts) | get_used_statements(expr.body, stmts)
        case dt.Application:
            return get_used_statements(expr.function, stmts) | get_used_statements(expr.argument, stmts)
        case dt.Axiom:
            return set()
        case dt.Statement:
            return {utils.find(lambda s: isinstance(s, Typed) and s.data.name == expr.name, stmts)}
