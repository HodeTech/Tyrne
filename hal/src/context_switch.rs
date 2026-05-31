//! Cooperative context-switch extension for BSPs.
//!
//! See [ADR-0020] for the design rationale. This trait is deliberately
//! separate from [`Cpu`][crate::Cpu] to preserve `Cpu`'s object-safety;
//! the scheduler is generic over `C: ContextSwitch` and does not use
//! dynamic dispatch.
//!
//! [ADR-0020]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0020-cpu-trait-v2-context-switch.md

/// Context-switch extension for BSPs that support cooperative task switching.
///
/// Separate from [`Cpu`][crate::Cpu] to preserve `Cpu`'s object-safety.
/// The scheduler is generic over `C: ContextSwitch`; it never needs
/// dynamic dispatch.
///
/// # Safety contract
///
/// Implementations must ensure that `context_switch` atomically saves
/// all callee-saved registers of the current execution context and
/// restores all callee-saved registers of the next context — i.e. the
/// target ABI's full callee-saved register set. On aarch64 (AAPCS64)
/// that is the general-purpose callee-saved registers `x19`–`x28`,
/// `x29` (fp), `x30` (lr), `sp`, **and the SIMD/FP callee-saved
/// registers `d8`–`d15` (the lower 64 bits of `v8`–`v15`) whenever FP
/// is enabled (`CPACR_EL1.FPEN ≠ 0`)**. Omitting `d8`–`d15` silently
/// corrupts FP state across a yield: the compiler may allocate those
/// registers for any task and does not emit callee-save spills across a
/// cooperative `context_switch` call, so the corruption is
/// data-dependent and survives smoke testing. From the perspective of
/// both call sites, `context_switch` appears to return normally — the
/// saving side resumes here when it is later selected as `next`.
pub trait ContextSwitch: Send + Sync {
    /// The saved register state for one cooperative task.
    ///
    /// Must be `Default` so the scheduler can zero-initialise a slot
    /// before `init_context` fills it in. Must be `Send` so contexts
    /// can be moved between (future) CPU cores.
    type TaskContext: Default + Send;

    /// Save the calling task's register state into `current` and resume
    /// the task whose state was saved in `next`.
    ///
    /// When this task is later resumed (by another call to
    /// `context_switch` with this `current` as the `next` argument),
    /// execution continues as if `context_switch` returned normally.
    ///
    /// # Safety
    ///
    /// - Interrupts must be disabled before this call. An IRQ firing
    ///   mid-switch would observe a partially saved state.
    /// - `current` must be valid for the entire time this task is
    ///   suspended; the caller is responsible for keeping the context
    ///   array alive.
    /// - `next` must contain a context previously written by
    ///   `context_switch` or fully initialised by `init_context`.
    ///   Restoring an uninitialised context is undefined behaviour.
    /// - The implementation must save and restore the **full** callee-
    ///   saved register set for the target ABI — see the trait-level
    ///   `# Safety contract`. On aarch64 this includes the SIMD/FP
    ///   callee-saved registers `d8`–`d15` (lower 64 bits of `v8`–`v15`)
    ///   whenever FP is enabled (`CPACR_EL1.FPEN ≠ 0`), not only the
    ///   general-purpose `x19`–`x28` / `x29` / `x30` / `sp`.
    unsafe fn context_switch(&self, current: &mut Self::TaskContext, next: &Self::TaskContext);

    /// Write an initial register state into `ctx` so that the first
    /// restore begins executing `entry` with `stack_top` as the initial
    /// stack pointer.
    ///
    /// # Safety
    ///
    /// - `stack_top` must point one byte past the top of a
    ///   sufficiently-sized (≥ 512 bytes recommended for aarch64),
    ///   16-byte-aligned stack region that remains valid for the
    ///   task's entire lifetime.
    /// - `entry` must be a `fn() -> !` that never returns; returning
    ///   from a task entry function is undefined behaviour.
    unsafe fn init_context(
        &self,
        ctx: &mut Self::TaskContext,
        entry: fn() -> !,
        stack_top: *mut u8,
    );

    /// Write an initial register state into `ctx` so that the first restore
    /// begins **dropping to EL0**: the BSP's enter-userspace trampoline sets
    /// `SP_EL0 = user_sp`, `ELR_EL1 = user_entry`, and `SPSR_EL1` to the EL0
    /// `PSTATE` (v1: `EL0t` with `DAIF` masked — cooperative, no preemption),
    /// then `ERET`s into the task at `user_entry`.
    ///
    /// Unlike [`init_context`][Self::init_context] — which seeds an EL1
    /// kernel-thread entry from a `fn() -> !` — this seeds a *userspace*
    /// first entry. `kernel_stack_top` becomes the task's `SP_EL1`, the
    /// kernel stack the EL0→EL1 trap path runs on (the same value the
    /// cooperative restore installs as the running stack, so a subsequent
    /// `SVC`/exception lands on it — closing the `SP_EL1` gate by
    /// construction). The trampoline runs exactly once per task (first
    /// dispatch); later resumes are ordinary cooperative switches. See
    /// [ADR-0037].
    ///
    /// # Safety
    ///
    /// - `kernel_stack_top` must be one byte past a 16-byte-aligned kernel
    ///   stack region valid for the task's entire lifetime; it becomes the
    ///   task's `SP_EL1`. **Size contract (stronger than
    ///   [`init_context`][Self::init_context]'s cooperative ≥ 512 bytes):**
    ///   every EL0→EL1 trap (`+0x400`) lands on this stack and pushes the full
    ///   ~272-byte syscall/exception trap frame *plus* the kernel handler call
    ///   tree, so the region must accommodate that trap-time worst case — not
    ///   merely the cooperative-switch frame.
    /// - `user_entry` must be a valid, EL0-executable userspace VA, and
    ///   `user_sp` a valid, 16-byte-aligned userspace stack top, **both mapped
    ///   and EL0-reachable in the task's address space before it is first
    ///   dispatched**. The implementation does not validate them; an unmapped
    ///   `user_entry` faults on the first EL0 instruction fetch.
    /// - That address space must be **ACTIVE** at first dispatch — its
    ///   `TTBR0_EL1` installed and `EPD0` cleared (the scheduler's activation
    ///   hook must have fired for the task) — so the EL0 entry fetch and
    ///   user-stack access translate. The BSP trampoline that consumes this
    ///   context installs no `TTBR0` of its own.
    ///
    /// [ADR-0037]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0037-el0-entry-context.md
    unsafe fn init_user_context(
        &self,
        ctx: &mut Self::TaskContext,
        user_entry: usize,
        user_sp: usize,
        kernel_stack_top: *mut u8,
    );
}
