def find(predicate, collection) -> int:
    last_matched_index = 0
    for element in collection:
        if predicate(element):
            return last_matched_index
        last_matched_index += 1
    return -1


def inverse_predicate(predicate):
    return lambda condition: not predicate(condition)


def unzip(fn):
    return lambda args: fn(*args)


def rpartial(fn, arg):
    return lambda *args: fn(*args, arg)


def ignore1(fn):
    return lambda _, *rest: fn(*rest)


def is_none1(tup):
    return tup[0] is None
