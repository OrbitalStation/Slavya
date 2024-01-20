from src.parse import chop
from os.path import realpath
from src.codegen import typecheck, optimize, compile
from src.data_types import TopLevel, Comment


def read_file(filename: str):
    with open(filename, "rt") as file:
        return filter(len, map(str.strip, file.read().split("\n")))


def parse_file(filename: str):
    info = chop.Info(filename, 1, [])
    for line in read_file(filename):
        info.top_level.append(chop.top_level(info, chop.Parseable(line)))
    return info.top_level


def typecheck_and_optimize(top_level: list[TopLevel]):
    result = []
    used_stmts = set()
    for stmt in top_level:
        if isinstance(stmt, Comment):
            result.append(stmt)
            continue

        stmt, used = typecheck.stmt(stmt, result, top_level)
        used_stmts |= used

        stmt = optimize.stmt(stmt, result)

        result.append(stmt)
    return result


def main(code_file: str):
    code_file = realpath(code_file)

    parsed = parse_file(code_file)

    t_and_o = typecheck_and_optimize(parsed)

    eliminated = optimize.eliminate_dead_code(t_and_o)

    compile.ccompile(eliminated, """
static mut COUNTER: usize = 0;
fn main() {
    f_main.call(F::zst(|x, _| {
        unsafe { COUNTER += 1 }
        x
    })).call(f_main);
    unsafe { println!("{COUNTER}") }
    
}
    """)


if __name__ == '__main__':
    main("./code.🌲")
