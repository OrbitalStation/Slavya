from src.codegen import analysis
from src import utils
from os import system
import src.data_types as dt


def ccompile(top_level: list[dt.TopLevel], extra_code: str):
    """
    Compile Slavya data structures to Rust
    """

    stmts = "\n".join(map(_top_level, top_level))

    main_rs = f"""
#![allow(unused_variables, non_upper_case_globals, dead_code)]
mod heart;
use heart::F;
{stmts}
{extra_code}
    """

    open("./compiled/main.rs", "wt").write(main_rs)
    system("cd compiled && rustc main.rs -C opt-level=3 && ./main")


def modify_arg(name: str) -> str:
    return f"a_{name}"


def modify_static(name: str) -> str:
    return f"f_{name}"


def _top_level(top_level: dt.TopLevel) -> str:
    if isinstance(top_level, dt.Comment):
        return f"/* {top_level.source} */"
    body = _expr(top_level.body, ())
    # Cannot make calling const in Rust
    if isinstance(top_level.body, dt.Application):
        body = f"F::gen(|| {body})"
    return f"const {modify_static(top_level.name)}: F = {body};"


def _expr(expr: dt.Expr, arguments: tuple[str, ...], no_clone_required: bool = False) -> str:
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
                filtered = tuple(filter(utils.unzip(lambda _, name: name in bound), enumerate(arguments)))
                data = ", ".join(map(_expr_index(filtered, arguments[-1]), bound))
                return f"F::new(|{arg_name}, data| {body}, ({data},))"
        case dt.Application:
            return f"{_expr(expr.function, arguments, no_clone_required=True)}.call({_expr(expr.argument, arguments)})"
        case dt.Axiom:
            raise NotImplementedError
        case dt.Statement:
            return modify_static(expr.name)


def _expr_index(filtered: tuple[tuple[int, str], ...], previous_abstraction_argument_name: str):
    def inner(bound_name: str) -> str:
        if bound_name == previous_abstraction_argument_name:
            return f"{previous_abstraction_argument_name}.clone()"
        else:
            return f"data.{filtered[utils.find(lambda f: bound_name == f[1], filtered)][0]}.clone()"
    return inner
