# T-062 — Add linker and boot consistency checks

- **Phase:** B.2
- **Milestone:** Track B.2-4
- **Status:** Ready
- **Created:** 2026-10-11
- **Author:** Claude (AI agent), opened on behalf of @cemililik
- **Dependencies:** none
- **Informs:** [T-072](T-072-doc-comment-hygiene.md)
- **ADRs required:** none

---

## User story

As the maintainer porting the kernel to a second board, I want every constant that the linker script and the Rust code must agree on to be cross-checked at build or boot time, so that a mismatch fails loudly instead of surfacing as a cryptic translation fault.

## Context

Opened under [ADR-0040](../../../decisions/0040-phase-b2-consolidation-bridge.md). Track B.2-4 of [`phase-b2.md`](../../../roadmap/phases/phase-b2.md) lists two findings plus three related Polish items. `KERNEL_IMAGE_PHYS_BASE` is hard-coded in `bsp-qemu-virt/linker.ld` (line 41) and `KERNEL_IMAGE_START` is hard-coded again in `bsp-qemu-virt/src/main.rs` (line 102) with no cross-check, unlike its sibling `KERNEL_HH_OFFSET`, which the linker script comment says is "kept in sync by a compile-time assert" (`main.rs:145`). Separately the kernel linker script's `/DISCARD/` list (lines 115-120) has no `.got`/`.got.plt` handling although the file's header claims the design relies entirely on PC-relative addressing, whereas `userland/hello/hello.ld` already collects `.got` and asserts it empty (lines 41-48). The Polish list adds a build-time kernel-image size guard against the 128 MiB RAM window and `OUTPUT_ARCH(aarch64)` in both scripts.

## Acceptance criteria

- [ ] `linker.ld` exposes the image physical base to Rust (`PROVIDE(__kernel_image_phys_base = KERNEL_IMAGE_PHYS_BASE);`, declared `extern "C"` in the BSP), and `kernel_entry` asserts it equals `KERNEL_IMAGE_START`; or the `--defsym` upgrade path of ADR-0039 is used instead. The chosen mechanism is recorded in the review history.
- [ ] Negative test, recorded: changing only one of the two values in a scratch copy makes the boot or the build fail with a clear message, and `tools/smoke.sh --int` on the real tree still passes.
- [ ] `bsp-qemu-virt/linker.ld` collects `.got : { *(.got .got.plt) }` and asserts `SIZEOF(.got) == 0` with a message stating the kernel image must be non-PIC, mirroring `userland/hello/hello.ld` lines 41-48; both `cargo kernel-build` and the release build pass with it.
- [ ] A build-time size guard (for example `ASSERT(__bss_end - KBASE <= <mapped window>, "...")`, using the existing `__bss_end` symbol) bounds the image against the 128 MiB RAM window the PMM manages (`PMM_EXTENT_START..PMM_EXTENT_END` in `main.rs`); the limit is stated once and referenced, not re-hard-coded in a third place.
- [ ] `OUTPUT_ARCH(aarch64)` is added to `bsp-qemu-virt/linker.ld` and `userland/hello/hello.ld`; `tools/build-userland.sh` still produces a `hello.bin` with sha256 `05816ccb9be5caea862dbe3e0fc45fc2068ff06cd049f2dda3459492d0ef7d88` (or any difference is explained and recorded).
- [ ] Unchanged behaviour: `cargo kernel-build`, the release kernel build, `cargo kernel-clippy` and `tools/smoke.sh --int` pass, and the boot trace is unchanged (same lines, boot-to-end in the same band as the 2026-10-11 baseline of about 4.7 ms).

## Out of scope

- Fixing the stale `PMM_EXTENT_START` comment that mentions a non-existent linker `MEMORY` block — [T-072](T-072-doc-comment-hygiene.md) owns the comment (this task only changes the mechanism around it).
- Per-section kernel-image permissions (ADR-0034, a Phase C carry-forward).
- Any change to the userland base-VA duplication that ADR-0039 already accepts.

## Approach

Add the `PROVIDE` and the `ASSERT`s to the linker script, read the symbol in the BSP the same way other linker symbols are read, and compare it with `KERNEL_IMAGE_START` at the top of `kernel_entry` (a runtime assert is the only option: linker-script constants cannot be const-asserted against Rust constants). Mirror `hello.ld`'s `.got` section and message style. Place `OUTPUT_ARCH` next to `ENTRY`. Re-run the whole boot and the userland build and compare outputs.

## Definition of done

- [ ] `cargo fmt --all -- --check`, `cargo host-clippy`, `cargo kernel-clippy` clean.
- [ ] `cargo host-test` passes (unchanged count).
- [ ] `tools/smoke.sh --int` PASS; trace and timing recorded in the review history.
- [ ] Any new `unsafe` (reading the extern symbol) has an audit entry or an Amendment per [`unsafe-policy.md`](../../../standards/unsafe-policy.md) / [`justify-unsafe`](../../../../.agents/skills/justify-unsafe/SKILL.md); prefer a safe form (taking the symbol's address) so none is needed.
- [ ] Commit message follows [`commit-style.md`](../../../standards/commit-style.md) with `Refs: ADR-0040`.
- [ ] Task status updated to `In Review`; [`current.md`](../../../roadmap/current.md) updated.

## Design notes

- **Location re-verification (2026-10-11, HEAD `400dec0`):** `linker.ld:41` (`KERNEL_IMAGE_PHYS_BASE = 0x40080000`), `main.rs:102` (`KERNEL_IMAGE_START`), `linker.ld:115-120` (`/DISCARD/`), `hello.ld:41-48` (`.got` + ASSERT), `main.rs:145` (the existing `KERNEL_HH_OFFSET` compile-time assert) all match the tree; `__bss_end` exists (`linker.ld:105`); neither script has `OUTPUT_ARCH` today.
- **Open decisions:** runtime-assert-on-extern-symbol vs `--defsym` (ADR-0039 upgrade path; the Pi 4 port is the natural moment for `--defsym`); the exact limit for the size guard.
- Verification needs a booting kernel: until [T-034](T-034-ci-qemu-smoke-job.md) lands, run `tools/smoke.sh --int` by hand.

## Review history

| Date | Reviewer | Note |
|------|----------|------|
| 2026-10-11 | Claude (AI agent) | opened under ADR-0040; status Ready |
