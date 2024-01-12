from src import data_types as dt
from src.codegen import analysis
from src import utils


def optimize(stmt: dt.Statement, stmts: list[dt.TopLevel]) -> dt.Statement:
    name, body = stmt.name, stmt.body

    body = _statement_replacing_pass(body, stmts)
    body = _beta_reduction_pass(body)

    return dt.Statement(name, body)


def _statement_replacing_pass(body: dt.Expr, stmts: list[dt.TopLevel]) -> dt.Expr:
    def transform(expr: dt.Statement) -> dt.Statement:
        return stmts[utils.find(lambda s: isinstance(s, dt.Statement) and s.name == expr.name, stmts)]
    return analysis.visit_expr(body, lambda e: isinstance(e, dt.Statement), transform)


def _beta_reduction_pass(body: dt.Expr) -> dt.Expr:
    def transform(expr: dt.Application):
        function = expr.function
        while isinstance(function, dt.Statement):
            function = function.body
        if isinstance(function, dt.Abstraction):
            reduced = analysis.visit_expr(
                function.body,
                lambda e: isinstance(e, dt.Argument) and e.name == function.argument.name,
                lambda _: expr.argument
            )
            # Repeat beta-reduction because replacement may have generated new possible reduction candidates
            return _beta_reduction_pass(reduced)
        return expr
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
