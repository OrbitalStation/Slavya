import src.data_types as dt
from src import utils, err
from src.codegen import optimize, analysis


def stmt(
        s: dt.Statement,
        typed_top_level: list[dt.TypedTopLevel],
        original_top_level: list[dt.TopLevel]
) -> tuple[dt.Typed[dt.Statement], set[int]]:
    ty, used = _expr(s.body, typed_top_level, original_top_level, ())
    return dt.Typed(s, ty), used


def _expr(
        e: dt.Expr,
        typed_top_level: list[dt.TypedTopLevel],
        original_top_level: list[dt.TopLevel],
        arguments: tuple[dt.Argument, ...],
        do_mark_arguments: bool = False
) -> tuple[dt.Expr, set[int]]:

    match type(e):
        case dt.Argument:
            if do_mark_arguments:
                return dt.Argument(analysis.modify_arg(e.name), dt.Axiom.TY), set()
            return arguments[utils.find(lambda x: x.name == e.name, arguments)].ty, set()
        case dt.Abstraction:
            modified = analysis.modify_arg(e.argument.name)
            arg_ty = optimize.expr(e.argument.ty, original_top_level)
            used1 = analysis.get_used_statements(arg_ty, original_top_level)
            body, used2 = _expr(e.body, typed_top_level, original_top_level,
                                arguments + (dt.Argument(modified, arg_ty),), do_mark_arguments=True)
            constructed_expr = dt.Application(dt.Application(dt.Axiom.FUN, arg_ty), dt.Abstraction(dt.Argument(
                modified, dt.Axiom.TY), body))
            return constructed_expr, used1 | used2
        case dt.Application:
            fn_ty, used1 = _expr(e.function, typed_top_level, original_top_level, arguments)
            arg_ty, used2 = _expr(e.function, typed_top_level, original_top_level, arguments)
            accepted_ty, return_ty_gen = get_arg_ty_and_ret_ty_gen(fn_ty) or err.error("", 0, 0, "", "not a function")
            # TODO: check for accepted_ty

            return optimize.expr(dt.Application(return_ty_gen, arg_ty), original_top_level), used1 | used2
        case dt.Axiom:
            match e:
                case dt.Axiom.ANY | dt.Axiom.TY:
                    return dt.Axiom.TY, set()
                case dt.Axiom.FUN:
                    # fun Ty (_: Ty -> fun (fun Ty (_: Ty -> Ty)) (_: Ty -> Ty))
                    return _fun(dt.Axiom.TY, _fun(_fun(dt.Axiom.TY, dt.Axiom.TY), dt.Axiom.TY)), set()
                    # noinspection PyTypeChecker
                    # return dt.Statement(analysis.ModifiedName("FUN_FULL_TY", lambda x: x), dt.Axiom.TY), set()
        case dt.Statement:
            return typed_top_level[utils.find(lambda s: isinstance(s, dt.Typed) and s.data.name == e.name,
                                              typed_top_level)].ty, set()


def get_arg_ty_and_ret_ty_gen(fn: dt.Expr) -> tuple[dt.Expr, dt.Expr] | None:
    # Special since functions are internally represented via axiom["F"]
    if (isinstance(fn, dt.Application)
            and isinstance(fn.function, dt.Application)
            and isinstance(fn.function.function, dt.Axiom)
            and fn.function.function == dt.Axiom.FUN):
        return fn.function.argument, fn.argument

    if not isinstance(fn, dt.Axiom):
        return

    match fn:
        case dt.Axiom.ANY:
            return dt.Axiom.ANY, dt.Abstraction(dt.Argument("", dt.Axiom.TY), dt.Axiom.BOOL)
        case dt.Axiom.TY:
            return dt.Axiom.TY, dt.Abstraction(dt.Argument("", dt.Axiom.TY), dt.Axiom.BOOL)
        case _:
            raise ValueError(f"{fn}: don't do it yet")


def _fun(arg, ret):
    ret_gen = dt.Abstraction(dt.Argument("", dt.Axiom.TY), ret)
    return dt.Application(dt.Application(dt.Axiom.FUN, arg), ret_gen)
