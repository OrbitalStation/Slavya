from src import data_types as dt
from src.codegen import analysis
from src import utils


def stmt(s: dt.TypedTopLevel, top_level: list[dt.TypedTopLevel]) -> dt.TypedTopLevel:
    name, body = s.data.name, s.data.body
    body = expr(body, top_level)
    return dt.Typed(dt.Statement(name, body), s.ty)


def expr(e: dt.Expr, top_level: list[dt.TypedTopLevel]) -> dt.Expr:
    e = _statement_replacing_pass(e, top_level)
    e = _beta_reduction_and_axiom_expanding_pass(e)
    return e


def _statement_replacing_pass(ee: dt.Expr, top_level: list[dt.TopLevel]) -> dt.Statement:
    def transform(e: dt.Typed[dt.Statement]) -> dt.Statement:
        return top_level[utils.find(lambda s: isinstance(s, dt.Typed) and s.data.name == e.data.name, top_level)]
    return analysis.visit_expr(ee, lambda e: isinstance(e, dt.Typed), transform)


def _beta_reduction_and_axiom_expanding_pass(body: dt.Expr) -> dt.Expr:
    def transform(e: dt.Application):
        function = e.function
        while isinstance(function, dt.Typed):
            function = function.data.body
        if isinstance(function, dt.Abstraction):
            reduced = analysis.visit_expr(
                function.body,
                lambda ee: isinstance(ee, dt.Argument) and ee.name == function.argument.name,
                lambda _: e.argument
            )
            # Repeat beta-reduction because replacement may have generated new possible reduction candidates
            return _beta_reduction_and_axiom_expanding_pass(reduced)
        # TODO: add axiom expanding
        return e
    return analysis.visit_expr(body, lambda e: isinstance(e, dt.Application), transform)

# TODO: maybe implement eta-reduction
#   why not do it rn? Because it may ruin some computational chains
#   since it removes lazy evaluation that was here before
# def _eta_reduce(expr: dt.Abstraction) -> dt.Expr | None:
#     """ λx.fx -> f    if x does not occur in f """
#     if not isinstance(expr.body, dt.Application):
#         return
#     if not isinstance(expr.body.argument, dt.Argument):
#         return
#     if expr.body.argument.name != expr.argument.name:
#         return
#     if _does_arg_occur_in_fn(expr.argument.name, expr.body.function):
#         return
#     return expr.body.function
#
#
# def _does_arg_occur_in_fn(arg_name: str, fn: dt.Expr) -> bool:
#     match type(fn):
#         case dt.Argument:
#             return arg_name == fn.name
#         case dt.Abstraction:
#             if fn.argument.name == arg_name:
#                 # Name is shadowed
#                 return False
#             return _does_arg_occur_in_fn(arg_name, fn.body)
#         case dt.Application:
#             return _does_arg_occur_in_fn(arg_name, fn.function) or _does_arg_occur_in_fn(arg_name, fn.argument)
#         case dt.Axiom:
#             return False
#         case dt.Statement:
#             return _does_arg_occur_in_fn(arg_name, fn.body)
