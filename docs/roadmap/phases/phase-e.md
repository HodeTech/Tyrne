# Phase E — Driver model and essential services

**Exit bar:** A set of real userspace services composes into a working system — log service, service supervisor, storage driver, simple filesystem, userspace network stack — with the driver template documented so new drivers can be written consistently.

**Scope:** Establishes "userspace drivers as first-class tasks" as a working pattern, not just an architectural claim. Lands the minimum set of services any real-world deployment will need.

**Out of scope:** Specific end-user applications (Phase F); cryptographic services (Phase G); wireless (blob-dependent).

---

## Milestone E1 — Userspace driver template

A template crate and guide for writing a userspace driver task. A driver holds a `MemoryRegionCap` for its device's MMIO, an `IrqCap` for its interrupt line, and an `EndpointCap` pair for its service interface.

### Sub-breakdown

1. **ADR-0047 — Driver task structure.** Single-threaded vs. multi-threaded; how does a driver receive IRQ notifications (endpoint + notify); error / restart semantics.
2. **Template crate** `tyrne-driver-template/` — a skeleton a new driver copies from.
3. **Guide** `docs/guides/write-a-driver.md`.

### Acceptance criteria

- ADR-0047 Accepted.
- Template compiles and documents the driver's service interface.

## Milestone E2 — Log service

A userspace service that receives log records from kernel and other userspace tasks via a capability-gated endpoint and emits them to the console (and later, to persistent storage).

### Sub-breakdown

1. **ADR-0048 — Log wire format.** Binary (postcard / custom TLV); versioned; structured key-value per [logging-and-observability.md](../../standards/logging-and-observability.md).
2. **`tyrne-log` facade** in the kernel — the `log!` / `info!` / `warn!` macros encoded in the facade.
3. **Log service task** — listens on its endpoint, reads records, renders to the console.

### Acceptance criteria

- ADR-0048 Accepted.
- Kernel logs route through the service rather than direct UART writes (the boot console remains as emergency fallback).

## Milestone E3 — Service manager / supervisor

A task that starts, watches, and restarts other tasks per a config. The foundation of the init-task concept.

### Sub-breakdown

1. **ADR-0049 — Supervision strategy.** Always-restart / N-failures-then-give-up / operator-controlled.
2. **Supervisor task** that reads a config (compile-time initial, filesystem-based later).
3. **Fault-endpoint plumbing** — each supervised task has its fault endpoint held by the supervisor.

### Acceptance criteria

- ADR-0049 Accepted.
- A deliberately-crashing test task is restarted by the supervisor per the configured policy.

## Milestone E4 — Storage driver

QEMU: virtio-blk. Pi 4: SD card via the SDHCI-like controller on BCM2711. The driver exposes a block-device service interface.

### Sub-breakdown

1. **ADR-0050 — Block-device service interface.** Synchronous / asynchronous read-write; sector size; capability model.
2. **`tyrne-driver-virtio-blk`** — the first real non-trivial driver.
3. **`tyrne-driver-sdhci-bcm2711`** — the Pi 4 counterpart (may be stubbed until later).

### Acceptance criteria

- ADR-0050 Accepted.
- A userspace client can read and write sectors through the storage service.

## Milestone E5 — Simple filesystem

A read-mostly filesystem service on top of E4. Initial choice may be read-only (e.g., something like BootFS or a custom simple layout) with write support added later.

### Sub-breakdown

1. **ADR-0051 — Filesystem choice.** Build a simple one, port an existing crate (`littlefs`, `ext4`-via-crate, a log-structured FS like F2FS-style for flash-friendly wear-levelling), or start with a read-only block layout and add write support incrementally. Weighed against portability, `no_std + alloc` compatibility, crash-consistency guarantees, and the smart-home target's preference for flash-friendly wear-levelling.
2. **Filesystem service task** implementing the chosen approach.
3. **Storage capability flow** — the filesystem service has the block-device capability; it grants named-file capabilities to clients.

### Acceptance criteria

- ADR-0051 Accepted.
- A userspace client can open, read, and (at minimum) list files through the filesystem service.

## Milestone E6 — Network stack integration

`smoltcp` or similar, in a userspace network service, using virtio-net on QEMU.

### Sub-breakdown

1. **ADR-0052 — Network stack choice.** smoltcp is the probable answer; this ADR commits to it or to an alternative, covering `no_std + alloc` compatibility, license, and maintenance.
2. **`tyrne-driver-virtio-net`** driver.
3. **Network service task** wrapping the stack with a capability-gated interface.

### Acceptance criteria

- ADR-0052 Accepted.
- Loopback works; a test client completes a TCP three-way handshake with a server on the host.

### Phase E closure

Business review. The system now has enough plumbing to support a real end-user deployment, which is Phase F.

## ADR ledger for Phase E

| ADR | Purpose | Expected state | Note |
|-----|---------|----------------|------|
| ADR-0047 | Driver task structure | E1 | renumbered 2026-05-22, was ADR-0037 (cascade from the Phase C/D renumbering, which shifted onto Phase E's old range) |
| ADR-0048 | Log wire format | E2 | renumbered 2026-05-22, was ADR-0038 (cascade) |
| ADR-0049 | Supervision strategy | E3 | renumbered 2026-05-22, was ADR-0039 (cascade) |
| ADR-0050 | Block-device service interface | E4 | renumbered 2026-05-22, was ADR-0040 (cascade) |
| ADR-0051 | Filesystem choice | E5 | renumbered 2026-05-22, was ADR-0041 (cascade) |
| ADR-0052 | Network stack choice | E6 | renumbered 2026-05-22, was ADR-0042 (cascade). ADR-0052 is now uniquely Phase E's E6: the phase-h/phase-i cascade was completed in this same pass (H → 0063–0065, I → 0066–0068) — see the §Downstream-renumbering note below. |

Numbers are tentative; final numbers are assigned when the ADR is actually written, per [ADR-0013](../../decisions/0013-roadmap-and-planning.md).

> **Downstream-renumbering note (2026-05-22).** The Phase C/D ADR-number collision fix shifted the entire forward ADR chain up by ten slots, and Phase F gained a new milestone (F5 — secure field update, ADR-0057). Phases **C, D, E, F, G, H, and I** were all renumbered/extended in this pass so the full forward chain is collision-free and ascends with phase order: Phase G's ceiling is **ADR-0062** (G5), and the cascade was carried through **H → 0063–0065** and **I → 0066–0068** (which also freed ADR-0057 for the new Phase F5 placeholder). The new overall ceiling is **ADR-0068** (Phase I's I3). All these numbers remain tentative per [ADR-0013](../../decisions/0013-roadmap-and-planning.md); none collides with a live ADR file (highest live is ADR-0035; the supersession ADR-0036 is the only newly-written one).

## Open questions carried into Phase E

- Whether a unified "service interface" pattern emerges that multiple services share, or each service designs its own interface.
- Sync vs. async driver model.
- Where smoltcp fits in licensing and `cargo-vet` posture.

---

## Review-derived work items (2026-07-15 full-repository review)

The 2026-07-15 full-repository review surfaced a cluster of capability-enforcement and object-lifecycle gaps in the current `kernel/src/cap`, `kernel/src/mm`, `kernel/src/obj/task_loader`, `kernel/src/ipc`, and `kernel/src/syscall` code. None of these is exploitable today: `grep` confirms `cap_map`, `cap_create_address_space`, and the other affected primitives have **zero syscall wiring** — every live caller is trusted kernel-internal code (`task_loader.rs`, boot sequencing) or test code, and no EL0 task can reach any of them. That is precisely why they belong on the Phase E backlog rather than an incident report: Phase E is where "userspace drivers as first-class tasks" stops being an architectural claim and starts being real syscall-reachable code (`MemoryRegionCap` for MMIO in Milestone E1, block/network device drivers in E4/E6, task-spawning services throughout). **Each item below MUST be closed in the same change that first exposes its path to a syscall or to a less-trusted caller** — not tracked as a follow-up, not merged as "we'll harden it later." Landing the syscall wiring first and the check second is exactly the ambient-authority window CLAUDE.md rule 1 forbids.

### Epic 1 — Capability-ownership enforcement (close before the syscall wires the path)

These gate Milestone E1: a driver's `MemoryRegionCap` for its device's MMIO is backed by the same `cap_map`/`cap_create_address_space`/`cap_derive` machinery audited here, and by extension every later milestone that maps device memory into a task (E4 storage driver, E6 network stack integration).

- 🟠 **HIGH** — `cap_map`/`cap_create_address_space` accept a caller-chosen `PhysFrame` with no memory-ownership capability check — an ambient-authority gap: any caller that reaches these functions can map arbitrary physical memory into an address space regardless of who owns it.
  - **Location:** `kernel/src/mm/address_space.rs:728-746` (`cap_map`); also `kernel/src/cap/mod.rs:85-86` (`CapKind::MemoryRegion` reserved but unimplemented).
  - **Action:** Treat as a hard architectural precondition, not a follow-up. Land the `MemoryRegion` capability / Untyped-style frame-ownership discipline (already tracked against [ADR-0028](../../decisions/0028-address-space-data-structure.md) for B4+) and thread a frame-ownership check through `cap_map` **before** any syscall exposes it to userspace — concretely, before Milestone E1's driver template can hand a real `MemoryRegionCap` to a driver task. Add a CI or review gate (a comment-linked TODO/ADR condition) that blocks a syscall-dispatch-wiring PR for `cap_map` from merging until the ownership check exists.

- 🟠 **HIGH** — `cap_derive` lets the caller mint a capability naming an arbitrary, unrelated kernel object — there is no check that `new_object` relates to `src` at all, and the [ADR-0014](../../decisions/0014-capability-representation.md) src↔object correlation was never implemented.
  - **Location:** `kernel/src/cap/table.rs:258-320` (`cap_derive`; doc at 243-247).
  - **Action:** Split the kind check out from the existing rights validation (which stays unchanged: DERIVE-present, then no-widening). Add the kind check using the accessors that actually exist — there is **no** `rights_and_kind_of` helper: the `entry_of(src)` lookup already inside `cap_derive` resolves the source capability, so compare its kind (`entry.capability.kind()`, i.e. `Capability::kind()` → `self.object.kind()`) against `new_object.kind()` (`CapObject::kind() -> CapKind`), returning `CapError::WrongKind` on mismatch. Minimal, safe, zero-cost. This does not break the one legitimate current call site (`cap_create_address_space` in `kernel/src/mm/address_space.rs:674-678`, which already independently checks `parent_cap.kind() == CapKind::AddressSpace` at line 551 before calling `cap_derive` with a fresh `CapObject::AddressSpace(handle)`; kind always matches there). For the deeper same-kind/different-instance case (e.g. an AddressSpace-DERIVE holder minting a cap to a *different* AddressSpace it was never granted), write a short ADR-0014 revision note (or successor ADR) formalizing that `cap_derive` is a "mint-new-object under creation-authority" primitive, not a same-object narrowing primitive — this was explicitly promised in ADR-0014 and never delivered.

- ⚪ **LOW** — `cap_derive`'s object-identity behavior is completely untested — no test pins whether a kind- or instance-mismatched `new_object` is accepted or rejected.
  - **Location:** `kernel/src/cap/table.rs:1123-1317` (test module).
  - **Action:** Add at least two tests once the kind-check above lands: (1) a positive/negative pin for cross-kind derivation (`cap_derive` from a `Task`-kind source with `new_object = CapObject::Endpoint(...)`); (2) if same-kind-different-instance derivation is intended to stay permitted (the `cap_create_address_space` "mint new" pattern), a test that documents this by name — e.g. `cap_derive_same_kind_different_object_is_permitted_by_design` — so the behavior is pinned rather than accidental.

- 🟡 **MEDIUM** — `link_child`'s (believed-unreachable) `InvalidHandle` path permanently leaks the already-popped free-list slot, with no `debug_assert` unlike the file's other "should never happen" branches.
  - **Location:** `kernel/src/cap/table.rs:613-628` (`link_child`); call sites at 220-227 (`cap_copy`) and 300-306 (`cap_derive`).
  - **Action:** Either (a) push `new_index` back onto the free list before returning the error (mirror `free_slot`'s prepend), or (b) reorder so the parent's liveness is validated *before* `pop_free()` is called — `link_child` could take an already-resolved `&mut SlotEntry` for the parent instead of an `Option<Index>`, eliminating the ordering hazard entirely. Either way, add `debug_assert!(false, "link_child: parent slot is empty")` matching the file's existing convention so a future invariant violation is caught loudly in tests rather than silently shrinking table capacity in production.

- 🟡 **MEDIUM** — W^X is unenforced by the mapping primitives: flags flow unchecked from caller through `cap_map` to `Mmu::map`, and neither `cap_map` nor the encoder rejects WRITE+EXECUTE.
  - **Location:** `kernel/src/mm/address_space.rs:728-746` (`cap_map`); cross-checked against `hal/src/mmu/vmsav8.rs:342-350` (`flags_to_descriptor_bits`).
  - **Action:** Enforce the invariant at the **shared, lower layer** — `Mmu::map` or a new shared `MappingFlags::validate()` — by rejecting `WRITE && EXECUTE && USER` (the userspace W^X case) with `InvalidFlags`, *not* at `cap_map`. Scope the check to the USER-tagged case specifically: kernel-only `WRITE && EXECUTE` — the existing ADR-0034-blessed bootstrap RWX block mapping — stays permitted until the ADR-0034 per-section kernel-image remap lands, so the guard must not reject it. `cap_map` is **not** the universal chokepoint: the task loader and bootstrap map pages by calling the mapper directly, bypassing `cap_map` entirely (this is exactly the direct-caller path the companion finding immediately below covers). Landing the check in the shared validation point closes the gap for every caller by construction. Keep the **same** `WRITE && EXECUTE && USER` rejection at `cap_map` too, framed as **defense-in-depth** at the capability layer — so the capability path still fails closed even if a future refactor moves the lower-level check. Both are independent of, and cheaper than, the broader ADR-0034 per-section kernel-image remap work.

- ⚪ **LOW** — `Mmu::map`/`flags_to_descriptor_bits` do not structurally reject WRITE+EXECUTE+USER — W^X is upheld only by loader-call-site discipline, not by the primitive itself. **This is the primary, shared enforcement point** the finding above defers to (it covers the direct loader/bootstrap callers that bypass `cap_map`); the `cap_map` guard is the defense-in-depth companion, not the authoritative check.
  - **Location:** `bsp-qemu-virt/src/mmu.rs:259-271` (`Mmu::map`'s only flag-combination rejection today is DEVICE+EXECUTE); `hal/src/mmu/vmsav8.rs:319-350` (`flags_to_descriptor_bits`).
  - **Action:** Make the shared MMU validation — `Mmu::map`, or a shared `MappingFlags::validate()` it calls — the **authoritative** rejection point for `WRITE && EXECUTE && USER`, returning `InvalidFlags`: it is the one point every direct mapper caller (`cap_map`, the task loader, bootstrap) passes through, so the userspace-W^X gap closes there by construction. Keep **matching** defense-in-depth checks at the two layers bracketing it — the VMSAv8 descriptor encoder (`flags_to_descriptor_bits`, the last line before the raw descriptor bits; mirror its existing DEVICE+EXECUTE guard) and `cap_map` (the capability layer, per the finding above) — so all direct callers stay covered even if one layer is later refactored. Continue to permit kernel-only `WRITE && EXECUTE` (the ADR-0034-blessed bootstrap RWX) at every layer until the per-section remap lands. Cheap now, before any userspace-reachable map-style syscall exists; expensive to retrofit once multiple callers depend on the permissive behavior.

- ⚪ **LOW** — `resolve_address_space_cap` checks capability kind only, never rights — `CapRights::EMPTY` still grants full map/unmap/activate authority.
  - **Location:** `kernel/src/mm/address_space.rs:430-441` (`resolve_address_space_cap`), used by `cap_map:738` and `cap_unmap:782`.
  - **Action:** Before any syscall wiring exposes `cap_map`/`cap_unmap` to userspace, land the per-operation rights bits (MAP/UNMAP/ACTIVATE) the doc comment already anticipates for "B5+", and have `resolve_address_space_cap` take an expected-rights parameter so `cap_map` and `cap_unmap` can each demand the specific bit they need instead of sharing one kind-only check.

- ⚪ **LOW** — `AddressSpaceCap` authority is kind-only (any AS cap of the right kind grants full map/unmap/activate), not rights-gated per operation, and this gap has no entry in `security-model.md`'s open-questions list (unlike the kernel-image W^X gap, which does).
  - **Location:** `kernel/src/mm/address_space.rs:408-441` (`resolve_address_space_cap` doc + body).
  - **Action:** Add an entry to the security model document's Open Questions recording that `AddressSpaceCap` authority is currently kind-gated rather than rights-gated, and that this must close before `cap_map`/`cap_unmap` become syscall-reachable — at which point a holder of any narrowed/derived AS cap (e.g. one meant only to `activate`) could `unmap` arbitrary pages in that AS. Companion documentation fix to the finding directly above; do not merge one without the other.

- ⚪ **LOW** — `cap_map`/`cap_unmap` discharge `MapperFlush` tokens without documenting reliance on `activate`'s full-TLB-flush as the compensating control for non-active address spaces.
  - **Location:** `kernel/src/mm/address_space.rs:741-744` (`cap_map`'s `token.flush(mmu)`) and `:785-788` (`cap_unmap`'s `token.flush(mmu)`); cross-referenced against `hal/src/mmu/mod.rs:376-386`.
  - **Action:** Add a short doc note at `cap_map`/`cap_unmap` cross-referencing `hal::MapperFlush`'s future-soundness-cliff paragraph, stating explicitly that correctness for non-active-AS mutation currently depends on `Mmu::activate`'s unconditional full flush — so a future change to `activate`'s flush policy (e.g. when ASIDs land) must revisit both call sites in lockstep.

### Epic 2 — Object lifecycle & reclaim

These gate Milestone E3 (service manager/supervisor): crash-and-restart of a supervised task is the first realistic trigger for reclaiming task-owned kernel resources at runtime rather than only at boot. They also connect directly to the existing Phase-C carry-forward **EL0 fault containment (K3-4)** — already tracked in `phase-c.md`'s carry-forward list and targeted at Phase E ("first real driver task") rather than Phase C. K3-4's supervisor-endpoint fault delivery is exactly Milestone E3's "Fault-endpoint plumbing" sub-item; closing K3-4's *fault-reporting* path and closing this epic's *resource-reclamation* path are two halves of the same restart story and should land together — a supervisor that can observe a crashed task's fault but cannot reclaim its address-space arena slot, frames, or capabilities has only solved half the problem Milestone E3 exists to solve.

- 🟡 **MEDIUM** — every failed `load_image` call permanently burns one of only 8 total address-space arena slots — no reclaim path exists.
  - **Location:** `kernel/src/obj/task_loader.rs:468-479` (rollback discipline doc), `:810-823` (`rollback()` doc), `:849-851` (`rollback()`'s cap-drop-only cleanup).
  - **Action:** With only 8 total slots, this is not a distant concern — the moment any code path calls `load_image` more than a handful of times without treating every failure as fatal (spawning several userspace tasks in a loop, or retrying after a transient frame-budget miss), the kernel permanently loses its ability to create new address spaces for its entire remaining uptime. Prioritize landing the forward-flagged `MemoryRegionCap`/per-AS-destroy mechanism (or at minimum a `Pmm`-and-arena-level rollback that also frees the AS arena slot) before `load_image` is called more than once per boot in any production path — which Milestone E3's restart loop will do routinely.

- 🟡 **MEDIUM** — `rollback()` leaks the AS arena slot despite an already-reachable, ADR-free function (`destroy_address_space` + `AddressSpace::root_frame`) that could reclaim it and the L0 root frame today.
  - **Location:** `kernel/src/obj/task_loader.rs:824-852` (`rollback()` body); `kernel/src/mm/address_space.rs:306-313` (`destroy_address_space`), `kernel/src/mm/address_space.rs:123-131` (`AddressSpace::root_frame`).
  - **Action:** Wire `rollback()` to resolve `loaded_as_cap` → `AddressSpaceHandle` (mirroring `task_create_from_image`'s own step-1 lookup), call `destroy_address_space(as_arena, handle)`, and `pmm.free_frame(freed.root_frame(mmu))` on the result before (or after) `cap_drop`. This closes two of the three documented leaks (arena slot + L0 frame) immediately, without waiting on the forward-flagged `MemoryRegionCap`/per-AS-destroy ADR — only the intermediate-table leak genuinely needs that future work. Update the `rollback()`/`load_image` doc comments to stop implying the whole leak set is ADR-blocked.

- ⚪ **LOW** — `reset_if_stale_generation`'s capability-leak guard is a debug-only `debug_assert` with no release-mode enforcement.
  - **Location:** `kernel/src/ipc/mod.rs:254-271` (`reset_if_stale_generation`); cross-ref `kernel/src/obj/endpoint.rs:78-114` (`destroy_endpoint`, C3-001 note).
  - **Action:** Track this as a hard precondition for the Phase B.2+ endpoint-destroy ADR ([ADR-0032](../../decisions/0032-endpoint-rollback-and-cancel-recv.md) already references it, and it is the same destroy/drain primitive Milestone E3's task-restart path will exercise): the destroy/drain primitive must not be mergeable until the cap-bearing-slot case is a release-mode-enforced refusal (typed error) rather than a `debug_assert!` — a silent authority leak in release is exactly the failure mode CLAUDE.md rule 1 rules out. No code change is required in `kernel/src/ipc/mod.rs` itself yet, but the tracking issue must say explicitly "promote `debug_assert!` to a release-enforced check," not just "add a drain step."

### Epic 3 — Userland runtime maturation

Findings that don't sit at a capability-mint chokepoint or an object-destroy path, but harden the syscall/IPC/task-creation surface every Phase E service will exercise routinely once real drivers and services (E1 onward) make live syscalls instead of being test/boot-only callers.

- ⚪ **LOW** — `SyscallError::Ipc(ReceiverTableFull)` discloses a different task's private resource state to the sender, outside ADR-0030's stated security justification.
  - **Location:** `kernel/src/syscall/error.rs:145` (`IpcError::ReceiverTableFull => 6,` inside `ipc_error_code`, composed into the stable status `0x206`).
  - **Action:** Either (a) extend [ADR-0030](../../decisions/0030-syscall-abi.md)'s security argument with an explicit rider covering `ReceiverTableFull`/`QueueFull`, documenting why disclosing a communicating peer's transient resource state to a party that already holds a SEND capability to it is an acceptable, bounded leak, or (b) if the leak isn't worth the diagnostic value, collapse `ReceiverTableFull` into a less specific code (e.g. fold it into `QueueFull` or a generic "transfer could not complete, retry" code) that does not name which side's table caused it. Given this is genuinely low-severity and low-likelihood, (a) — an explicit ADR amendment closing the analysis gap — is the proportionate fix, and should land before Milestone E2's log service and E3's supervisor put IPC error codes in front of routine cross-task traffic.

- ⚪ **LOW** — the `has_current_task` / fail-closed-table pairing is enforced only by caller discipline, not asserted inside `dispatch()`.
  - **Location:** `kernel/src/syscall/dispatch.rs:97-110, 144-161`.
  - **Action:** Add a cheap `debug_assert!` at the top of `dispatch` (or a constructor-time check on `SyscallContext`) asserting that `has_current_task == false` implies the caller table cannot resolve any handle — e.g. expose/require a cheap `CapabilityTable::is_empty()` the test-only assertion can call. Converts an implicit, externally-verified contract into a self-checking one, matching the module's stated "single most security-sensitive control-flow join" bar, before Phase E's services turn this join into a hot path.

- ⚪ **LOW** — `task_create_from_image` trusts a caller-constructed `LoadedImage` with no consistency check against the named address space.
  - **Location:** `kernel/src/obj/task_loader.rs:194-229` (`LoadedImage` field-invariants doc), `:917-936` (`task_create_from_image` step 1).
  - **Action:** Either (a) make `LoadedImage`'s fields private with construction restricted to `load_image`'s success path — removing the public-struct-literal convention now that a real consumer (`task_create_from_image`) exists — or (b) have `task_create_from_image` perform a cheap runtime check (e.g. via the [ADR-0038](../../decisions/0038-mmu-translate-and-user-access.md) `Mmu::translate` read-only walk once it lands) that `entry_va` resolves to an EXECUTE|USER mapping inside the AS named by `as_cap` before minting the Task cap. Permissive construction was safe when `LoadedImage` was purely a descriptor (pre-T-024); it is materially riskier now that it seeds a runnable EL0 execution context — and Milestone E1's driver template will be the first non-boot code constructing these routinely.

- ⚪ **LOW** — `task_create_from_image` mints a live task but leaves the source AS capability's unrestricted map/unmap authority untouched.
  - **Location:** `kernel/src/obj/task_loader.rs:892-903` (v1 cap-rights model doc), `:917-967` (`task_create_from_image` body).
  - **Action:** Not currently exploitable — the cap lives only in the fully-trusted `BOOTSTRAP_AS_TABLE`, unreachable from EL0 — but the gap is structural and belongs to the trust-boundary story this module owns. Document explicitly in `task_create_from_image`'s doc comment what the caller is expected to do with `loaded.as_cap` after minting a task (drop it, or keep only a documented-safe use), and/or forward-flag that per-operation AS rights (MAP/UNMAP, already a named B5+ TODO elsewhere in this file — see the `resolve_address_space_cap` finding in Epic 1) must close this gap before `task_create_from_image` is reachable from anything less than fully-trusted kernel-boot code, which Milestone E1's driver spawning will be.

- ⚪ **LOW** — `task_create_from_image` mints a Task cap from an AS cap with zero rights check — not even DERIVE — unlike `cap_create_address_space`'s explicit DERIVE-gated mint.
  - **Location:** `kernel/src/obj/task_loader.rs:924-936` (step 1, no rights check on the resolved AS cap).
  - **Action:** If the intent is genuinely "any AS cap of the right kind authorizes task creation, mirroring the AS kind-only model" (a defensible v1 choice given the project's own documented kind-only AS baseline), say so explicitly in `task_create_from_image`'s doc comment — the same way `resolve_address_space_cap`'s doc explicitly calls out its own kind-only contract — so a future reader doesn't mistake the omission for an oversight. Otherwise, gate on `CapRights::DERIVE` (or a purpose-built right) to match `cap_create_address_space`'s discipline before this function becomes reachable from anything less trusted than boot code.

### Polish & excellence

- **Polish** — Bake rights/kind correlation into `CapRights` or `Capability::new` as defense-in-depth, complementing the `cap_derive` fix above: catches a nonsensical rights/kind combination at construction time rather than relying on every downstream syscall handler to independently check both kind and the relevant right bit. Zero runtime cost in release builds (`debug_assert`); turns a class of "the two are just conventionally correlated" bugs into compile-adjacent, test-caught ones.

- **Polish** — Surface the destroy-drain / cap-leak forward-reference from `obj::endpoint.rs` inside `ipc/mod.rs`'s own module doc, so a reader auditing `ipc/mod.rs` in isolation doesn't have to cross into `obj/endpoint.rs` to get the full picture of an already well-documented hazard — keeps the two halves co-located for the next auditor, and for whoever lands Milestone E3's fault/restart path.

- **Polish** — Track `ObjError::StillReachable`/`references_object` as unenforced before the first destroy-capable syscall lands. A short pre-flight checklist item — "the first live `task_destroy`/`endpoint_destroy`/`notification_destroy` syscall must wire `references_object` across every live `CapabilityTable`, not just one" — prevents this deferred invariant from being forgotten when Milestone E3's supervisor restart path authors that syscall (related tracking: SEC-T028-01 in `sched/mod.rs:958-964`).

- **Polish** — Surface a per-AS live-mapping/frame-count diagnostic accessor (mirroring `root_frame()`). Would help the eventual B4+/E3 per-AS destroy path verify it has fully drained an AS's mappings before freeing the root, and make future OOM/leak debugging on real hardware substantially easier.

- **Polish** — Reserve VA 0 as an unmapped guard page. High-assurance kernels commonly refuse to map the zero page (Linux's `mmap_min_addr`, OpenBSD's default) as defense-in-depth against a kernel NULL-pointer-dereference bug turning into userspace-controlled arbitrary-address kernel memory access. Low-cost, high-signal hardening to consider once image placement becomes policy-configurable rather than a fixed linker-script constant — worth doing before `copy_from_user`/`copy_to_user` (ADR-0038) starts dereferencing user-supplied pointers in earnest for Phase E's driver/service IPC traffic.

- **Polish** — Enforce or forward-flag task-id uniqueness. Currently harmless (`Task::id()` is used only for diagnostics/tests, not as an addressing key), but worth a one-line doc note or a `debug_assert`-level uniqueness check now, before scheduler diagnostics, IPC addressing, or debugger attach start trusting task ids as unique — all plausible needs once Milestone E3's supervisor is watching multiple live tasks.

- **Polish** — Cross-reference the `WidenedRights`/intermediate-frame-count forward-flags already sitting in the task-loader docstrings back to their originating review item (`docs/analysis/reviews/master-review/2026-05-22-152729/tracks/C4-kernel-task-loader.md`), the same discipline already applied to the unsafe-log cross-references, so a future reader doesn't have to independently rediscover which review round motivated each comment.

- **Polish** — Add a structural WRITE^EXECUTE guard to `Mmu::map`/`flags_to_descriptor_bits` mirroring the existing DEVICE^EXECUTE guard (see the matching Epic 1 finding). Converts today's "W^X holds because the one caller behaves" into "W^X holds because the primitive enforces it" — the difference matters precisely because Phase C and beyond add more mapping call sites (per-region `MemoryRegionCap`, a future mmap-equivalent syscall), and each new caller currently inherits zero protection from the trait layer.

---

Covers all 17 review findings + 8 polish items routed to this phase.
