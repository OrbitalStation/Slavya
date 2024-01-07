from src.parse import chop
from os.path import realpath
from src.codegen.compile import ccompile


def read_file(filename: str):
    with open(filename, "rt") as file:
        return filter(len, map(str.strip, file.read().split("\n")))


def parse_file(filename: str):
    info = chop.Info(filename, 1, [])
    for line in read_file(filename):
        info.top_level.append(chop.top_level(info, chop.Parseable(line)))
    return info.top_level


def main(code_file: str):
    code_file = realpath(code_file)
    parsed = parse_file(code_file)
    ccompile(parsed, """
static mut COUNTER: usize = 0;
fn main() {
    f_main.call(F::zst(|x, _| {
        unsafe { COUNTER += 1 }
        x
    })).call(F::zst(|x, _| {
        unsafe { COUNTER += 100 }
        x
    })).call(f_main);
    unsafe { println!("{COUNTER}") }
    
}
    """)


if __name__ == '__main__':
    main("./code.🌲")
