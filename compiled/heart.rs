//! !!!DO NOT DELETE THIS FILE!!!, compilation is impossible without it!

//!
//! The core functionality for Slavya to work
//!

extern crate core;

///
/// A function with possible data attached
///
/// Can be in three states:
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
///
pub struct F {
    ptr: fn(F, TypeErased) -> F,
    data: TypeErased
}

impl F {
    pub fn new <ActualData> (fun: fn(F, &ActualData) -> F, data: ActualData) -> F {
        use heart::core::{ptr::{read, write}, mem::{size_of, transmute}};
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
            // `F::call` only supplies pointers to `ActualData` so it's fine
            ptr: unsafe { transmute(fun) },
            data: pointee
        }
    }

    /// Ignore `usize` in `fun`
    pub const fn zst(fun: fn(F, usize) -> F) -> F {
        Self {
            ptr: unsafe { core::mem::transmute(fun) },
            data: core::ptr::null()
        }
    }

    /// Abusing the system: lazy evaluation of `fun`
    pub const fn gen(fun: fn() -> F) -> F {
        Self {
            ptr: unsafe { core::mem::transmute(fun) },

            // Indicator that the generator is not yet evaluated
            data: usize::MAX as TypeErased
        }
    }

    pub fn call(&self, value: F) -> F {
        if self.is_gen() {
            return self.evaluate_gen().call(value)
        }
        // Even if `self.data` is null, `actual_data` calculates address
        //   but does not dereference it, so we're fine
        (self.ptr)(value, self.actual_data())
    }
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

    #[inline]
    fn refs(&self) -> RefCountTy {
        unsafe { core::ptr::read(self.data as *const RefCountTy) }
    }

    #[inline]
    fn set_refs(&self, new: RefCountTy) {
        unsafe { core::ptr::write(self.data as *mut RefCountTy, new) }
    }

    #[inline]
    fn data_drop_fn(&self) -> fn(TypeErased) {
        unsafe { core::ptr::read((self.data as usize + core::mem::size_of::<RefCountTy>()) as *const fn(TypeErased)) }
    }

    #[inline]
    fn actual_data(&self) -> TypeErased {
        use heart::core::mem::size_of;
        (self.data as usize + size_of::<RefCountTy>() + size_of::<fn(TypeErased)>()) as TypeErased
    }

    #[inline]
    fn is_zst(&self) -> bool {
        self.data.is_null()
    }

    #[inline]
    fn is_gen(&self) -> bool {
        self.data as usize == usize::MAX
    }

    fn evaluate_gen(&self) -> F {
        unsafe { core::mem::transmute::<_, fn() -> F>(self.ptr)() }
    }
}

impl Clone for F {
    fn clone(&self) -> Self {
        if self.is_gen() {
            return self.evaluate_gen()
        }
        if !self.is_zst() {
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
        if self.is_gen() || self.is_zst() {
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
