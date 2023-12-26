# The Slavya programming language

### ⚠️ Warning ⚠️
This project is nowhere near its end, thus it's very likely
    to dramatically change in the future.

## What's that?
"Slavya" is a new programming language heavily based on lambda calculus,
    it is in fact my petite attempt at implementing this beautiful concept
    as a general-purpose programming language.

This language's name is "Slavya" and this repo is its compiler.

(I'm too lazy rn to write this README, so bare minimum.)

## How to use?
Right now you can write your Slavya code to a file(e.g. `code.slavya`)
    and means to show it on the screen as the argument to `chop.compile(...)`
    function call in the `main` function in the `src/main.py` file.

## Examples:
The following program defines "zero" and a way to increment it
    in Church numerals. `main` returns 3.
```
* code.slavya
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

The examples given in the `code.slavya` at the moment of the commit is implements
calculation of the factorial of 5, purely in Slavya.
