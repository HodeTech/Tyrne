# Phase G — Security maturation

**Exit bar:** Measured boot where hardware permits, cryptographic primitives available, TLS usable by network services, and a formal-verification pilot on a core primitive. Security posture becomes demonstrable rather than aspirational.

**Scope:** The "high assurance" claim of [ADR-0001](../../decisions/0001-microkernel-architecture.md) turns into shipped features. May overlap with Phase F if Phase F needs crypto before this phase formally starts.

**Out of scope:** Verifying the whole kernel (far horizon); hardware security modules (depends on hardware choice); certification.

---

## Milestone G1 — Measured boot

On hardware that supports it (Pi 4 via its secure-boot chain, or a future board with TPM / secure element), extend the boot flow to measure each stage.

### Sub-breakdown

1. **ADR-0058 — Boot measurement scheme.** PCR-like registers, event log, chaining algorithm (SHA-256 vs. -384), where measurements are stored.
2. **BSP integration** — measurement computed for the kernel image before `kernel_entry`; recorded somewhere the kernel can query.
3. **Verification path** — a post-boot service that reads the measurement log and compares against expected values (signed manifest).

### Acceptance criteria

- ADR-0058 Accepted.
- Measurement log produced on a supported board and inspectable from userspace.

## Milestone G1.5 — TEE support in the HAL

Introduce a Trusted Execution Environment trait in `tyrne-hal` and a BSP implementation where the hardware offers ARM TrustZone or an equivalent. This is one of the four "AI-readiness" hooks mandated by [ADR-0015](../../decisions/0015-ai-integration-stance.md); it also stands on its own for non-AI use (secrets protection, boot attestation, high-assurance crypto containment).

### Sub-breakdown

1. **ADR — TEE trait surface.** What operations (enter / exit, attested message exchange, key sealing), what errors, what capability model for granting TEE access.
2. **BSP implementation** for whichever target is chosen first (Pi 4 TrustZone via Pi firmware is plausible; QEMU has `-machine virt,secure=on`; Jetson has its own chain).
3. **Integration with G1** — boot measurements can be sealed to the TEE for attestation.
4. **Security review** per [`analysis/reviews/security-reviews/`](../../analysis/reviews/security-reviews/).

### Acceptance criteria

- TEE trait in `tyrne-hal` with at least one BSP impl.
- Security review recorded; attestation flow documented.
- Usable independently by Phase G2 (crypto) and — later — by Phase J6 (confidential inference).

### Why this pairs with G1

Measured boot and TEE are complementary: measured boot proves what was loaded, TEE protects what runs. Doing them together lets both land with a single security review and a consistent attestation model.

## Milestone G2 — Cryptographic primitives

A crypto crate with audited implementations: hash (SHA-2, SHA-3), AEAD (ChaCha20-Poly1305, AES-GCM), signature (Ed25519, ECDSA P-256), random-bytes source.

### Sub-breakdown

1. **ADR-0059 — Crypto crate choice.** RustCrypto crates vs. one curated alternative vs. in-tree impls. Auditability, formal guarantees where applicable, no-std support.
2. **`tyrne-crypto`** — the crate that wraps the chosen primitives with Tyrne-native types (`Hash`, `Key`, `Signature`, `Nonce`).
3. **Security review** per [`analysis/reviews/security-reviews/`](../../analysis/reviews/security-reviews/) — mandatory for every primitive.
4. **Constant-time audit** — where timing side channels matter, document which paths are constant-time and which are not.

### Acceptance criteria

- ADR-0059 Accepted.
- Each primitive's security review recorded.
- No primitive is in-tree hand-rolled without explicit justification.

## Milestone G3 — TLS / DTLS

For network services (Phase E6) to talk securely. Probably `rustls` if `no_std + alloc` works; otherwise a curated alternative.

### Sub-breakdown

1. **ADR-0060 — TLS library choice.** rustls (preferred), mbedtls, in-tree. Covers version-pinning, maintenance, supply-chain posture.
2. **Integration** with the network service from E6.
3. **Test** — TLS 1.3 handshake with a known server.

### Acceptance criteria

- ADR-0060 Accepted.
- Network service completes a TLS handshake and exchanges encrypted data.

## Milestone G4 — Formal verification pilot

Pick one kernel primitive — probably the capability table's derivation/revocation logic — and specify-and-verify it with Kani / Creusot / some tool suited to Rust.

### Sub-breakdown

1. **ADR-0061 — Verification tool choice.** What tool for what scope; how it interacts with the build.
2. **Specification** of the chosen primitive's invariants in machine-checkable form.
3. **Proof** (or counterexamples that correct the implementation).
4. **CI integration** — verification runs per-commit on the verified subset.

### Acceptance criteria

- ADR-0061 Accepted.
- At least one invariant proved on a real kernel primitive.
- CI fails if the verification breaks.

## Milestone G5 — Threat model v2

Revisit the threat model from [`security-model.md`](../../architecture/security-model.md) with the experience accumulated through Phases A–F. Some threats will have moved from "out of scope" to "in scope"; some will be deprecated.

### Sub-breakdown

1. **Review of the existing threat model** against Phase F deployment learnings.
2. **ADR-0062 — Threat model v2.** Explicit supersession of security-model's Phase-1 threat statements where warranted.
3. **`security-model.md` update** to reflect v2 (standards-update skill + ADR-first discipline).

### Acceptance criteria

- ADR-0062 Accepted.
- `security-model.md` updated.
- Business review captures "what the deployment taught us about the model."

### Phase G closure

Business review. Tyrne now has the security engineering to back the "high assurance" claim at a level beyond process.

## ADR ledger for Phase G

| ADR | Purpose | Expected state | Note |
|-----|---------|----------------|------|
| ADR-0058 | Boot measurement scheme | G1 | renumbered 2026-05-22, was ADR-0047 (cascade from the Phase C/D renumbering). G1.5's TEE-trait ADR remains an unnumbered placeholder. |
| ADR-0059 | Crypto crate choice | G2 | renumbered 2026-05-22, was ADR-0048 (cascade) |
| ADR-0060 | TLS library choice | G3 | renumbered 2026-05-22, was ADR-0049 (cascade) |
| ADR-0061 | Verification tool choice | G4 | renumbered 2026-05-22, was ADR-0050 (cascade) |
| ADR-0062 | Threat model v2 | G5 | renumbered 2026-05-22, was ADR-0051 (cascade). Phase G's ceiling is ADR-0062; phases H and I were renumbered in the same pass (H → 0063–0065, I → 0066–0068), completing the cascade — see the §Downstream-renumbering note in [phase-e.md](phase-e.md). |

Numbers are tentative; final numbers are assigned when the ADR is actually written, per [ADR-0013](../../decisions/0013-roadmap-and-planning.md).

## Open questions carried into Phase G

- Whether verification is a standing practice after G4 or a one-off pilot.
- How deeply to audit crypto dependencies we do not own.
- Whether TLS lives in the network service or in its own crypto service (likely its own service for capability-scope reasons).

---

## Review-derived work items (2026-07-15 full-repository review)

The 2026-07-15 full-repository review found Phase G's scope largely in the "prove-it" category: the review turned up only one documentation-accuracy finding, and its remaining observations are excellence/polish items that push already-correct code and already-documented gaps toward the exemplary standard a high-assurance kernel should hold itself to. Items are grouped into the three epics below, followed by the one stray finding and a Polish & excellence subsection.

### Epic G-R1 — Prove-it: property & fuzz testing of invariants

This phase's "prove-it" posture (Milestone G4 in particular) is best served by turning today's hand-picked example tests into property/fuzz tests that defend the codebase's stated invariants across their full input space rather than at a few chosen boundary points. Four independent opportunities converge on this theme:

- **[Polish]** Property-test the capability derivation-tree invariants (parent-liveness, no-cycles, BFS-completeness).
  - Location: `kernel/src/cap/table.rs` — `cap_derive` (table.rs:258); the derivation-tree size-and-shape reasoning at table.rs:341-359; the cycle-detection `debug_assert!`s at table.rs:369-372 and table.rs:393-396, which today only fire incidentally during ordinary unit tests; the ADR-0014 cross-reference at table.rs:428.
  - Action: add a `proptest`/`quickcheck`-style test module (the crate already runs a `no_std`-with-`std`-test-harness setup, so this is a dependency-light addition) that generates randomized sequences of `cap_derive` / `cap_copy` / `cap_revoke` calls against `CapabilityTable` and asserts, after every step: (1) every live slot's parent chain terminates at a root within `MAX_DERIVATION_DEPTH` (parent-liveness); (2) the `first_child`/`next_sibling` linked structure never revisits a node (no-cycles) — the property the existing `debug_assert!`s only catch by accident; (3) a BFS from any node visits exactly its live descendant set, each exactly once (BFS-completeness), checked against a reference `HashSet`-based oracle. This is a precursor deliverable for Epic G-R2 below — it independently re-derives, and directly precedes, the "prior review already flagged this as a strong fit" conclusion for the same invariants.

- **[Polish]** Add a property/fuzz test asserting panic-freedom over the full syscall register space.
  - Location: `kernel/src/syscall/dispatch.rs` — the module's stated hard rule at dispatch.rs:9-11 ("No path may `panic!` / `unwrap` / `expect` on any register-supplied input"); `dispatch()` itself at dispatch.rs:129.
  - Action: add a property/fuzz test (a `proptest` strategy or a `cargo-fuzz` target, whichever the crate's existing test tooling favors) that calls `dispatch` with randomized `SyscallNumber` and `x1`–`x7` register patterns drawn from the full `u64` space and asserts no panic occurs for any input. This turns the module doc's strongest stated guarantee from "true for tested inputs" into "defended by construction of the test," the natural next step from correct to exemplary.

- **[Polish]** Property-test `SchedQueue`'s wraparound arithmetic.
  - Location: `kernel/src/sched/mod.rs` — `SchedQueue::enqueue`'s `wrapping_add`/`% N` tail computation (mod.rs:104-119) and the mirrored `dequeue` head advance (mod.rs:133); the existing hand-picked FIFO/full/empty/one-wraparound tests (mod.rs:1737-1780 area).
  - Action: add a reference-model fuzz/property test that runs `SchedQueue<N>` against a `std::collections::VecDeque` oracle over randomized enqueue/dequeue sequences at several `N` values, with generation biased toward the `N`-1 boundary and repeated-wrap sequences — exactly the region where an off-by-one is easy to miss by hand and cheap to catch by construction, given the crate is already `no_std`-with-`std`-test-harness.

- **[Polish]** Exhaustive pairwise-disjointness test across the full status-code space.
  - Location: `kernel/src/syscall/error.rs` — the blocked status-code layout documented at error.rs:1-27 (`0` = Ok, `1`–`3` top-level, `0x101`–`0x1FF` = Cap block, `0x201`–`0x2FF` = Ipc block); `SyscallError::as_status` (error.rs:95); the existing `cap_and_ipc_status_blocks_do_not_collide` test (error.rs:241 area), which checks only block-level, not full pairwise, disjointness.
  - Action: add a host test that enumerates every `CapError`, `IpcError`, and top-level `SyscallError` variant's `as_status()` output into one collection (e.g. inserting into a `BTreeSet` and asserting every insert returns `true`) and asserts all values are pairwise distinct. This closes the gap left by the existing block-collision test without requiring a `const`-fn rewrite, and fits the module's already-strong culture of pinning ABI-stability invariants with host tests (the exhaustive-without-wildcard match technique cited in error.rs's own module doc, error.rs:24-27).

### Epic G-R2 — Formal-verification pilot candidates

Milestone G4 names its target only tentatively ("probably the capability table's derivation/revocation logic"). Based on this review, three primitives are strong, concretely-scoped candidates for the ADR-0061 tool pilot (gates Milestone G4's Specification sub-step):

- **Capability derivation/revocation logic** — `kernel/src/cap/table.rs`'s `cap_derive` (table.rs:258) and `cap_revoke` (table.rs:329), including the BFS descendant-collection loops at table.rs:341-410. This is the primitive G4 already names as the likely target, and it is the highest-value candidate: it is security-critical, its invariants are genuinely multi-step (spanning several functions, per Epic G-R1 above), and Epic G-R1's property tests are a direct, low-cost precursor to G4's Specification sub-step — the same parent-liveness / no-cycles / BFS-completeness invariants that a property test defends empirically are exactly what a machine-checkable specification needs to state formally.
- **`SchedQueue`'s bounded-FIFO wraparound arithmetic** — `kernel/src/sched/mod.rs:104-134`. Small, self-contained, free of external dependencies or `unsafe`, and already isolated behind a `const`-generic capacity (mod.rs:91). A good lower-risk warm-up candidate for exercising whichever tool ADR-0061 selects before committing to the higher-stakes capability-table primitive.
- **Syscall status-code encoding** — `kernel/src/syscall/error.rs`'s `as_status` (error.rs:95) and `kernel/src/syscall/abi.rs`'s `encode_cap_handle`/`decode_cap_handle` (abi.rs:213 area). Purely combinatorial, `unsafe`-free code with an existing exhaustive-match discipline (error.rs:24-27) — well suited to a tool that specializes in bounded model-checking over a finite state space, and complementary to the pairwise-disjointness property test in Epic G-R1.

### Epic G-R3 — Decisions to formalize

- **[Polish]** Make an explicit ADR call on zero-on-free vs. zero-on-alloc-only before capability revocation lands.
  - Location: [ADR-0035](../../decisions/0035-physical-memory-manager.md):33 ("Capability-aware extension point... the future capability-system grants will sit on top of `Pmm::alloc_frame`"); `kernel/src/mm/pmm.rs` — the module doc's "zero-fill every allocated frame" statement (pmm.rs:18) confirms the current posture is zero-on-alloc-only; `alloc_frame`'s doc (pmm.rs:327-335).
  - Action: write an ADR making the zero-on-free vs. zero-on-alloc-only decision explicit before B5+'s `MemoryRegionCap` revocation model creates the first real reader of freed-but-unreused physical frames. Per CLAUDE.md's security-first rule ("when in doubt, choose the more conservative option"), the current zero-on-alloc-only behavior should be either upgraded to zero-on-free or explicitly justified against a stated threat model — not inherited silently as the default. Number per the Phase G ADR ledger's normal allocation process.

- **Measured-boot items** — cross-checked against Milestone G1, not new scope. The review found no measured-boot decision point that Milestone G1's ADR-0058 sub-breakdown (item 1: "PCR-like registers, event log, chaining algorithm (SHA-256 vs. -384), where measurements are stored") does not already track. This bullet records that cross-check for completeness; ADR-0058 remains the single place these decisions land, and no additional decision item is proposed here.

### HAL/BSP: documentation accuracy

- **[⚫ INFO]** Wrong unsafe-policy section cited for `create_address_space`'s "no separate audit entry" claim.
  - Location: `bsp-qemu-virt/src/mmu.rs:174-186` (the `create_address_space` `SAFETY` comment), specifically the citation "per unsafe-policy §4" at mmu.rs:180.
  - Action: correct the citation — [docs/standards/unsafe-policy.md](../../standards/unsafe-policy.md) §4 covers `unsafe impl` / `unsafe trait` discipline, not this case (an unsafe-body-free `unsafe fn` implementing a trait method's contract). Cite §2 ("`unsafe fn` requires a `# Safety` section") and/or §3 ("every `unsafe` block has an audit entry") instead, whose reasoning is what the comment actually relies on. Alternatively, if the project wants to formally recognize "unsafe-body-free `unsafe fn` implementing a safe trait method" as its own named exemption class, add that language explicitly to unsafe-policy.md rather than leaving the reasoning implicit in a single call-site comment.

### Polish & excellence

- **[Polish]** `cap_revoke`'s release-build fallback silently reports `Ok(())` on a (currently provably unreachable) invariant violation, rather than failing closed.
  - Location: `kernel/src/cap/table.rs:369-374` and the mirrored branch at table.rs:393-398, inside `cap_revoke`'s BFS descendant-collection loop (`cap_revoke` starts at table.rs:329; the size proof backing "provably unreachable" is at table.rs:353-359).
  - Action: on the `desc_len >= CAP_TABLE_CAPACITY` branch, return a typed `CapError` (or escalate to a hard `panic!`/`assert!`, matching the precedent `enqueue_ready` already sets for an analogous "should never happen" condition at `kernel/src/sched/mod.rs:605-608`) instead of `break`-ing out to a silent `Ok(())`. Speculative defense-in-depth rather than an active bug — the current size proof is sound today — but a few lines of change make `cap_revoke` fail-closed under future corruption instead of fail-open.

- **[Polish]** Promote the two v1 rights-model gaps from source docstrings to `security-model.md`'s tracked Open Questions list.
  - Location: `kernel/src/mm/address_space.rs:416-421` (`resolve_address_space_cap`'s "v1 rights model" docstring: an `AddressSpaceCap` grants full mapping authority by kind alone, not by rights bits — deferred to B5+); `hal/src/mmu/mod.rs`'s `Mmu::map` flags contract (mod.rs:565-573), which documents only the `DEVICE | EXECUTE` rejection and has no `WRITE ^ EXECUTE` guard — confirmed absent by `hal/src/mmu/vmsav8.rs`, whose `WRITE | EXECUTE` flag combination (vmsav8.rs:595, vmsav8.rs:628) is exercised without any rejection path, unlike the `DEVICE | EXECUTE` combination it does reject (vmsav8.rs:671-692). Target: [`docs/architecture/security-model.md`](../../architecture/security-model.md)'s `## Open questions` section (currently ending around line 331).
  - Action: add two bullets to security-model.md's Open Questions list: (1) `AddressSpaceCap`'s kind-only authority check, and (2) the absence of a W^X (`WRITE` ^ `EXECUTE`) guard in `Mmu::map`'s flags validation. Centralizing every known authority-model gap in the document a security reviewer reads first — human or AI — is what turns "correct" into "exemplary" for a project whose stated goal is to be the reference for how a capability kernel documents itself.

Covers all 1 review finding + 7 polish items routed to this phase.
