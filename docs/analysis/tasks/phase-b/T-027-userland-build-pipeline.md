# T-027 — `userland/hello` + `tyrne-user` + the raw-flat build pipeline (B6 step 5)

- **Phase:** B
- **Milestone:** B6 — First userspace "hello" (step 5 of the [B6 dependency-ordered sequence](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello) — `tyrne-user` crate + `userland/hello/` crate + the `cargo build → rust-objcopy -O binary → include_bytes!` pipeline + the shared base-VA source-of-truth)
- **Status:** Draft (opened in the [ADR-0039](../../../decisions/0039-userland-build-pipeline.md) Propose commit per [ADR-0025 §Rule 1](../../../decisions/0025-adr-governance-amendments.md); implementation follows ADR-0039 Accept)
- **Created:** 2026-05-31
- **Author:** @cemililik (+ Claude Opus 4.8 agent)
- **Dependencies:** [ADR-0039](../../../decisions/0039-userland-build-pipeline.md) (the build-pipeline orchestration this implements); [ADR-0029](../../../decisions/0029-initial-userspace-image-format.md) (the raw-flat format — entry at offset 0, image `USER|EXECUTE`); [ADR-0006](../../../decisions/0006-workspace-layout.md) (the workspace-member / `tyrne-` naming conventions); [ADR-0031](../../../decisions/0031-initial-syscall-set.md) + [ADR-0030](../../../decisions/0030-syscall-abi.md) (the syscall ABI the `tyrne-user` wrappers + the SVC sequence target); [T-019](T-019-task-loader.md) (the loader that maps this image; pins `USERSPACE_IMAGE_BASE_VA`).
- **Informs:** Produces the real userspace image (replacing the hand-coded `USERSPACE_IMAGE` placeholder) so [T-028](T-028-el0-userspace-wireup.md) can load + run it in EL0. Does **not** itself run a task — the image is embedded but dormant until T-028.
- **ADRs required:** [ADR-0039](../../../decisions/0039-userland-build-pipeline.md) (must be Accepted before implementation). No new `unsafe` in the kernel; the only kernel-side change is the `include_bytes!` source of `USERSPACE_IMAGE` (data, not code).

---

## User story

As a kernel developer, I want a **real** userspace program compiled from Rust source — not a hand-coded byte literal — embedded into the kernel image through a reproducible, auditable pipeline, so that B6's first EL0 task is a maintainable program (greeting + clean exit) and every future userspace program follows the same shape.

## Context

ADR-0029 chose the raw-flat image format and deferred the build orchestration to B6; ADR-0039 settles that orchestration (a `tools/build-userland.sh` step + `rust-objcopy` from the pinned `llvm-tools-preview` + `include_bytes!` of a git-ignored `.bin`, with the userland crates as `default-members`-excluded workspace members). T-027 implements it. The current `USERSPACE_IMAGE` ([`bsp-qemu-virt/src/main.rs`](../../../../bsp-qemu-virt/src/main.rs)) is the placeholder `mov w0, #42; ret`; T-027 replaces it with the objcopy output of a `userland/hello` crate that, when run (T-028), will `console_write` a greeting and `task_exit`.

## Acceptance criteria

- [ ] **`tyrne-user` crate** (`userland/` or workspace root, package `tyrne-user`, `#![no_std]`): safe wrappers over the [ADR-0031](../../../decisions/0031-initial-syscall-set.md) syscalls needed by `hello` — at minimum `console_write(cap: CapWord, buf: &[u8]) -> Result<usize, …>` and `task_exit(code) -> !` — each a thin `svc #0` inline-asm shim packing the ABI ([ADR-0030](../../../decisions/0030-syscall-abi.md): `x8` = number, `x0..x5` = args; `ConsoleWrite = 5`, `TaskExit = 4`). No dependency on kernel internals (the ABI constants are restated/owned userspace-side or shared via a leaf crate).
- [ ] **`userland/hello` crate** (package `tyrne-userland-hello`, `#![no_std] #![no_main]`): a `_start` entry placed at **offset 0** of the linked image (linker `ENTRY` + a `KEEP`'d first section) that calls `tyrne_user::console_write` with a greeting string (living in the image's read-only data — reachable as a `USER` page, [T-025](T-025-user-access-translation.md) gate #1 requires only the `USER` flag for a read) then `tyrne_user::task_exit(0)`; a minimal `#[panic_handler]` that `task_exit`s or loops (no unwinder — `panic=abort` inherited).
- [ ] **Userland linker script** places `.text` (entry first) + `.rodata` contiguously at `USERSPACE_IMAGE_BASE_VA`, **no `.data`/`.bss`** (writable globals would fault — image is `USER|EXECUTE`, no `WRITE`), 16-byte aligned; produces a contiguous byte stream with no ELF artifacts under `rust-objcopy -O binary`.
- [ ] **Base-VA source-of-truth:** a single Rust-side `pub const USERSPACE_IMAGE_BASE_VA = 0x0080_0000` (read by the BSP loader call site); the userland linker script restates the literal with a documented `keep-in-sync-with` comment (LD cannot import a Rust const — per [ADR-0039](../../../decisions/0039-userland-build-pipeline.md)).
- [ ] **Build orchestration** ([`tools/build-userland.sh`](../../../../tools/build-userland.sh)): `cargo build -p tyrne-userland-hello --target aarch64-unknown-none` (release + debug as the kernel profile dictates) → `rust-objcopy -O binary` (resolved from the active toolchain's `llvm-tools` — **no Cargo dependency**, K3-8 unfired) → a git-ignored `.bin` at a stable path. Clear error if `llvm-tools` / the ELF is missing. `.gitignore` updated.
- [ ] **Workspace integration:** `userland/hello` + `tyrne-user` added to `members`, **excluded from `default-members`** (host commands skip them — mirrors `bsp-qemu-virt`); `cargo host-test` / `cargo build` / `cargo host-clippy` unaffected (verified).
- [ ] **BSP embed:** `USERSPACE_IMAGE` becomes `include_bytes!(<path-to-hello.bin>)`; [`bsp-qemu-virt/build.rs`](../../../../bsp-qemu-virt/build.rs) gains `rerun-if-changed` on the `.bin` and a `panic!` naming `tools/build-userland.sh` if it is absent.
- [ ] **`tools/smoke.sh` runs the userland build first** so the canonical smoke + CI path is unchanged (still one entry point).
- [ ] **Disassembly verification:** the objcopy'd `.bin` round-trips — a host test (or a documented `rust-objdump -d` check in the task's review-history) confirms offset 0 is the entry instruction and the SVC sequence + greeting match `hello`'s source. (The image is **not run** in T-027 — running is T-028.)
- [ ] **All gates green:** `cargo fmt --all --check`; host + kernel clippy `-D warnings`; host tests unchanged + green; `cargo kernel-build`; `tools/smoke.sh` PASS — the embedded real image loads via the existing loader smoke (maps `USER|EXECUTE` image + `USER|WRITE` stack, `LoadedImage` metadata printed), **byte-stable boot otherwise**, zero new fault class. Miri unaffected (no kernel logic change).

## Out of scope

- **Running the image in EL0 / the `+0x400` round-trip / `task_create_from_image` + `add_user_task` wiring** — [T-028](T-028-el0-userspace-wireup.md).
- **Seeding the task's capability table with a `DebugConsole` cap** — T-028 (the `hello` source hard-codes the *handle value* it will use; minting + inserting the cap is the wire-up's job).
- **Per-section permissions (RX `.text` / R `.rodata` / RW `.data`)** — the future ADR-0034 placeholder; v1 `hello` is code + read-only data only.
- **`cargo xtask` multi-binary orchestration** — the named B7+ upgrade ([ADR-0039](../../../decisions/0039-userland-build-pipeline.md)); v1 uses the shell script.

## Approach

Per [ADR-0039](../../../decisions/0039-userland-build-pipeline.md) §Decision outcome: two `default-members`-excluded crates (`tyrne-user` lib + `userland/hello` bin) targeting `aarch64-unknown-none`; a minimal userland linker script fixing the entry at `USERSPACE_IMAGE_BASE_VA` offset 0; `tools/build-userland.sh` driving `cargo build` + `rust-objcopy -O binary` (llvm-tools, no Cargo dep) to a git-ignored `.bin`; the BSP `build.rs` embedding it via `include_bytes!` with a `rerun-if-changed` + missing-file panic; `tools/smoke.sh` chaining the script. The hello program is deliberately tiny (greeting + `task_exit`) so the v1 no-`.data` constraint is non-binding. Verification is by disassembly + the existing loader smoke (the image maps cleanly); **execution is deferred to T-028**, mirroring how T-023's EL0-entry mechanism landed dormant before its wire-up.

## Definition of done

All acceptance criteria checked; gates green; the embedded real image replaces the placeholder and loads cleanly under `tools/smoke.sh` (dormant — not run); `current.md` + [phase-b.md §B6 step 5](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello) updated. Lands **after** [ADR-0039](../../../decisions/0039-userland-build-pipeline.md) is Accepted. The EL0 wire-up + the explicit EL0-boundary security review are [T-028](T-028-el0-userspace-wireup.md).

## Review history

- **2026-05-31 — opened Draft** in the [ADR-0039](../../../decisions/0039-userland-build-pipeline.md) Propose commit (the ADR's dependency chain names it — step 5; [ADR-0025 §Rule 1](../../../decisions/0025-adr-governance-amendments.md)). Implementation follows the ADR Accept.
