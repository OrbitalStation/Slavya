def find(predicate, collection) -> int:
    last_matched_index = 0
    for element in collection:
        if predicate(element):
            return last_matched_index
        last_matched_index += 1
    return -1


def inverse_predicate(predicate):
    return lambda condition: not predicate(condition)


def or_else(something_or_none, generator):
    if something_or_none is not None:
        return something_or_none
    return generator()


def unzip(fn):
    return lambda args: fn(*args)


def mixin(mixin_name: str, what_to_plug, pass_cls: bool = False):
    def take_class(cls):
        return type(cls.__name__, cls.__bases__, cls.__dict__
                    | {mixin_name: what_to_plug if not pass_cls else what_to_plug(cls)})
    return take_class
