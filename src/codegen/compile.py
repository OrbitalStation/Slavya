from src.codegen import analysis
from src import utils
import src.data_types as dt


def ccompile(top_level_list: list[dt.TopLevel], extra_code: str, filename: str = "main"):
    """
    Compile Slavya data structures to Rust
    """
    stmts = "\n".join(map(ttop_level, top_level_list))
    file_rs = analysis.rs_template(stmts + "\n" + extra_code)
    analysis.compile_and_run(file_rs, filename)


def ttop_level(top_level: dt.TopLevel) -> str:
    if isinstance(top_level, dt.Comment):
        return f"/* {top_level.source} */"
    body = eexpr(top_level.body, ())
    # Cannot make calling const in Rust
    if isinstance(top_level.body, dt.Application):
        body = f"F::gen(|| {body})"
    return f"const {analysis.modify_static(top_level.name)}: F = {body};"


def eexpr(expr: dt.Expr, arguments: tuple[analysis.ModifiedName, ...], no_clone_required: bool = False) -> str:
    match type(expr):
        case dt.Argument:
            modified = analysis.modify_arg(expr.name)
            idx = arguments.index(modified)
            clone = "" if no_clone_required else ".clone()"
            if idx == len(arguments) - 1:
                # The last introduced argument is separate from `data`
                return modified + clone
            return f"data.{idx}" + clone
        case dt.Abstraction:
            # `set`s do not preserve order, which will crucial later, so convert to tuple
            bound = tuple(analysis.get_bound_arguments(expr.body, arguments))
            arg_name = analysis.modify_arg(expr.argument.name)
            body = eexpr(expr.body, bound + (arg_name,))
            if len(bound) == 0:
                return f"F::zst(|{arg_name}, _| {body})"
            else:
                # Get arguments' indexes in bound's order
                filtered = tuple(filter(utils.unzip(lambda _, name: name in bound), enumerate(arguments)))
                data = ", ".join(map(expr_index(filtered, arguments[-1]), bound))
                return f"F::new(|{arg_name}, data| {body}, ({data},))"
        case dt.Application:
            return f"{eexpr(expr.function, arguments, no_clone_required=True)}.call({eexpr(expr.argument, arguments)})"
        case dt.Axiom:
            return f"AXIOM_{expr.name}"
        case dt.Statement:
            return analysis.modify_static(expr.name)


def expr_index(filtered: tuple[tuple[int, str], ...], previous_abstraction_argument_name: analysis.ModifiedName):
    def inner(bound_name: analysis.ModifiedName) -> str:
        if bound_name == previous_abstraction_argument_name:
            return f"{previous_abstraction_argument_name}.clone()"
        else:
            return f"data.{filtered[utils.find(lambda f: bound_name == f[1], filtered)][0]}.clone()"
    return inner
