from src.codegen import analysis
from src import utils
from os import system
import src.data_types as dt


def ccompile(statements, extra_code: str):
    """
    Compile Slavya data structures to Rust
    """

    stmts = "\n".join(map(_stmt, statements))

    main_rs = f"""
#![allow(unused_variables, non_upper_case_globals, dead_code)]
mod heart;
use heart::F;
{stmts}
{extra_code}
    """

    open("./compiled/main.rs", "wt").write(main_rs)
    system("cd compiled && rustc main.rs && ./main")


def modify_arg(name: str) -> str:
    return f"a_{name}"


def modify_static(name: str) -> str:
    return f"f_{name}"


def _stmt(stmt: dt.Statement) -> str:
    body = _expr(stmt.body, ())
    # Cannot make calling const in Rust
    if isinstance(stmt.body, dt.Application):
        body = f"F::gen(|| {body})"
    return f"const {modify_static(stmt.name)}: F = {body};"


def _expr(expr, arguments, no_clone_required=False) -> str:
    match type(expr):
        case dt.Argument:
            modified = modify_arg(expr.name)
            idx = arguments.index(modified)
            clone = "" if no_clone_required else ".clone()"
            if idx == len(arguments) - 1:
                # The last introduced argument is separate from `data`
                return modified + clone
            return f"data.{idx}" + clone
        case dt.Abstraction:
            bound = analysis.get_bound_arguments(expr.body, arguments)
            arg_name = modify_arg(expr.argument.name)
            body = _expr(expr.body, bound + (arg_name,))
            if len(bound) == 0:
                return f"F::zst(|{arg_name}, _| {body})"
            else:
                # Get arguments' indexes in bound's order
                filtered = list(filter(utils.unzip(lambda _, name: name in bound), enumerate(arguments)))
                data = ", ".join(map(_expr_index(filtered, arguments[-1]), bound))
                return f"F::new(|{arg_name}, data| {body}, ({data},))"
        case dt.Application:
            return f"{_expr(expr.function, arguments, no_clone_required=True)}.call({_expr(expr.argument, arguments)})"
        case dt.Axiom:
            raise NotImplementedError
        case dt.Statement:
            return modify_static(expr.name)


def _expr_index(filtered, previous_abstraction_argument_name):
    def inner(bound_name):
        if bound_name == previous_abstraction_argument_name:
            return f"{previous_abstraction_argument_name}.clone()"
        else:
            return f"data.{filtered[utils.find(lambda f: bound_name == f[1], filtered)][0]}.clone()"
    return inner
