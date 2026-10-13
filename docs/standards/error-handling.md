# Error handling

How Tyrne code reports, propagates, and recovers from failures. The design rules cover kernel code, HAL and userspace services, with explicit carve-outs for kernel panics, init paths and ISRs. Enforcement differs by crate: the kernel, HAL and QEMU BSP carry panic-family deny attributes with scoped allowances; test-hal and userland inherit only the workspace-level lint configuration. Planned task supervision is distinguished from current runtime behavior below.

## Scope and goals

- Make the **failure model explicit** at every boundary.
- Make the **happy path obvious** and the error path auditable.
- Keep the kernel from crashing on recoverable conditions.
- Keep userspace driver faults out of the kernel.

## Rules

### 1. `Result<T, E>` is the default

Any operation that can fail for reasons outside the caller's invariants returns `Result<T, E>`, not `Option<T>`, and not a sentinel value.

Use `Option<T>` only for *genuine* absence (lookup that may legitimately return nothing). Failure is a `Result`, not a `None`.

### 2. Per-module error enums

Each module that can fail defines a local `Error` enum that captures the distinct failure modes callers might want to discriminate. Use `#[non_exhaustive]` so adding a variant in a future change is backward-compatible.

```rust
#[non_exhaustive]
#[derive(Debug, Copy, Clone, Eq, PartialEq)]
pub enum IpcError {
    /// The target endpoint has no waiting receiver and the call was non-blocking.
    NoReceiver,
    /// The receiving task's capability table is full.
    CapsExhausted,
    /// The sending task does not hold a send capability for this endpoint.
    NotAuthorized,
    /// The message payload exceeds the configured per-endpoint size.
    PayloadTooLarge,
}
```

`thiserror` is not used in `no_std` kernel code; derive `Debug` by hand or write a short `Display` impl only where needed.

### 3. Convert at boundaries, do not forward

Modules must not leak their own error types across public boundaries unless the boundary is specifically designed for that type. When calling a lower module and bubbling the error up, convert it at the boundary:

```rust
pub fn syscall_send(/* ... */) -> Result<(), SyscallError> {
    ipc::send(endpoint, msg).map_err(SyscallError::from)
}
```

The `From` impl makes the conversion explicit and localized. Downstream callers see one error type per layer, not a leaking hierarchy.

### 4. No `unwrap` / `expect` on hot paths

In the kernel, HAL and QEMU BSP, `unwrap()` and `expect()` are forbidden outside of explicitly scoped exceptions:

- **One-shot `init` paths.** Code that runs once at boot, before any user-controllable input has been accepted, may use `expect()` with a message that describes the invariant being asserted.
- **Test-only code.** Unit and integration tests may `unwrap()` freely.

**Required:** `clippy::unwrap_used`, `clippy::expect_used` and `clippy::panic` are denied in `tyrne-kernel`, `tyrne-hal` and `tyrne-bsp-qemu-virt`. Source-local allowances cover the relevant boot/demo, fatal-handler and test paths; they are not a general runtime escape. `tyrne-test-hal`, `tyrne-user` and `tyrne-userland-hello` inherit workspace lints without those crate-level denies. See [code-style.md](code-style.md#lints) and [infrastructure.md](infrastructure.md#required-gates-enforced-by-the-current-branch-protection) for configuration and target coverage.

### 5. `panic!` is an assertion, not error handling

`panic!` is reserved for situations where the program has detected a broken invariant that makes continuing undefined or unsafe. It is not a substitute for returning a `Result`.

Examples of legitimate panics (in invariant-checking paths):

- The bootloader handed us an invalid memory map.
- An impossible discriminant appeared in a match because the caller violated `Safety`.

Current behavior and future BSP policy are separate:

- **Current QEMU BSP:** the panic handler prints `!! tyrne panic !!` and formatted `PanicInfo` (message and available source location) to UART, then spins. It does not dump the general-purpose register frame or provide a backtrace, reset or diagnostic shell. Exception handlers can include saved exception class/ESR and interrupt identifiers in a panic message; those diagnostics are not a generic panic-time register dump. Required QEMU smoke rejects a panic marker.
- **Planned real-hardware policy:** supervised reset or a capability-controlled diagnostic shell requires a board-specific implementation and decision; neither exists in the current QEMU BSP.

The current `hello` userspace panic handler explicitly calls `task_exit(101)`. This does not implement general userspace fault isolation: an unexpected non-SVC EL0 synchronous exception still reaches the BSP's whole-kernel panic path. No supervisor notification or resource reclamation is delivered (see §8).

### 6. Return errors, do not log-and-return

A function that returns a `Result` does not also log the error. Logging is the caller's decision, because only the caller knows whether the error is expected and how it should be surfaced.

Bad:

```rust
fn open(&self, name: &str) -> Result<Handle, FsError> {
    let h = self.lookup(name).map_err(|e| {
        log::error!("failed to open {}: {}", name, e);   // do not do this
        e
    })?;
    Ok(h)
}
```

Good: return the error; let the caller decide whether `error!`, `warn!`, or silent retry is right.

### 7. Preserve root cause through the stack

When converting between layers, preserve root-cause information. In `no_std`, `thiserror` and boxed errors are unavailable; encode root cause as an enum variant that carries a smaller `Error` from the layer below:

```rust
#[non_exhaustive]
pub enum SyscallError {
    NotAuthorized,
    Ipc(IpcError),
    Memory(MemoryError),
}

impl From<IpcError> for SyscallError {
    fn from(e: IpcError) -> Self {
        Self::Ipc(e)
    }
}
```

Do not swallow. Do not collapse distinct IPC failures into a generic "internal error."

### 8. Userspace task faults are kernel-visible errors

**Planned:** task fault delivery and supervision belong to [Phase E](../roadmap/phases/phase-e.md), including E3's service-manager/supervisor Fault-endpoint plumbing. The intended model suspends a faulting task, encodes a `TaskFault` message and delivers it to a supervisor endpoint; the supervisor chooses restart, termination or logging policy. This is a target design, not the current fault-handler contract.

**Current:** unexpected non-SVC EL0 synchronous faults panic the kernel. Explicit `task_exit` removes the running task from scheduling but retains its Task, address space, capability-table and frame state; it neither sends `TaskFault` nor reclaims these resources. The `hello` panic handler's explicit exit is one application's behavior. See the [security model](../architecture/security-model.md) for the implemented syscall-input boundary and retained-state limitations.

### 9. Interrupt service routines minimize error paths

ISRs run with restricted state. Inside an ISR:

- **Do not allocate.** No heap, no growable structures.
- **Do not log with blocking facilities.** A trace buffer or lock-free ring is the intended deferred transport; neither exists today. Do not assume that the current raw UART path is a nonblocking ISR logger. See the planned [logging and observability](logging-and-observability.md#context-rules) design.
- **Do not return `Result` that the ISR entry cannot handle.** An ISR either fully handles the event or marks a deferred work item for a task-context handler. An error inside an ISR is an assertion failure and should be a `panic!` in debug builds, or a quiet hardware-fault counter bump in release builds (with an entry in the audit log explaining why).

### 10. `todo!()` and `unimplemented!()` are transient markers

- `todo!()` is a transient development marker and must be resolved before the feature lands. **Required:** the workspace sets `clippy::todo = "deny"`; required Clippy commands cover the configured host and bare-metal targets. A cfg-disabled branch is not proof of completeness or lint coverage for every configuration.
- `unimplemented!()` has **no automated deny lint** today. Review must reject incomplete reachable runtime paths; a genuinely unreachable branch requires an explicit explanation.
- Intentional non-bare-metal stubs in `userland/tyrne-user` permit host workspace compilation without executing the bare-metal syscall shim. These are documented target stubs, not unfinished runtime features; preserve them. Review distinguishes these from missing feature implementations. See [infrastructure.md](infrastructure.md#required-gates-enforced-by-the-current-branch-protection) for actual Clippy coverage.

## Panic strategy

The workspace sets `panic = "abort"` in `Cargo.toml` for kernel crates. Unwinding in kernel mode across a context switch boundary is undefined behavior without substantial runtime support, which we are not adding. `abort` is a hard stop that the kernel panic handler intercepts.

Userspace task crates may differ in later phases; that will be revisited in an ADR.

## Error-type design checklist

When introducing a new `Error` enum, ask:

- Does each variant represent a **distinct case a caller could handle differently**? If two variants always get the same treatment, merge them.
- Is the enum `#[non_exhaustive]`? It should be.
- Does it derive `Debug`, `Copy`, `Clone`, `Eq`, `PartialEq`? (Skip `Copy` if any variant carries non-`Copy` payload.)
- Does the enum's name include the subsystem, so `use`d names remain clear? (`IpcError`, not just `Error`.)
- Is there a `From` impl for every error type that should compose into this one?

## Anti-patterns to reject

- `.unwrap()` in kernel code outside init.
- `panic!` used as a shortcut for "return an error up there somewhere."
- Single monolithic `Error` enum that aggregates every subsystem's failures.
- Logging and returning the same error.
- Discarding error context by matching and re-panicking with a generic message.
- Using `bool` as a return type for "success or silent failure."

## Tooling

- **Required:** `clippy::unwrap_used`, `clippy::expect_used`, `clippy::panic` are denied by crate attributes in `tyrne-kernel`, `tyrne-hal` and `tyrne-bsp-qemu-virt`, with the scoped allowances described above. They are not workspace-wide denies.
- `clippy::result_large_err` is `warn` — error types larger than ~128 bytes bloat the `Result` return value.
- `clippy::missing_errors_doc` is `warn` — every public `fn -> Result` should document its errors.

> Both of the above are active workspace-wide through `clippy::pedantic = "warn"` (root `Cargo.toml`, `[workspace.lints.clippy]`) and clippy's default lint groups — not as standalone per-lint entries. A grep of `Cargo.toml` for the literal lint names will therefore not find them; this is expected, not a missing configuration.

## References

- Rust API Guidelines, Error types: https://rust-lang.github.io/api-guidelines/interoperability.html#error-types
- `#[non_exhaustive]` RFC: https://rust-lang.github.io/rfcs/2008-non-exhaustive.html
- Hubris task supervision / restart model (prior art): https://hubris.oxide.computer/
