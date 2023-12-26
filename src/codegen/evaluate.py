import src.data_types as dt
from src.data_types import Axiom


def evaluate(expr, arguments=None):
    """
    Evaluate Slavya data structures as Python equivalents
    """
    arguments = arguments or {}
    match type(expr):
        case dt.Argument:
            return arguments[expr.name]
        case dt.Abstraction:
            return lambda arg: evaluate(expr.body, arguments | {expr.argument.name: arg})
        case dt.Application:
            return evaluate(expr.function, arguments)(evaluate(expr.argument, arguments))
        case dt.Axiom:
            return _axiom(expr)
        case dt.Statement:
            return evaluate(expr.body)


def _axiom(axiom):
    """ Nested matches are hell """
    match axiom:
        case Axiom.ANY:
            return lambda _: _CHURCH_TRUE


_CHURCH_TRUE = lambda x: lambda y: x
