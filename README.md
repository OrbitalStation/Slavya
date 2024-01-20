# The Slavya programming language

### ⚠️ Warning ⚠️
This project is nowhere near its end, thus it's very likely
    to dramatically change in the future.

It also currently only works on *nix OS(Linux, etc.).

## What's that?
"Slavya" is a new programming language heavily based on lambda calculus,
    it is in fact my petite attempt at implementing this beautiful concept
    as a general-purpose programming language.

This language's name is "Slavya" and this repo is its compiler.

(I'm too lazy rn to write this README, so bare minimum.)

## How to use?
Right now you can write your Slavya code to a file(e.g. `code.🌲`)
    and means to show it on the screen as the argument to `ccompile(...)`
    function call in the `main` function in the `src/main.py` file.
Then you should run `main.py` with python(version >=3.12) interpreter.
It also requires `rustc` compiler.

Currently, uses `.🌲` file extension(`.slavya` is also being considered).

## Examples:
The following program defines "zero" and a way to increment it
    in Church numerals. `main` returns 3.

NOTE: it will not run right now, because I'm in process of introducing types to the language.
```
* code.🌲
* ^^^^^^^^^^^ A comment btw
* It starts with an asterisk(`*`) and goes till the end of line
0 = f -> x -> x
succ = n -> f -> x -> f (n f x)

main = succ (succ (succ 0))
```
```rust
// argument to chop.compile(...)
static mut COUNTER: usize = 0;
fn main() {
    f_main.call(F::zst(|x, _| {
        unsafe { COUNTER += 1 }
        x
    })).call(f_main);
    unsafe { println!("{COUNTER}") }
}
```
The argument is used to show this "3" on the screen.
It transforms Slavya's Church 3 into a Rust one and displays it.

## License
Licensed under Apache-2.0 conditions(check out `LICENSE.md`)
