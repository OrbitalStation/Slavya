import src.data_types as dt
from src import utils
from dataclasses import dataclass
from src.codegen import compile as ccompile
from src.codegen import analysis


@dataclass
class Typed[T]:
    data: T
    ty: dt.Expr


type TypedTopLevel = Typed[dt.Statement] | dt.Comment


def typecheck(top_level_list: list[dt.TopLevel], filename: str):
    stmts = []
    typecheck_code = []
    used_statements = set()
    for top_level in top_level_list:
        if isinstance(top_level, dt.Comment):
            stmts.append(top_level)
            continue
        body, tcode, used = _expr(top_level.body, stmts, ())
        used_statements |= used
        typecheck_code.extend(tcode)
        stmts.append(Typed(top_level, body))

    used_statements = "\n".join(map(lambda x: ccompile.ttop_level(stmts[x].data), used_statements))
    stmts = "\n".join(map(ttop_level, filter(lambda x: not isinstance(x, dt.Comment), stmts)))

    file_rs = typecheck_rs_template(typecheck_code, used_statements + "\n" + stmts, filename)
    analysis.compile_and_run("typecheck", file_rs)


def ttop_level(x):
    body = ccompile.eexpr(x.ty, ())
    if isinstance(x.ty, dt.Application):
        body = f"F::gen(|| {body})"
    return f"const {analysis.modify_type(x.data.name)}: F = {body};"


def typecheck_rs_template(typecheck_code: list[str], stmts: str, filename: str):
    return analysis.rs_template(f"""
{stmts}

fn main() -> std::process::ExitCode {{
    type_check("{filename}", &[
        {",\n\t\t".join(typecheck_code)}
    ])
}}
    """)


def _expr(expr: dt.Expr, stmts: list[TypedTopLevel], arguments: tuple[dt.Argument, ...]) \
        -> tuple[dt.Expr, list[str], set[int]]:
    match type(expr):
        case dt.Argument:
            return arguments[utils.find(lambda x: x.name == expr.name, arguments)].ty, [], set()
        case dt.Abstraction:
            modified = analysis.modify_arg(expr.argument.name)
            body, code, used1 = _expr(expr.body, stmts, arguments + (dt.Argument(modified, expr.argument.ty),))
            used2 = analysis.get_used_statements(expr.argument, stmts)
            return dt.Application(dt.Application(dt.Axiom.FUN, expr.argument.ty), dt.Abstraction(dt.Argument(
                expr.argument.name, dt.Axiom.TY), body)), code, used1 | used2
        case dt.Application:
            fn_ty, compiled1, code1, used1 = compile_typed(expr.function, stmts, arguments)
            arg_ty, compiled2, code2, used2 = compile_typed(expr.argument, stmts, arguments)
            code3_call = f"AXIOM_ARG_TY.call({compiled1}).call({compiled2})"
            # TODO: Add span
            # TODO: Improve error messages
            combined_code = code1 + code2 + [f'({code3_call}, (0, 0))']
            combined_used = used1 | used2
            return dt.Application(dt.Application(dt.Axiom.RET_TY, fn_ty), arg_ty), combined_code, combined_used
        case dt.Axiom:
            match expr:
                case dt.Axiom.ANY | dt.Axiom.TY:
                    return dt.Axiom.TY, [], set()
                case dt.Axiom.FUN:
                    # noinspection PyTypeChecker
                    return dt.Statement(analysis.ModifiedName("FUN_FULL_TY", lambda x: x), dt.Axiom.TY), [], set()
        case dt.Statement:
            return stmts[utils.find(lambda s: isinstance(s, Typed) and s.data.name == expr.name, stmts)].ty, [], set()


def compile_typed(expr: dt.Expr, stmts: list[TypedTopLevel], arguments: tuple[dt.Argument, ...])\
        -> tuple[dt.Expr, str, list[str], set[int]]:
    if isinstance(expr, dt.Statement):
        ss = stmts[utils.find(lambda s: isinstance(s, Typed) and s.data.name == expr.name, stmts)]
        return dt.Statement(analysis.modify_type(ss.data.name), ss.ty), analysis.modify_type(expr.name), [], set()
    ty, code, used = _expr(expr, stmts, arguments)
    return ty, ccompile.eexpr(ty, tuple(map(lambda x: x.name, arguments))), code, used
