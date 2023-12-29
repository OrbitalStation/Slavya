import src.data_types as dt


def get_bound_arguments(expr: dt.Expr, arguments: tuple[str, ...]):
    from src.codegen.compile import modify_arg

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


def _add_uniquely[T](a: tuple[T, ...], b: tuple[T, ...]):
    a = list(a)
    for item in b:
        if item not in a:
            a.append(item)
    return tuple(a)
