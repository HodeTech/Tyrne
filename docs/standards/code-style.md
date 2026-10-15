# Code style

This standard defines how Rust source code is written in the Tyrne repository. It applies to every `.rs` file in the kernel, the HAL, userspace services, tests, and build tooling.

For documentation (`.md`) style, see [documentation-style.md](documentation-style.md). For `unsafe` blocks specifically, see [unsafe-policy.md](unsafe-policy.md) — the rules there take precedence over anything in this document when they overlap.

## Scope and goals

The goals of this standard are:

1. **Consistency** — a reader (human or AI) should not spend mental budget on style questions.
2. **Reviewability** — diffs should reflect intentional changes, not formatter churn or import reordering.
3. **Safety** — conventions that reduce the chance of silently introducing UB, panics on hot paths, or implicit allocations in kernel space.

## Toolchain

- **MSRV (Minimum Supported Rust Version):** the pinned nightly in `rust-toolchain.toml`. There is no stable-Rust fallback — the kernel uses nightly features (inline asm stabilized, but certain intrinsics and lang items still require it).
- **Edition:** `2021` (or current default when the workspace is created).
- **Formatter:** `rustfmt`. The project's `rustfmt.toml` is the source of truth; do not override per-file.
- **Linter:** `clippy` with the project's `clippy.toml`. All warnings are errors in CI.

## Formatting

- Run `cargo fmt --all` before every commit. CI rejects unformatted code.
- Do not add `// rustfmt::skip` unless a specific readability justification is in a comment on the same line. Review will reject silent skips.
- Line length: rustfmt default (100). Long URL / literal strings may exceed; use `// rustfmt::skip` with justification if needed.
- Imports are grouped by rustfmt:
  1. Standard (if any — rare in `no_std`).
  2. External crates.
  3. Internal crates (`crate::`, `self::`, `super::`).

## Naming

| Kind | Convention | Example |
|------|-----------|---------|
| Crate | `snake_case` | `tyrne_kernel` |
| Module | `snake_case` | `ipc::endpoint` |
| Type (struct, enum, trait, union) | `PascalCase` | `Capability`, `ThreadId` |
| Trait | `PascalCase`, usually an adjective or a role | `Schedulable`, `MmioRegion` |
| Enum variant | `PascalCase` | `MessageKind::Notify` |
| Function, method | `snake_case` | `send_message` |
| Macro | `snake_case!` for function-style, `PascalCase` for derive | `log!`, `derive(Capability)` |
| Constant, static | `SCREAMING_SNAKE_CASE` | `MAX_CAPABILITIES` |
| Lifetime | short, meaningful | `'kernel`, `'msg`, `'tls`; avoid `'a`, `'b` when context is ambiguous |
| Generic type | single uppercase when unconstrained, meaningful when bounded | `T`, `M: Message` |

Unforgeable capability types should be named with a `Cap` suffix when the bearer aspect is significant: `SendCap`, `EndpointCap`, `MemoryRegionCap`.

## Module organization

- Prefer **one concept per module**. A file that defines both scheduling and IPC should be split.
- Use **directory modules with `mod.rs`** for anything with submodules. Do *not* use the legacy per-file-with-same-name convention (`foo.rs` + `foo/bar.rs`); it makes grep less useful. *Exception:* single-file modules stay as `foo.rs`.
- **Internal-only items are `pub(crate)`** unless they genuinely need to leak further. `pub` on a kernel-internal item is a bug.
- **Re-exports** are allowed at the crate root and at clear boundary modules. Do not re-export for the sake of shortening paths in tests.

## Documentation comments

- Every `pub` and `pub(crate)` item has a doc-comment. The workspace level is `missing_docs = "warn"` in `Cargo.toml` `[workspace.lints.rust]`; required Clippy commands pass `-D warnings`, so emitted missing-doc warnings fail those covered targets unless explicitly allowed in source. The lint does not cover every internal `pub(crate)` item; review still enforces this documentation rule. No workspace lint-level change is implied.
- Doc-comments follow the standard Rust shape:
  - First line is a **one-sentence summary**.
  - Blank line.
  - Optional paragraphs of elaboration.
  - `# Safety` section is **required** for every `unsafe fn`. See [unsafe-policy.md](unsafe-policy.md).
  - `# Errors` section lists the error conditions of any `fn -> Result<_, _>`.
  - `# Panics` section lists panic conditions (ideally, there are none — see [error-handling.md](error-handling.md)).
  - `# Examples` are encouraged for public userspace APIs, optional for kernel-internal APIs.

Example:

```rust
/// Sends a message on this endpoint, blocking until a receiver rendezvouses.
///
/// The message's capability slot is consumed by this call. If the caller needs
/// to retain a copy, they must duplicate the capability first.
///
/// # Errors
///
/// - [`IpcError::NoReceiver`] if the endpoint has no waiting receiver and
///   the caller is in non-blocking mode.
/// - [`IpcError::CapsExhausted`] if the receiver's capability table is full.
///
/// # Panics
///
/// Does not panic.
pub fn send(&self, msg: Message) -> Result<(), IpcError> { /* ... */ }
```

## Module-local conventions

- **Error types:** each module defines a module-local `Error` enum (or reuses a closer parent's). Boundary layers (`syscall`, `driver`) convert between their neighbors' errors. See [error-handling.md](error-handling.md).
- **Result type aliases:** a module may define `pub type Result<T> = core::result::Result<T, Error>;` at the top for brevity.
- **Constants** live near their first use unless they are a cross-module contract (in which case they go in a `consts` module or a top-level config).

## `no_std` discipline

- Kernel and HAL crates are `#![no_std]`. Do not depend, transitively or directly, on anything that pulls `std`.
- Heap allocation is **not** available in the kernel by default. When the allocator is added (see the allocator ADR, to be written when the allocator is introduced — no existing ADR covers it), it will be a distinct crate and kernel code will opt in explicitly.
- No `println!`, `print!`, `eprintln!`. Current kernel diagnostics use the raw HAL `Console` / BSP UART path. The structured logging facade and service are planned, not available APIs; see [logging-and-observability.md](logging-and-observability.md).

## Capability type conventions

Capabilities are first-class types in Tyrne's design:

- Capabilities are **move-only** (implement neither `Copy` nor `Clone` unless an explicit duplication operation is intended).
- Duplicating a capability requires calling an explicit `duplicate()` method that itself consumes a `DuplicateCap` authority.
- Capabilities should not leak through `Debug` or `Display` in ways that reveal unforgeable token bits. `Debug` should print a type name and object ID, not the raw token.

## `unsafe`

See [unsafe-policy.md](unsafe-policy.md). Summary: every `unsafe` block and every `unsafe fn` has a `// SAFETY:` comment with (a) invariants upheld, (b) why safer alternatives were rejected, and (c) a reference to the audit entry.

## Panics in kernel code

- Kernel code **must not** panic on the hot path. See [error-handling.md](error-handling.md).
- `unwrap()` / `expect()` are forbidden in kernel source outside of `init` paths that run once at boot.
- `todo!()` is denied by workspace Clippy and must be resolved before landing. `unimplemented!()` has no automated deny: review rejects incomplete reachable runtime paths and requires an explanation for unreachable branches. Intentional non-bare-metal user-library host stubs are a documented exception; see [error-handling.md](error-handling.md#10-todo-and-unimplemented-are-transient-markers).

## Lints

The root `Cargo.toml` `[workspace.lints.*]` tables are authoritative for inherited levels; every workspace member opts in. All current workspace entries are listed below, followed by additional crate attributes in kernel/HAL libraries and the BSP entry point:

- `unsafe_op_in_unsafe_fn` (deny, workspace)
- `missing_docs` (warn, workspace — required Clippy `-D warnings` escalates emitted warnings; see the documentation-comments section above)
- `unreachable_pub` (warn, workspace)
- `unused_must_use` (deny, workspace)
- `clippy::pedantic` (warn, priority -1, workspace; required Clippy `-D warnings` escalates emitted warnings, with justified scoped allowances)
- `clippy::alloc_instead_of_core` (deny, workspace)
- `clippy::undocumented_unsafe_blocks`, `clippy::missing_safety_doc` (deny, workspace)
- `clippy::todo` (deny, workspace: unfinished implementation markers must not land)
- `clippy::arithmetic_side_effects` (deny in kernel; explicit wrapping math required)
- `clippy::float_arithmetic` (deny in kernel)
- `clippy::panic`, `clippy::unwrap_used`, `clippy::expect_used` (deny in `tyrne-kernel`, `tyrne-hal` and `tyrne-bsp-qemu-virt`, with explicit boot/demo, fatal-handler and test allowances; not inherited as denies by test-hal/userland)

Lint **levels** are configured in `Cargo.toml` `[workspace.lints.clippy]` / `[workspace.lints.rust]` and per-crate attributes (`kernel/src/lib.rs`, `hal/src/lib.rs`, `bsp-qemu-virt/src/main.rs`), including explicit scoped allowances. `clippy.toml` holds only numeric thresholds (e.g. `avoid-breaking-exported-api`), not lint levels — do not look there for the authoritative list.

## Tooling

| Tool | Purpose | Where |
|------|---------|-------|
| `rustfmt` | Formatter | `cargo fmt` |
| `clippy` | Required linter | `cargo host-clippy`; bare-metal `cargo kernel-clippy` after `tools/build-userland.sh`, plus explicit userland/release commands in [infrastructure.md](infrastructure.md) |
| `miri` | Required UB detector | Pinned-toolchain workspace command excluding the BSP; see [infrastructure.md](infrastructure.md#miri-as-a-blocking-gate) |
| `cargo-geiger` | `unsafe` accounting | Periodic audit |
| `cargo-audit` | Known vulnerabilities | Planned CI gate when the first external dependency lands; see [infrastructure.md](infrastructure.md#planned-gates-not-yet-enforced) |
| `cargo-vet` | Dependency auditing | Planned under the same first-external-dependency condition |

## Enforcement

- **Author:** runs `cargo fmt --all`, `cargo host-clippy` and `cargo host-test` locally; build matching userland before bare-metal kernel build/clippy/smoke when applicable. Use the target-aware commands in [infrastructure.md](infrastructure.md).
- **Reviewer:** does not comment on issues the tools catch; those are CI's job. Reviewer focuses on design, correctness, and capability semantics.
- **CI:** fails the build on any formatter, clippy, or test failure.

## References

- Rust API Guidelines: https://rust-lang.github.io/api-guidelines/
- Embedded Rust Book: https://docs.rust-embedded.org/book/
- Clippy lints: https://rust-lang.github.io/rust-clippy/
- Hubris code style (prior art): https://hubris.oxide.computer/
