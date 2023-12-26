from src.chop import Chopper


def read_file(filename: str):
    with open(filename, "rt") as file:
        return map(str.strip, file.read().split("\n"))


def main(code_file: str):
    chop = Chopper(code_file)
    chop.iterate(read_file(code_file))

    chop.compile("""
static mut COUNTER: usize = 0;
fn main() {
    f_main.call(F::zst(|x, _| {
        unsafe { COUNTER += 1 }
        x
    })).call(f_id);
    unsafe { println!("{COUNTER}") }
}
    """)


if __name__ == '__main__':
    main("./code.slavya")
