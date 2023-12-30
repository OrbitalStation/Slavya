import src.data_types as dt
from os import system
from src import utils


def compile_and_run(mod_name: str, text: str):
    open(f"./compiled/{mod_name}.rs", "wt").write(text)
    system(f"cd compiled && rustc {mod_name}.rs -C opt-level=3 && ./{mod_name}")


def rs_template(code: str):
    return f"""
#![allow(unused_variables, non_upper_case_globals, dead_code)]
mod heart;
use heart::*;
{code}
    """


def modify_arg(name: str) -> str:
    return f"a_{name}"


def modify_static(name: str) -> str:
    return f"f_{name}"


def modify_type(name: str) -> str:
    return f"t_{name}"


def get_bound_arguments(expr: dt.Expr, arguments: tuple[str, ...]) -> tuple[str, ...]:
    match type(expr):
        case dt.Argument:
            modified = modify_arg(expr.name)
            return (modified,) if modified in arguments else ()
        case dt.Abstraction:
            return get_bound_arguments(expr.body, arguments)
        case dt.Application:
            return _add_uniquely(get_bound_arguments(expr.function, arguments),
                                 get_bound_arguments(expr.argument, arguments))
        case dt.Axiom | dt.Statement:
            return ()


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


# TODO: try replacing with sets
def _add_uniquely[T](a: tuple[T, ...], b: tuple[T, ...]) -> tuple[T, ...]:
    a = list(a)
    for item in b:
        if item not in a:
            a.append(item)
    return tuple(a)
