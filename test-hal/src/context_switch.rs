//! Deterministic fake [`tyrne_hal::ContextSwitch`] for host-side tests.
//!
//! A real context switch saves/restores CPU registers and swaps stacks,
//! which a host process cannot perform meaningfully. `FakeContextSwitch`
//! instead **records** that a switch (or an `init_context`) happened, so
//! scheduler unit tests can assert the scheduler invoked the switch the
//! expected number of times and seeded each new task's context exactly
//! once — without actually changing the host's control flow.
//!
//! Pair with [`crate::FakeCpu`] when a test needs both the [`Cpu`] surface
//! (IRQ-mask save/restore with DAIF polarity) and the [`ContextSwitch`]
//! surface (e.g. asserting that interrupts are masked across a switch):
//! a single test type can hold one of each, or a test can construct both
//! and drive them in concert.
//!
//! [`Cpu`]: tyrne_hal::Cpu
//! [`ContextSwitch`]: tyrne_hal::ContextSwitch

use std::sync::Mutex;
use tyrne_hal::ContextSwitch;

/// Saved register state for one cooperative task, as modelled by
/// [`FakeContextSwitch`].
///
/// Carries no real registers. `switched` flips to `true` the first time
/// this context is passed as the `current` argument of
/// [`ContextSwitch::context_switch`] (i.e. its owning task was suspended);
/// `initialized` flips to `true` when [`ContextSwitch::init_context`]
/// seeds it. Tests can assert on both. The `entry_addr` / `stack_top`
/// fields record the last `init_context` arguments so a test can confirm
/// the scheduler seeded the intended entry point and stack.
#[derive(Default, Debug, Clone, PartialEq, Eq)]
pub struct FakeTaskContext {
    /// Set when this context was saved as `current` by `context_switch`.
    pub switched: bool,
    /// Set when this context was seeded by `init_context` **or**
    /// `init_user_context`.
    pub initialized: bool,
    /// Set when this context was seeded by `init_user_context` (an EL0 task)
    /// rather than `init_context` (an EL1 kernel task). Lets a test confirm
    /// the scheduler chose the userspace first-entry path.
    pub is_user: bool,
    /// Entry-point address from the last `init_context` / `init_user_context`
    /// call (as `usize`): the kernel `fn` entry, or the userspace entry VA.
    pub entry_addr: usize,
    /// Userspace stack top from the last `init_user_context` call (as `usize`);
    /// `0` for a context seeded by `init_context`.
    pub user_sp: usize,
    /// Stack-top pointer (as `usize`) from the last `init_context` call, or the
    /// kernel stack top (the task's `SP_EL1`) from the last
    /// `init_user_context` call.
    pub stack_top: usize,
}

/// A [`ContextSwitch`] that records switch / init call counts for test
/// assertions instead of performing a real register save/restore.
///
/// # Example
///
/// ```
/// use tyrne_test_hal::{FakeContextSwitch, FakeTaskContext};
/// use tyrne_hal::ContextSwitch;
///
/// fn never_returns() -> ! {
///     panic!("the fake never calls task entry points")
/// }
///
/// let cs = FakeContextSwitch::new();
/// let mut a = FakeTaskContext::default();
/// let mut stack = [0u8; 512];
/// let top = stack.as_mut_ptr().wrapping_add(stack.len());
///
/// // SAFETY:
/// // (a) `ContextSwitch::init_context` is `unsafe` — for a real CPU it would
/// //     install `top` as the stack pointer and `never_returns` as the entry.
/// // (b) `top` is one-past a live 512-byte stack and `never_returns` diverges;
/// //     `FakeContextSwitch` only records the arguments, dereferencing neither.
/// // (c) No safe shim exists: the trait method is `unsafe` by contract, so the
/// //     call site must discharge it even for the recording fake.
/// unsafe { cs.init_context(&mut a, never_returns, top) };
/// assert!(a.initialized);
/// assert_eq!(cs.init_count(), 1);
///
/// let b = FakeTaskContext::default();
/// // SAFETY:
/// // (a) `ContextSwitch::context_switch` is `unsafe` — for a real CPU it
/// //     saves/restores callee-saved state through the context pointers.
/// // (b) `a`/`b` are live `FakeTaskContext`s; the fake performs no real switch
/// //     and never dereferences register state — it only records.
/// // (c) The trait method is `unsafe` by contract; no safe alternative exists.
/// unsafe { cs.context_switch(&mut a, &b) };
/// assert!(a.switched);
/// assert_eq!(cs.switch_count(), 1);
/// ```
pub struct FakeContextSwitch {
    state: Mutex<FakeContextSwitchState>,
}

#[derive(Default)]
struct FakeContextSwitchState {
    switch_count: u64,
    init_count: u64,
}

impl FakeContextSwitch {
    /// Construct a `FakeContextSwitch` with zeroed call counts.
    #[must_use]
    pub fn new() -> Self {
        Self {
            state: Mutex::new(FakeContextSwitchState::default()),
        }
    }

    /// Return the number of [`ContextSwitch::context_switch`] calls so far.
    ///
    /// # Panics
    ///
    /// Panics if the internal mutex has been poisoned.
    #[must_use]
    pub fn switch_count(&self) -> u64 {
        self.locked().switch_count
    }

    /// Return the number of [`ContextSwitch::init_context`] **or
    /// [`ContextSwitch::init_user_context`]** calls so far (a single shared
    /// counter — both seed a context, so both increment it).
    ///
    /// # Panics
    ///
    /// Panics if the internal mutex has been poisoned.
    #[must_use]
    pub fn init_count(&self) -> u64 {
        self.locked().init_count
    }

    fn locked(&self) -> std::sync::MutexGuard<'_, FakeContextSwitchState> {
        self.state.lock().expect("FakeContextSwitch mutex poisoned")
    }
}

impl Default for FakeContextSwitch {
    fn default() -> Self {
        Self::new()
    }
}

impl ContextSwitch for FakeContextSwitch {
    type TaskContext = FakeTaskContext;

    /// # Safety
    ///
    /// Inherits the [`ContextSwitch::context_switch`] trait contract, but
    /// the fake performs **no** register save/restore and no stack swap —
    /// it only marks `current.switched` and increments a counter. It
    /// therefore never dereferences a real saved context and cannot
    /// corrupt host state regardless of the caller's invariants. Callers
    /// in tests still satisfy the contract (IRQs masked, valid contexts)
    /// to mirror production call sequences.
    unsafe fn context_switch(&self, current: &mut Self::TaskContext, _next: &Self::TaskContext) {
        current.switched = true;
        self.locked().switch_count += 1;
    }

    /// # Safety
    ///
    /// Inherits the [`ContextSwitch::init_context`] trait contract. The
    /// fake records the requested `entry` / `stack_top` (as `usize`) and
    /// marks the context initialised; it neither dereferences `stack_top`
    /// nor calls `entry`, so no real stack or function pointer is touched.
    unsafe fn init_context(
        &self,
        ctx: &mut Self::TaskContext,
        entry: fn() -> !,
        stack_top: *mut u8,
    ) {
        ctx.initialized = true;
        // Fully re-seed as a *kernel* context: clear any user-path markers a
        // prior `init_user_context` left, so a reused slot does not report
        // stale `is_user` / `user_sp` (init_context overwrites the context).
        ctx.is_user = false;
        ctx.user_sp = 0;
        ctx.entry_addr = entry as *const () as usize;
        ctx.stack_top = stack_top as usize;
        self.locked().init_count += 1;
    }

    /// # Safety
    ///
    /// Inherits the [`ContextSwitch::init_user_context`] trait contract. The
    /// fake records the requested `user_entry` / `user_sp` (as `usize`) and the
    /// kernel `kernel_stack_top`, marks the context `initialized` + `is_user`,
    /// and counts it; it performs no real EL0 entry and dereferences neither
    /// the entry VA, the user stack, nor the kernel stack.
    unsafe fn init_user_context(
        &self,
        ctx: &mut Self::TaskContext,
        user_entry: usize,
        user_sp: usize,
        kernel_stack_top: *mut u8,
    ) {
        ctx.initialized = true;
        ctx.is_user = true;
        ctx.entry_addr = user_entry;
        ctx.user_sp = user_sp;
        ctx.stack_top = kernel_stack_top as usize;
        self.locked().init_count += 1;
    }
}

#[cfg(test)]
mod tests {
    use super::{FakeContextSwitch, FakeTaskContext};
    use tyrne_hal::ContextSwitch;

    fn never_returns() -> ! {
        panic!("FakeContextSwitch never calls task entry points")
    }

    #[test]
    fn init_context_records_entry_stack_and_marks_initialized() {
        let cs = FakeContextSwitch::new();
        let mut ctx = FakeTaskContext::default();
        let mut stack = [0u8; 512];
        let top = stack.as_mut_ptr().wrapping_add(stack.len());

        // SAFETY:
        // (a) `init_context` is `unsafe` — for a real CPU it installs `top`
        //     as the stack pointer and `never_returns` as the entry point.
        // (b) `top` is one-past a live 512-byte stack and `never_returns`
        //     diverges; the fake only records the pointer, never derefs it.
        // (c) The trait method is `unsafe` by contract; no safe shim exists.
        unsafe { cs.init_context(&mut ctx, never_returns, top) };

        assert!(ctx.initialized);
        // Under Miri a function pointer cast to an integer is given a
        // synthetic, non-stable address: two separate `fn as usize`
        // exposures of the same function need not be equal (they are on real
        // hardware). Assert exact equality only off-Miri; under Miri confirm
        // a non-zero value was recorded.
        #[cfg(not(miri))]
        assert_eq!(ctx.entry_addr, never_returns as *const () as usize);
        #[cfg(miri)]
        assert_ne!(ctx.entry_addr, 0);
        assert_eq!(ctx.stack_top, top as usize);
        assert!(!ctx.is_user);
        assert_eq!(ctx.user_sp, 0);
        assert_eq!(cs.init_count(), 1);
        assert_eq!(cs.switch_count(), 0);
    }

    #[test]
    fn init_user_context_records_user_entry_sp_kernel_stack_and_marks_is_user() {
        let cs = FakeContextSwitch::new();
        let mut ctx = FakeTaskContext::default();
        let mut kstack = [0u8; 512];
        let ktop = kstack.as_mut_ptr().wrapping_add(kstack.len());
        // Opaque userspace VAs — the fake records but never dereferences them.
        let user_entry = 0x0080_0000usize;
        let user_sp = 0x0080_2000usize;

        // SAFETY:
        // (a) `init_user_context` is `unsafe` — for a real CPU it would seed an
        //     EL0 first-entry (SP_EL0 / ELR_EL1 / SPSR_EL1) and `ERET` there.
        // (b) `ktop` is one-past a live 512-byte kernel stack; `user_entry` /
        //     `user_sp` are opaque integers the fake only records, never derefs.
        // (c) The trait method is `unsafe` by contract; no safe shim exists.
        unsafe { cs.init_user_context(&mut ctx, user_entry, user_sp, ktop) };

        assert!(ctx.initialized);
        assert!(ctx.is_user);
        assert_eq!(ctx.entry_addr, user_entry);
        assert_eq!(ctx.user_sp, user_sp);
        assert_eq!(ctx.stack_top, ktop as usize);
        assert_eq!(cs.init_count(), 1);
        assert_eq!(cs.switch_count(), 0);
    }

    #[test]
    fn init_context_clears_prior_user_markers_on_reuse() {
        // A reused context first seeded as an EL0 task, then re-seeded by the
        // kernel path, must not report stale is_user / user_sp.
        let cs = FakeContextSwitch::new();
        let mut ctx = FakeTaskContext::default();
        let mut kstack = [0u8; 512];
        let ktop = kstack.as_mut_ptr().wrapping_add(kstack.len());

        // SAFETY: opaque integers + a one-past-end ptr; the fake only records,
        // never dereferences them or performs a real EL0 entry.
        unsafe { cs.init_user_context(&mut ctx, 0x0080_0000, 0x0080_2000, ktop) };
        assert!(ctx.is_user);
        assert_eq!(ctx.user_sp, 0x0080_2000);

        // SAFETY: as `init_context`'s doctest — the fake records `entry`/
        // `stack_top` and never calls/derefs them.
        unsafe { cs.init_context(&mut ctx, never_returns, ktop) };
        assert!(ctx.initialized);
        assert!(!ctx.is_user, "init_context must clear the user-path marker");
        assert_eq!(ctx.user_sp, 0, "init_context must clear user_sp");
    }

    #[test]
    fn context_switch_marks_current_and_counts() {
        let cs = FakeContextSwitch::new();
        let mut a = FakeTaskContext::default();
        let b = FakeTaskContext::default();

        // SAFETY:
        // (a) `context_switch` is `unsafe` — for a real CPU it saves/restores
        //     callee-saved state through the two context pointers.
        // (b) `a`/`b` are live `FakeTaskContext`s; the fake performs no real
        //     switch and only records, dereferencing no register state.
        // (c) The trait method is `unsafe` by contract; no safe alternative.
        unsafe { cs.context_switch(&mut a, &b) };
        assert!(a.switched);
        assert!(!b.switched);
        assert_eq!(cs.switch_count(), 1);

        // SAFETY: as the first `context_switch` call above — (a) the trait
        // method is `unsafe`, (b) the fake only records over live contexts and
        // derefs no register state, (c) no safe alternative to the `unsafe` API.
        unsafe { cs.context_switch(&mut a, &b) };
        assert_eq!(cs.switch_count(), 2);
    }

    #[test]
    fn default_context_is_uninitialized_and_unswitched() {
        let ctx = FakeTaskContext::default();
        assert!(!ctx.initialized);
        assert!(!ctx.switched);
        assert!(!ctx.is_user);
        assert_eq!(ctx.entry_addr, 0);
        assert_eq!(ctx.user_sp, 0);
        assert_eq!(ctx.stack_top, 0);
    }
}
