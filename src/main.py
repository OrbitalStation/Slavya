from src.chop import Chopper
from src.data_types import Comment
from src.codegen.compile import ccompile


def read_file(filename: str):
    with open(filename, "rt") as file:
        return map(str.strip, file.read().split("\n"))


def main(code_file: str):
    chop = Chopper(code_file)
    statements = chop.iterate(read_file(code_file))
    no_comments = filter(lambda s: not isinstance(s, Comment), statements)

    ccompile(no_comments, """
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
