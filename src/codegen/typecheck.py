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
        body, tcode, used = _expr(top_level.body, stmts, (), filename)
        used_statements |= used
        typecheck_code.extend(tcode)
        stmts.append(Typed(top_level, body))

    used_statements = "\n".join(map(lambda x: ccompile.ttop_level(stmts[x].data), used_statements))
    stmts = "\n".join(map(ttop_level, filter(lambda x: not isinstance(x, dt.Comment), stmts)))

    file_rs = typecheck_rs_template(typecheck_code, used_statements + "\n" + stmts)
    analysis.compile_and_run("typecheck", file_rs)


def ttop_level(x):
    body = ccompile.eexpr(x.ty, ())
    if isinstance(x.ty, dt.Application):
        body = f"F::gen(|| {body})"
    return f"const {analysis.modify_type(x.data.name)}: F = {body};"


def typecheck_rs_template(typecheck_code: list[str], stmts: str):
    return analysis.rs_template(f"""
extern crate core;

{stmts}

static mut BOOLEAN: Option <bool> = None; 

const True: F = F::zst(|x, _| {{
    unsafe {{ BOOLEAN = Some(true) }}
    x
}});

const False: F = F::zst(|x, _| {{
    unsafe {{ BOOLEAN = Some(false) }}
    x
}});

fn main() -> Result <(), ()> {{
    let to_typecheck: [(F, &'static str); {len(typecheck_code)}] = [{",\n".join(typecheck_code)}];
    for (ty, location) in to_typecheck {{
        ty.call(True).call(False).call(/* stub */ True);
        if let Some(boolean) = core::mem::replace(unsafe {{ &mut BOOLEAN }}, None) {{
            if !boolean {{
                eprintln!("{{location}}\\nTypechecking failed");
                return Err(())
            }}
        }} else {{
            eprintln!("{{location}}\\nNot a type");
            return Err(())
        }}
    }}
    return Ok(())
}}
    """)


def _expr(expr: dt.Expr, stmts: list[TypedTopLevel], arguments: tuple[str, ...], filename: str)\
        -> tuple[dt.Expr, list[str], set[int]]:
    match type(expr):
        case dt.Argument:
            return dt.Argument(expr.name, dt.Axiom.TY), [], set()
        case dt.Abstraction:
            modified = analysis.modify_arg(expr.argument.name)
            body, code, used1 = _expr(expr.body, stmts, arguments + (modified,), filename)
            used2 = analysis.get_used_statements(expr.argument, stmts)
            return dt.Application(dt.Application(dt.Axiom.FUN, expr.argument.ty), dt.Abstraction(dt.Argument(
                expr.argument.name, dt.Axiom.TY), body)), code, used1 | used2
        case dt.Application:
            fn_ty, compiled1, code1, used1 = compile_typed(expr.function, stmts, arguments, filename)
            arg_ty, compiled2, code2, used2 = compile_typed(expr.argument, stmts, arguments, filename)
            code3_call = f"{compiled1}.call({compiled2})"
            # TODO: Add span
            code3_location = f"At {filename}:<unknown>:<unknown>"
            combined_code = code1 + code2 + [f'({code3_call}, "{code3_location}")']
            combined_used = used1 | used2
            return dt.Application(fn_ty.function, arg_ty), combined_code, combined_used
        case dt.Axiom:
            match expr:
                case dt.Axiom.ANY | dt.Axiom.FUN | dt.Axiom.TY:
                    return dt.Axiom.TY, [], set()
        case dt.Statement:
            return stmts[utils.find(lambda s: isinstance(s, Typed) and s.data.name == expr.name, stmts)].ty, [], set()


def compile_typed(expr: dt.Expr, stmts: list[TypedTopLevel], arguments: tuple[str, ...], filename: str)\
        -> tuple[dt.Expr, str, list[str], set[int]]:
    if isinstance(expr, dt.Statement):
        ty = stmts[utils.find(lambda s: isinstance(s, Typed) and s.data.name == expr.name, stmts)].ty
        return ty, analysis.modify_type(expr.name), [], set()
    ty, code, used = _expr(expr, stmts, arguments, filename)
    return ty, ccompile.eexpr(ty, arguments), code, used
