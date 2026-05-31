# T-024 — `task_create_from_image`: `LoadedImage` → runnable `CapObject::Task` capability

- **Phase:** B
- **Milestone:** B6 — First userspace "hello" (step 3 of the [B6 opening sequence](../../../roadmap/phases/phase-b.md#b6-opening-sequence--prerequisites); the deferred [B4 §3](../../../roadmap/phases/phase-b.md#milestone-b4--task-loader) bridge)
- **Status:** In Review (implemented + all gates green incl. Miri; security-relevant — awaiting the explicit security review per Definition of done)
- **Created:** 2026-05-31
- **Author:** @cemililik (+ Claude Opus 4.8 agent)
- **Dependencies:** [T-019](T-019-task-loader.md) (`load_image` → `LoadedImage`, which this consumes); [T-023](T-023-el0-entry-context.md) / [ADR-0037](../../../decisions/0037-el0-entry-context.md) (the EL0 context + `add_user_task` the wire-up later feeds with `entry_va`/`stack_top_va`); [ADR-0028](../../../decisions/0028-address-space-data-structure.md) (the `CapKind::AddressSpace` cap this resolves); [ADR-0016](../../../decisions/0016-kernel-object-storage.md) (the `Task` arena + cap model); [ADR-0014](../../../decisions/0014-capability-representation.md) (capabilities).
- **Informs:** Unblocks the B6 wire-up — a real EL0 task is created from the embedded image via this bridge, then run via `add_user_task` once the security-critical **gate #1** (per-task user-VA→kernel-VA translation) + **gate #3** (current-task capability table) close. Does **not** itself run the task.
- **ADRs required:** **None.** This composes already-Accepted decisions (ADR-0029 loader + ADR-0028 AS-cap + ADR-0016 kernel-object/arena + ADR-0037 EL0 context). The one micro-decision — the **Task cap is kind-only** — follows the established `CapKind::AddressSpace` v1 pattern (see §Approach); no per-operation Task right is introduced, so no new ADR. Introduces **no new `unsafe`** (entirely safe cap/arena composition).

---

## User story

As the kernel, I want a `task_create_from_image` bridge that turns a [`LoadedImage`](../../../../kernel/src/obj/task_loader.rs) into a runnable `CapHandle{CapObject::Task(...)}` — minting a `Task` kernel object bound to the loaded address space and a capability that names it — so that the B6 wire-up can schedule a real EL0 task (via `add_user_task` with the image's entry/stack), **without** the loader or the wrapper having to know the EL0 register mechanics.

## Context

[T-019](T-019-task-loader.md) delivered the loader half ([`LoadedImage`](../../../../kernel/src/obj/task_loader.rs) = `{ as_cap, entry_va, stack_top_va, image_bytes, stack_bytes }`) but explicitly **does not** mint a runnable task. [T-023](T-023-el0-entry-context.md) delivered the EL0 entry mechanism (`init_user_context` + `enter_el0` + `add_user_task`). T-024 is the **bridge** ([phase-b §B6 step 3](../../../roadmap/phases/phase-b.md#milestone-b6--first-userspace-hello)): `LoadedImage` → `CapHandle{CapObject::Task(...)}`. It **mints, does not run** — running is the wire-up's job, gated behind the remaining T-021 carry-forward gates.

The EL0 entry context (`entry_va`/`stack_top_va`) is **not** stored on the `Task` object (per [ADR-0037 §D2](../../../decisions/0037-el0-entry-context.md) — the `Task` stays `id + address_space_handle`); the wire-up passes those straight from the retained `LoadedImage` to `add_user_task`. So `task_create_from_image` reads only `loaded.as_cap`.

## Acceptance criteria

- [x] **`task_create_from_image`** ([`kernel/src/obj/task_loader.rs`](../../../../kernel/src/obj/task_loader.rs)): `fn(loaded: &LoadedImage, table: &mut CapabilityTable, task_arena: &mut TaskArena, id: u32, task_rights: CapRights) -> Result<CapHandle, TaskCreateError>`. Steps: (1) resolve `loaded.as_cap` → `AddressSpaceHandle` (lookup + `CapKind::AddressSpace` kind-check); (2) `create_task(arena, Task::new(id, ash))`; (3) `Capability::new(task_rights, CapObject::Task(handle))` → `insert_root`.
- [x] **Rollback:** if step 3's `insert_root` fails (`CapsExhausted`), the step-2 task object is rolled back via `destroy_task` so a full cap-table leaves no orphaned arena slot. Pinned by a host test.
- [x] **`TaskCreateError`** taxonomy (`#[non_exhaustive]`): `InvalidAddressSpaceCap(CapError)` (stale / wrong-kind `as_cap`), `TaskArenaFull`, `CapTableExhausted(CapError)`. Re-exported from `crate::obj`.
- [x] **Kind-only Task cap.** The minted `CapKind::Task` cap carries `task_rights` governing only *cap management*; no Task-*operation* right exists in v1 (mirrors the `CapKind::AddressSpace` kind-only model). Documented on the fn.
- [x] **Host tests:** mint-success + AS-binding + id (`task_create_from_image_mints_task_cap_bound_to_the_loaded_as`); wrong-kind `as_cap` rejection; stale `as_cap` rejection; rollback-on-cap-table-exhausted (slot 0 reused → no leak).
- [x] **All gates green:** **347 host tests** (+4); host + kernel clippy `-D warnings`; `cargo fmt --check`; kernel build (the BSP links the kernel lib); `cargo +nightly miri test --workspace --exclude tyrne-bsp-qemu-virt` (0 UB). **QEMU smoke** byte-stable + fault-clean — `task_create_from_image` is **dormant** (no BSP caller yet), so the trace matches the post-T-023 baseline; the runtime exercise is the B6 wire-up.

## Out of scope

- **Running / scheduling** the created task — the B6 wire-up (calls `add_user_task` with the `LoadedImage`'s entry/stack; not before gate #1/#3).
- **Seeding the EL0 task's own capability table** with initial caps (e.g. the debug-console cap) — that is T-021 **gate #3** (`SYSCALL_STUB_TABLE` → current-task table) / the wire-up.
- **gate #1** (per-task `console_write` window + per-page user-VA→kernel-VA translation) — separate B6 task.
- **`tyrne-user` + `userland/hello` + the build pipeline** — separate B6 task.
- **Per-operation Task rights** (run / suspend / kill authority) — deferred to a later ADR (v1 Task cap is kind-only).

## Approach

Compose the already-built pieces with `load_image`'s preflight→rollback discipline. The AS-cap resolution mirrors the private `resolve_address_space_cap` (lookup + `CapObject::AddressSpace(h)` match) but maps failures into `TaskCreateError`. The Task cap is installed as a **root** cap (`insert_root`) — there is no parent Task cap to derive from, matching the demo's endpoint-cap pattern. **Kind-only rights:** v1 has no Task-operation right (the `CapKind` names/authorizes the task object, exactly as `CapKind::AddressSpace` grants AS authority); `task_rights` only govern duplicate/derive/transfer/revoke of the Task cap. No new `unsafe`.

## Definition of done

All acceptance criteria checked; gates green (incl. Miri); `current.md` updated; **security-relevant — flagged for explicit security review** (cap minting + AS-cap resolution + rollback are capability-model surface). No `unsafe` introduced, so no audit-log entry.

## Review history

- **2026-05-31 — surface verified, then implemented (→ In Review)** on branch `t-024-task-create-from-image` (off `main` at the merged T-023 PR #37, `eb3125f`). Before coding, the exact surface was verified against the live tree (no assumptions): `LoadedImage` shape; `CapObject::Task`/`CapKind::Task` exist; `Capability::new` + `insert_root` (→ `CapError::CapsExhausted` on full); `create_task`/`destroy_task`; the `resolve_address_space_cap` kind-only pattern; `CapRights` has no Task-specific bit. **No ADR needed** — composes ADR-0029/0028/0016/0037; Task cap kind-only per the AS-cap pattern. Implementation: `task_create_from_image` + `TaskCreateError` + 4 host tests, all gates green (347 host tests, fmt, host+kernel clippy `-D warnings`, kernel build, byte-stable fault-clean QEMU smoke — dormant, Miri 0 UB).
- **2026-05-31 — adversarial multi-agent review (4 lenses × per-finding verification): 6 findings, all confirmed Low/Nit, no code/security/correctness defect.** The borrow scoping, rollback, error mapping, kind-only model, and the 4 host tests were verified **correct**. **Fixed:** `obj/mod.rs` module-doc (was stale — omitted the T-024 surface and claimed the loader does *not* mint a Task cap; CC-001, Low); `current.md` stale "Next to open: task_create_from_image" line (superseded by the T-024 lead's own "Next:"; DOC-1, Low); the rustdoc redundant `[cap_map][crate::mm::cap_map]` link target (DOC-2, Nit); a comment pinning that `create_task` only returns `ArenaFull` so the `map_err(|_|…)` is exhaustive-by-contract (T024-C-N1, Nit). **Deferred (tracked, no code change):**
  - **SEC-T024-01 (Nit, defer)** — the minted Task cap stores an `AddressSpaceHandle` whose liveness is **not** coupled to the AS cap; if a later milestone drops/reuses an AS while a bound Task is live, the Task could activate a stale/reused handle (a confused-deputy / use-after-free class). **Dormant + out of scope** (T-024 mints, does not schedule) and inherited from v1's documented object-lifecycle gap ([ADR-0016](../../../decisions/0016-kernel-object-storage.md); the `references_object` check `destroy_task` defers). **Carry-forward precondition for the B6 wire-up / the successor lifecycle ADR:** before a real EL0 task runs, a Task must not be able to outlive (or alias a reused slot of) its bound AS — either the wire-up keeps the AS cap live for the task's lifetime, or AS-destroy checks `references_object` across the task arena.
  - **CC-002 (Nit, defer)** — the inline AS-cap lookup+kind-match duplicates the module-private `resolve_address_space_cap` (mm). Reuse is not cleanly available (it returns `AddressSpaceError`, not `CapError`; widening + lossy unwrapping). Justified for now (documented "mirroring…" comment); if a 3rd kind-only resolver appears, hoist a generic `CapabilityTable::lookup_kind(handle, CapKind) -> Result<CapObject, CapError>` and route all sites (cap_create_address_space / cap_map / cap_unmap / here) through it.
