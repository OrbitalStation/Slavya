from src.parse import chop
from os.path import realpath
from src.codegen.compile import ccompile
from src.codegen.optimize import optimize
from src.data_types import TopLevel, Comment


def read_file(filename: str):
    with open(filename, "rt") as file:
        return filter(len, map(str.strip, file.read().split("\n")))


def parse_file(filename: str):
    info = chop.Info(filename, 1, [])
    for line in read_file(filename):
        info.top_level.append(chop.top_level(info, chop.Parseable(line)))
    return info.top_level


def optimise(stmts: list[TopLevel]) -> list[TopLevel]:
    result = []
    while len(stmts) > 0:
        if isinstance(stmts[0], Comment):
            result.append(stmts.pop(0))
            continue
        result.append(optimize(stmts.pop(0), result))
    return result


def main(code_file: str):
    code_file = realpath(code_file)
    parsed = parse_file(code_file)
    optimized = optimise(parsed)
    ccompile(optimized, """
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
