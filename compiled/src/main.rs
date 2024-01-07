
#![allow(unused_variables, non_upper_case_globals, dead_code)]
mod heart;
use heart::*;
const f_any: F = AXIOM_ANY;
const f_fun: F = AXIOM_FUN;
const f_Ty: F = AXIOM_TY;
const f_id: F = F::zst(|a_x, _| a_x.clone());
const f_true: F = F::zst(|a_x, _| F::new(|a_y, data| data.0.clone(), (a_x.clone(),)));
const f_false: F = F::zst(|a_x, _| F::zst(|a_y, _| a_y.clone()));
const f_idTy: F = F::gen(|| f_fun.call(f_any).call(F::zst(|a_x, _| a_x.clone())));
const f_main: F = F::gen(|| f_idTy.call(f_idTy));

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
    
    