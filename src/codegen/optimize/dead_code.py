from src.data_types import *
from src.codegen import analysis
from src import utils


def eliminate_dead_code(stmts: list[TypedTopLevel]) -> list[TypedTopLevel]:
    used = set()
    for stmt in stmts:
        if isinstance(stmt, Comment):
            continue
        used |= analysis.get_used_statements(stmt.data.body, stmts, is_final=True)
    used |= {utils.find(lambda s: s.data.name == "main", stmts)}
    result = []
    for idx in sorted(used):
        result.append(stmts[idx])
    return result
