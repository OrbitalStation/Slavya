//! !!!DO NOT DELETE THIS FILE!!!, compilation is impossible without it!

//!
//! The core functionality for Slavya to work
//!

use std::process::ExitCode;

///
/// A function with possible data attached
///
/// Can be in four states:
/// 1. Full (created by `F::new`). This state has some allocated data, thus it cannot be created at compile-time.
///     In this state `self.data` is a pointer to the tuple `(RefCountTy, <drop fn of the data>, <the data, size unknown>)`.
///     Performs reference counting on clone; drops data.
/// 2. ZST(zero sized type) - created by `F::zst`. This state has no data attached, it's just a pure function, which
///     is why it can be obtained in compile-time. `self.data` is null, no drops nor reference counting on clone.
/// 3. A generator - can be obtained via `F::gen`, also in compile time(that is the whole reason
///     for generators to exist). It performs a lazy evaluation of the underlying `F`.
///     `self.data` is `usize::MAX`, as we ensure it cannot be obtained naturally through `malloc` by using a modified version
///     of it - `F::malloc_non_usize_max`. `ptr` points to the generator function of signature `fn() -> F`.
///     A generator is evaluated at the first opportunity: at a clone or a call. When it is evaluated, the generator is
///     used as if it was the real value - `F::clone` returns it and `F::call` calls on it.
/// 4. A mark - created by `F::mark`. A special state used to mark arguments; solely used by AXIOM_FUN.
///    `self.ptr` is null, `self.data` is the number of the mark
///
pub struct F {
    ptr: TypeErased,
    data: TypeErased
}

impl F {
    /// Full form
    pub fn new <ActualData> (fun: fn(F, &ActualData) -> F, data: ActualData) -> F {
        use std::{ptr::{read, write}, mem::size_of};
        debug_assert!(size_of::<ActualData>() > 0, "use `F::zst` if you want to use a ZST");

        let pointee = unsafe { Self::malloc_non_usize_max(size_of::<RefCountTy>() + size_of::<fn(&mut ActualData)>() + size_of::<ActualData>()) };

        let refs = pointee as *mut RefCountTy;
        let drop_fn = (refs as usize + size_of::<RefCountTy>()) as *mut fn(&mut ActualData);
        let actual_data = (drop_fn as usize + size_of::<fn(&mut ActualData)>()) as *mut ActualData;

        unsafe {
            write(refs, 1);
            // `&mut ActualData` and `TypeErased` are both pointers, so same size
            // We can't access `ActualData::drop` so this closure is a replacement
            write(drop_fn, |x| drop(read(x)));
            write(actual_data, data)
        }

        Self {
            ptr: fun as TypeErased,
            data: pointee
        }
    }

    /// Ignore `usize` in `fun`
    pub const fn zst(fun: fn(F, usize) -> F) -> F {
        Self {
            ptr: fun as TypeErased,
            data: std::ptr::null()
        }
    }

    /// Abusing the system: lazy evaluation of `fun`
    pub const fn gen(fun: fn() -> F) -> F {
        Self {
            ptr: fun as TypeErased,

            // Indicator that the generator is not yet evaluated
            data: usize::MAX as TypeErased
        }
    }

    /// Used when calculating AXIOM_FUN
    pub const fn mark(mark: usize) -> F {
        Self {
            ptr: std::ptr::null(),
            data: mark as TypeErased
        }
    }

    pub fn call(&self, value: F) -> F {
        if self.is_gen() {
            return self.evaluate_gen().call(value)
        }
        if self.is_mark() {
            return if value.is_mark() && self.mark_value() == value.mark_value() {
                CHURCH_TRUE
            } else {
                CHURCH_FALSE
            }
        }
        // Even if `self.data` is null, `actual_data` calculates address
        //   but does not dereference it, so we're fine
        (unsafe { std::mem::transmute::<_, fn(F, TypeErased) -> F>(self.ptr) })(value, self.actual_data())
    }
}

pub fn type_check(filename: &str, array: &[(F, (usize, usize))]) -> ExitCode {
    static mut BOOLEAN: Option <bool> = None;

    const True: F = F::zst(|x, _| {
        unsafe { BOOLEAN = Some(true) }
        x
    });

    const False: F = F::zst(|x, _| {
        unsafe { BOOLEAN = Some(false) }
        x
    });

    fn fail(filename: &str, line: usize, column: usize, msg: &str) -> ExitCode {
        eprintln!("At {filename}:{line}:{column}\n{msg}");
        return ExitCode::FAILURE
    }

    for (ty, (line, column)) in array {
        ty.call(True).call(False).call(/* stub */ True);
        if let Some(boolean) = std::mem::replace(unsafe { &mut BOOLEAN }, None) {
            if !boolean {
                return fail(filename, *line, *column, "Typechecking failed")
            }
        } else {
            return fail(filename, *line, *column, "Not a type")
        }
    }

    ExitCode::SUCCESS
}

pub const AXIOM_ANY:    F = F::zst(axiom_any_final);
pub const AXIOM_FUN:    F = F::zst(axiom_fun_start);
pub const AXIOM_TY:     F = F::zst(axiom_ty_final);
pub const AXIOM_RET_TY: F = F::zst(axiom_ret_ty_final);
pub const AXIOM_ARG_TY: F = F::zst(axiom_arg_ty_final);

pub const FUN_FULL_TY:  F = F::gen(fun_full_ty);

const CHURCH_FALSE: F = F::zst(|_, _| F::zst(|y, _| y));
const CHURCH_TRUE:  F = F::zst(|x, _| F::new(|_, x| x.clone(), x));
const CHURCH_BOOL:  F = F::zst(axiom_bool_final);

const VOID_TY: F = F::zst(axiom_void_ty_final);

/* Next few functions are separate because we need to reference their address */

fn axiom_fun_start(arg: F, _: usize) -> F {
    F::new(axiom_fun_middle, arg)
}

fn axiom_fun_middle(ret: F, arg: &F) -> F {
    F::new(axiom_fun_final, (arg.clone(), ret))
}

fn axiom_fun_final(input: F, data: &(F, F)) -> F {
    static mut CURRENT_MARK: usize = 0;

    let Some((in2, out2)) = input.get_fun_arg_ty_and_ret_ty_gen_if_possible() else { return CHURCH_FALSE };
    let (r#in, out) = data;
    let arg_ok = in2.call(r#in.clone());

    let mark = F::mark(unsafe { CURRENT_MARK });
    unsafe { CURRENT_MARK += 1 }
    let out_generated = out.call(mark.clone());
    let out2_generated = out2.call(mark);
    unsafe { CURRENT_MARK -= 1 }

    let ret_ok = out_generated.call(out2_generated);
    let both = arg_ok.call(ret_ok).call(arg_ok.clone());
    return both
}

fn axiom_any_final(_: F, _: usize) -> F {
    CHURCH_TRUE
}

fn axiom_void_ty_final(_: F, _: usize) -> F {
    CHURCH_FALSE
}

/// Type `Ty` is defined recursively -- `Ty = fun Ty bool`,
///     that's why there are all these ceremonies around it
fn axiom_ty_final(f: F, _: usize) -> F {
    if f.is_axiom_of_type_ty() {
        CHURCH_TRUE
    } else {
        AXIOM_FUN.call(AXIOM_TY).call(CHURCH_BOOL).call(f)
    }
}

/// Ugly, dirty, terrible hack
/// Instead of properly defining bool as a type
///     we just give `f` two marks and see if it returns either,
///     and if that's the case, then we got either `true` or `false`
///     -- both of which are `bool`.
fn axiom_bool_final(f: F, _: usize) -> F {
    // Cannot start with `usize::MAX` because that may trigger `F` to think it is
    //     not a mark but a generator
    const MARK1: F = F::mark(usize::MAX - 1);
    const MARK2: F = F::mark(usize::MAX - 2);
    let returned = f.call(MARK1).call(MARK2);
    let p = MARK1.call(returned.clone());
    return p.call(p.clone()).call(MARK2.call(returned.clone()))
}

/// This is not a type and we do not need address of this function,
///     but it's separated for consistency
fn axiom_ret_ty_final(of: F, _: usize) -> F {
    let Some((_, out)) = of.get_fun_arg_ty_and_ret_ty_gen_if_possible() else { return VOID_TY };
    return out
}

fn axiom_arg_ty_final(of: F, _: usize) -> F {
    let Some((r#in, _)) = of.get_fun_arg_ty_and_ret_ty_gen_if_possible() else { return VOID_TY };
    return r#in
}

fn fun_full_ty() -> F {
    AXIOM_FUN.call(AXIOM_TY).call(F::zst(|_, _| AXIOM_FUN.call(AXIOM_FUN.call(AXIOM_TY).call(F::zst(|_, _| AXIOM_TY))).call(F::zst(|_, _| AXIOM_TY))))
}

type TypeErased = *const ();

extern "C" {
    fn malloc(num: usize) -> TypeErased;
    fn free(mem: TypeErased);
}

type RefCountTy = usize;
const MAX_REFS: RefCountTy = isize::MAX as RefCountTy;

impl F {
    /// Required for generators to be possible
    unsafe fn malloc_non_usize_max(len: usize) -> TypeErased {
        unsafe fn inner(len: usize) -> TypeErased {
            let result = malloc(len);
            assert!(!result.is_null(), "failed to allocate");
            result
        }

        let result = inner(len);
        if result as usize == usize::MAX {
            // Cannot give us this value again
            let result2 = inner(len);
            free(result);
            result2
        } else {
            result
        }
    }

    fn is_axiom_of_type_ty(&self) -> bool {
        if self.is_gen() {
            return self.evaluate_gen().is_axiom_of_type_ty()
        }
        let p = self.ptr as usize;
        return p == axiom_any_final as *const () as usize
        || p == axiom_ty_final as *const () as usize
        || p == axiom_bool_final as *const () as usize
        || p == axiom_void_ty_final as *const () as usize
        // || p == axiom_fun_final as *const () as usize
        // Not included because it can lead to situations where e.g. `(typeof f) f` == true
    }

    fn get_fun_arg_ty_and_ret_ty_gen_if_possible(&self) -> Option <(F, F)> {
        if self.is_gen() {
            return self.evaluate_gen().get_fun_arg_ty_and_ret_ty_gen_if_possible()
        }

        let p = self.ptr as usize;
        if p == axiom_fun_final as *const () as usize {
            let data = unsafe { &*(self.actual_data() as *const (F, F)) };
            return Some((data.0.clone(), data.1.clone()))
        } else if p == axiom_fun_start as *const () as usize {
            return fun_full_ty().get_fun_arg_ty_and_ret_ty_gen_if_possible()
        } else if self.is_axiom_of_type_ty() {
            return Some((AXIOM_TY, CHURCH_BOOL))
        } else if p == axiom_fun_middle as *const () as usize {
            return Some((AXIOM_FUN.call(AXIOM_TY).call(F::zst(|_, _| AXIOM_TY)), F::zst(|_, _| AXIOM_TY)))
        }

        None
    }

    #[inline]
    fn refs(&self) -> RefCountTy {
        unsafe { std::ptr::read(self.data as *const RefCountTy) }
    }

    #[inline]
    fn set_refs(&self, new: RefCountTy) {
        unsafe { std::ptr::write(self.data as *mut RefCountTy, new) }
    }

    #[inline]
    fn data_drop_fn(&self) -> fn(TypeErased) {
        unsafe { std::ptr::read((self.data as usize + std::mem::size_of::<RefCountTy>()) as *const fn(TypeErased)) }
    }

    #[inline]
    fn actual_data(&self) -> TypeErased {
        use std::mem::size_of;
        (self.data as usize + size_of::<RefCountTy>() + size_of::<fn(TypeErased)>()) as TypeErased
    }

    #[inline]
    fn mark_value(&self) -> usize {
        self.data as usize
    }

    #[inline]
    fn is_zst(&self) -> bool {
        self.data.is_null()
    }

    #[inline]
    fn is_gen(&self) -> bool {
        self.data as usize == usize::MAX
    }

    #[inline]
    fn is_mark(&self) -> bool {
        self.ptr.is_null()
    }

    fn evaluate_gen(&self) -> F {
        unsafe { std::mem::transmute::<_, fn() -> F>(self.ptr)() }
    }
}

impl Clone for F {
    fn clone(&self) -> Self {
        if self.is_gen() {
            return self.evaluate_gen()
        }
        if !self.is_zst() && !self.is_mark() {
            let new_refs = self.refs() + 1;
            assert!(new_refs < MAX_REFS, "too many F clones");
            self.set_refs(new_refs)
        }
        F {
            ptr: self.ptr,
            data: self.data
        }
    }
}

impl Drop for F {
    fn drop(&mut self) {
        if self.is_mark() || self.is_gen() || self.is_zst() {
            return
        }
        let new_refs = self.refs() - 1;
        if new_refs > 0 {
            self.set_refs(new_refs)
        } else {
            self.data_drop_fn()(self.actual_data());
            unsafe { free(self.data) }
        }
    }
}
