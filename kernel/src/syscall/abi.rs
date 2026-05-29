//! The syscall register ABI: number decode, argument/return register frames,
//! the dispatch effect, and the value↔register packing helpers.
//!
//! This module instantiates [ADR-0030][adr-0030]'s calling convention (`x8` =
//! number, `x0`–`x5` = arguments, `x0` = status, `x1`–`x7` = payload) and
//! [ADR-0031][adr-0031]'s concrete v1 syscall numbers and per-call layouts. It
//! is **pure, host-testable Rust** — no hardware, no `unsafe`: the trap frame
//! save/restore and the EL0↔EL1 transition live in the BSP trampoline, and the
//! validated user-memory access lives in [`super::user_access`]. Everything
//! here is register *shuffling* over `u64` words, which is exactly what the
//! host ABI tests pin.
//!
//! [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
//! [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md

use crate::cap::CapHandle;
use crate::ipc::{Message, RecvOutcome, SendOutcome};

use super::error::SyscallError;

/// The reserved handle word meaning "no capability" (`Option::<CapHandle>::None`).
///
/// Used for `send`'s transfer-handle argument (`x5`) and `recv`'s
/// transferred-cap return (`x6`). A live [`CapHandle`] packs into the low 48
/// bits (a `u16` index in bits `0..16`, a `u32` generation in bits `16..48`),
/// so bits `48..64` are always clear for a real handle. `u64::MAX` therefore
/// has its top bits set and **can never collide** with a real packed handle —
/// the property [ADR-0031][adr-0031]'s null-handle sentinel note requires.
///
/// [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md
pub const NULL_CAP_HANDLE: u64 = u64::MAX;

/// The v1 syscall set, decoded from the `x8` register, per [ADR-0031][adr-0031].
///
/// [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum SyscallNumber {
    /// `1` — `ipc_send` on an endpoint capability (`SEND`).
    Send,
    /// `2` — `ipc_recv` on an endpoint capability (`RECV`).
    Recv,
    /// `3` — cooperative `task_yield` on the caller's own task.
    TaskYield,
    /// `4` — `task_exit` on the caller's own task (does not return).
    TaskExit,
    /// `5` — `console_write` through a debug-console capability. **Debug-gated**:
    /// [`SyscallNumber::decode`] only recognises it under `debug_assertions`.
    ConsoleWrite,
}

impl SyscallNumber {
    /// Decode the raw `x8` value into a v1 syscall, or `None` if it names no
    /// syscall (number `0` reserved-invalid, any number above the v1 ceiling,
    /// or `console_write`'s number `5` in a **non-debug build**).
    ///
    /// The release **debug-gate** is implemented here as a `cfg!(debug_assertions)`
    /// match guard (the mechanism [ADR-0031][adr-0031] left to T-021): in a
    /// non-debug build, number `5` falls through to `None`, so the dispatcher
    /// returns [`SyscallError::BadSyscallNumber`] and the debug console is
    /// *absent* from the production syscall surface even for a holder of the
    /// debug-console capability. `cfg!` (not `#[cfg]`) keeps the
    /// [`SyscallNumber::ConsoleWrite`] arm compiled and referenced in every
    /// build, so no dead-code arises in release.
    ///
    /// [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md
    #[must_use]
    pub const fn decode(raw: u64) -> Option<Self> {
        match raw {
            1 => Some(Self::Send),
            2 => Some(Self::Recv),
            3 => Some(Self::TaskYield),
            4 => Some(Self::TaskExit),
            // Debug-gate: number 5 is only a syscall in a debug build.
            5 if cfg!(debug_assertions) => Some(Self::ConsoleWrite),
            // 0 (reserved-invalid), out-of-range, and 5-in-release → no syscall.
            _ => None,
        }
    }

    /// The raw `x8` number a userspace stub loads to invoke this syscall — the
    /// inverse of [`SyscallNumber::decode`] for the recognised arms. Pinned by
    /// the host tests so the integers cannot drift from [ADR-0031][adr-0031].
    ///
    /// [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md
    #[must_use]
    pub const fn as_u64(self) -> u64 {
        match self {
            Self::Send => 1,
            Self::Recv => 2,
            Self::TaskYield => 3,
            Self::TaskExit => 4,
            Self::ConsoleWrite => 5,
        }
    }
}

/// The registers a syscall is invoked with: `x8` = number, `x0`–`x5` = args.
///
/// The BSP trampoline reads these from the saved trap frame and hands them to
/// [`super::dispatch::dispatch`]; argument interpretation is syscall-specific
/// per [ADR-0031][adr-0031]. `x6` / `x7` are reserved on entry and not carried.
///
/// [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub struct SyscallArgs {
    /// The syscall number from `x8`.
    pub number: u64,
    /// Argument words `x0`–`x5` (index `0` = `x0`).
    pub args: [u64; 6],
}

/// The registers a syscall returns: `x0` = status, `x1`–`x7` = payload.
///
/// `status` is `0` ([`super::error::OK_STATUS`]) on success or a
/// [`SyscallError::as_status`] code otherwise; `payload[i]` maps to register
/// `x{i + 1}`. v1 uses at most `payload[0..6]` (`x1`–`x6`, for `recv`).
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub struct SyscallReturn {
    /// The status word written to `x0`.
    pub status: u64,
    /// Payload words `x1`–`x7` (index `0` = `x1`).
    pub payload: [u64; 7],
}

impl SyscallReturn {
    /// A successful return with a zeroed payload (`x0 = 0`, `x1`–`x7 = 0`).
    #[must_use]
    pub const fn ok() -> Self {
        Self {
            status: super::error::OK_STATUS,
            payload: [0; 7],
        }
    }

    /// A failure return carrying `e`'s stable status in `x0` and a zeroed
    /// payload (the payload registers are undefined on error per
    /// [ADR-0030][adr-0030]; zeroing them is deterministic and leaks nothing).
    ///
    /// [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
    #[must_use]
    pub const fn error(e: SyscallError) -> Self {
        Self {
            status: e.as_status(),
            payload: [0; 7],
        }
    }

    /// Set payload word `x{IDX + 1}` to `val`, returning the updated frame.
    ///
    /// `IDX` is a **const generic** bounded to `0..7` (the seven payload
    /// registers `x1`–`x7`) by the `const { assert!(IDX < 7) }` below: an
    /// out-of-range index is a **compile error at the call site**, not a
    /// runtime panic — so this builder cannot panic on any input, matching the
    /// kernel's compile-time-guard discipline (cf. `SchedQueue::new`'s
    /// `const { assert!(N > 0) }` and the `SyscallTrapFrame` `size_of` guard).
    /// Every caller passes a literal `::<N>`, so the indexing is provably
    /// in-bounds. (Closes the T-021 review-round nit on unchecked indexing.)
    #[must_use]
    pub const fn with_payload<const IDX: usize>(mut self, val: u64) -> Self {
        const { assert!(IDX < 7, "SyscallReturn payload index must be < 7 (x1..x7)") };
        self.payload[IDX] = val;
        self
    }
}

/// What the dispatcher decided the trampoline should do after a syscall.
///
/// The data-plane syscalls (`send` / `recv` / `console_write`) complete inside
/// the dispatcher and produce [`SyscallEffect::Resume`]. The two control-plane
/// syscalls return a *directive* the BSP glue acts on, because they touch the
/// scheduler — which is raw-pointer-wired per [ADR-0021][adr-0021] and lives
/// outside the dispatcher's pure data-plane surface. Keeping them as directives
/// keeps the dispatcher host-testable without a live scheduler.
///
/// [adr-0021]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0021-raw-pointer-scheduler-ipc-bridge.md
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum SyscallEffect {
    /// Write these registers into the trap frame and `ERET` back to the caller.
    Resume(SyscallReturn),
    /// `task_yield` (number `3`): the caller should run the cooperative
    /// scheduler yield, then resume with status `Ok`. v1's BSP glue treats
    /// this as plumbing — the real `yield_now` wiring lands in B6 when the
    /// caller is a real EL0 scheduler task (ADR-0031).
    Reschedule,
    /// `task_exit` (number `4`) with the caller's exit code: terminate the
    /// calling task; control does not return to it. v1's BSP glue is a
    /// kernel-stub stand-in — real EL0-task termination lands in B6 once an
    /// EL0 context register file exists (ADR-0031).
    Terminate(u64),
}

// ── Capability-handle packing ─────────────────────────────────────────────────

/// Pack an optional capability handle into a single register word.
///
/// `None` becomes the [`NULL_CAP_HANDLE`] sentinel; `Some(h)` packs the
/// generation into bits `16..48` and the index into bits `0..16`. Used for
/// `send`'s transfer handle and `recv`'s transferred-cap return.
#[must_use]
pub const fn encode_cap_handle(handle: Option<CapHandle>) -> u64 {
    match handle {
        None => NULL_CAP_HANDLE,
        Some(h) => ((h.generation() as u64) << 16) | (h.index() as u64),
    }
}

/// Unpack a register word into an optional capability handle.
///
/// The [`NULL_CAP_HANDLE`] sentinel decodes to `None`; any other word decodes
/// to `Some(handle)` by splitting the low 48 bits into `(index, generation)`.
/// The reconstructed handle is **not trusted** — [`crate::cap::CapabilityTable::lookup`]
/// validates it against the live slot's generation, so a malformed or stale
/// word simply fails lookup (see [`CapHandle::from_raw`]).
#[must_use]
#[allow(
    clippy::cast_possible_truncation,
    reason = "intentional ABI unpack: `word as u16` takes the index bits 0..16; \
              `(word >> 16) as u32` takes the generation bits 16..48"
)]
pub const fn decode_cap_handle(word: u64) -> Option<CapHandle> {
    if word == NULL_CAP_HANDLE {
        None
    } else {
        let index = word as u16;
        let generation = (word >> 16) as u32;
        Some(CapHandle::from_raw(index, generation))
    }
}

/// Unpack a register word as a **required** capability handle (no `None` case).
///
/// Used for arguments that always name a real object — `send` / `recv`'s
/// endpoint handle (`x0`) and `console_write`'s debug-console handle (`x0`).
/// A caller that passes the [`NULL_CAP_HANDLE`] sentinel (or any garbage) gets
/// a handle that fails [`crate::cap::CapabilityTable::lookup`]: the sentinel's
/// `index == 0xFFFF` is far past any table's capacity, so it resolves to
/// `InvalidHandle` rather than aliasing a live slot.
#[must_use]
#[allow(
    clippy::cast_possible_truncation,
    reason = "intentional ABI unpack: `word as u16` takes the index bits 0..16; \
              `(word >> 16) as u32` takes the generation bits 16..48"
)]
pub const fn decode_required_cap_handle(word: u64) -> CapHandle {
    let index = word as u16;
    let generation = (word >> 16) as u32;
    CapHandle::from_raw(index, generation)
}

// ── Outcome packing ────────────────────────────────────────────────────────────

/// `send`'s `x1` payload code for [`SendOutcome::Delivered`].
pub const SEND_OUTCOME_DELIVERED: u64 = 0;
/// `send`'s `x1` payload code for [`SendOutcome::Enqueued`].
pub const SEND_OUTCOME_ENQUEUED: u64 = 1;
/// `recv`'s `x1` payload code for a message having been received.
pub const RECV_OUTCOME_RECEIVED: u64 = 0;
/// `recv`'s `x1` payload code for no sender being ready (receiver registered).
pub const RECV_OUTCOME_PENDING: u64 = 1;

/// Encode a [`SendOutcome`] into `send`'s `x1` payload word.
#[must_use]
pub const fn encode_send_outcome(outcome: SendOutcome) -> u64 {
    match outcome {
        SendOutcome::Delivered => SEND_OUTCOME_DELIVERED,
        SendOutcome::Enqueued => SEND_OUTCOME_ENQUEUED,
    }
}

/// Encode a successful [`RecvOutcome`] into `recv`'s return registers.
///
/// Layout per [ADR-0031][adr-0031]: `x1` = outcome code, `x2` = `msg.label`,
/// `x3`–`x5` = `msg.params[0..3]`, `x6` = transferred cap handle (or the
/// [`NULL_CAP_HANDLE`] sentinel). `Pending` carries no message: `x1` = pending
/// code and `x2`–`x6` are zeroed (deterministic; the ABI leaves them undefined).
///
/// [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md
#[must_use]
pub const fn encode_recv_outcome(outcome: RecvOutcome) -> SyscallReturn {
    match outcome {
        RecvOutcome::Received { msg, cap } => SyscallReturn::ok()
            .with_payload::<0>(RECV_OUTCOME_RECEIVED) // x1
            .with_payload::<1>(msg.label) // x2
            .with_payload::<2>(msg.params[0]) // x3
            .with_payload::<3>(msg.params[1]) // x4
            .with_payload::<4>(msg.params[2]) // x5
            .with_payload::<5>(encode_cap_handle(cap)), // x6
        RecvOutcome::Pending => SyscallReturn::ok().with_payload::<0>(RECV_OUTCOME_PENDING),
    }
}

/// Decode the four-word [`Message`] body `send` carries in `x1`–`x4`.
///
/// `args` is the full `x0`–`x5` argument array; the message is `x1` = label,
/// `x2`–`x4` = params. (The endpoint handle in `x0` and the transfer handle in
/// `x5` are decoded separately by the dispatcher.)
#[must_use]
pub const fn decode_send_message(args: [u64; 6]) -> Message {
    Message {
        label: args[1],
        params: [args[2], args[3], args[4]],
    }
}

#[cfg(test)]
#[allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    reason = "tests may use pragmas forbidden in production kernel code"
)]
mod tests {
    use super::{
        decode_cap_handle, decode_required_cap_handle, decode_send_message, encode_cap_handle,
        encode_recv_outcome, encode_send_outcome, SyscallNumber, SyscallReturn, NULL_CAP_HANDLE,
        RECV_OUTCOME_PENDING, RECV_OUTCOME_RECEIVED, SEND_OUTCOME_DELIVERED, SEND_OUTCOME_ENQUEUED,
    };
    use crate::cap::CapHandle;
    use crate::ipc::{Message, RecvOutcome, SendOutcome};

    // ── number decode ────────────────────────────────────────────────────────

    #[test]
    fn decode_maps_v1_numbers() {
        assert_eq!(SyscallNumber::decode(1), Some(SyscallNumber::Send));
        assert_eq!(SyscallNumber::decode(2), Some(SyscallNumber::Recv));
        assert_eq!(SyscallNumber::decode(3), Some(SyscallNumber::TaskYield));
        assert_eq!(SyscallNumber::decode(4), Some(SyscallNumber::TaskExit));
    }

    #[test]
    fn decode_zero_is_reserved_invalid() {
        // Number 0 must never name a syscall — an uninitialised x8 faults.
        assert_eq!(SyscallNumber::decode(0), None);
    }

    #[test]
    fn decode_out_of_range_is_none() {
        assert_eq!(SyscallNumber::decode(6), None);
        assert_eq!(SyscallNumber::decode(99), None);
        assert_eq!(SyscallNumber::decode(u64::MAX), None);
    }

    #[test]
    fn as_u64_round_trips_recognised_numbers() {
        for n in [
            SyscallNumber::Send,
            SyscallNumber::Recv,
            SyscallNumber::TaskYield,
            SyscallNumber::TaskExit,
        ] {
            assert_eq!(SyscallNumber::decode(n.as_u64()), Some(n));
        }
        // console_write's number round-trips only where it is a syscall.
        assert_eq!(SyscallNumber::ConsoleWrite.as_u64(), 5);
    }

    #[test]
    #[cfg(debug_assertions)]
    fn console_write_is_a_syscall_in_debug_builds() {
        assert_eq!(SyscallNumber::decode(5), Some(SyscallNumber::ConsoleWrite));
    }

    #[test]
    #[cfg(not(debug_assertions))]
    fn console_write_is_absent_in_release_builds() {
        // The release debug-gate: number 5 names no syscall, so the dispatcher
        // returns BadSyscallNumber even for a debug-console capability holder.
        assert_eq!(SyscallNumber::decode(5), None);
    }

    // ── capability-handle packing ────────────────────────────────────────────

    #[test]
    fn none_round_trips_through_null_sentinel() {
        assert_eq!(encode_cap_handle(None), NULL_CAP_HANDLE);
        assert_eq!(decode_cap_handle(NULL_CAP_HANDLE), None);
    }

    #[test]
    fn some_handle_round_trips() {
        let h = CapHandle::from_raw(0x1234, 0xDEAD_BEEF);
        let word = encode_cap_handle(Some(h));
        // Top 16 bits stay clear, so the sentinel can never collide.
        assert_eq!(word >> 48, 0);
        let decoded = decode_cap_handle(word).expect("non-sentinel word decodes to Some");
        assert_eq!(decoded.index(), 0x1234);
        assert_eq!(decoded.generation(), 0xDEAD_BEEF);
    }

    #[test]
    fn required_handle_decode_ignores_sentinel_semantics() {
        // A required-handle slot never means "none"; decoding the sentinel
        // yields an out-of-range handle (index 0xFFFF) that fails lookup.
        let h = decode_required_cap_handle(NULL_CAP_HANDLE);
        assert_eq!(h.index(), 0xFFFF);
        assert_eq!(h.generation(), 0xFFFF_FFFF);
    }

    // ── outcome packing ──────────────────────────────────────────────────────

    #[test]
    fn send_outcome_codes() {
        assert_eq!(
            encode_send_outcome(SendOutcome::Delivered),
            SEND_OUTCOME_DELIVERED
        );
        assert_eq!(
            encode_send_outcome(SendOutcome::Enqueued),
            SEND_OUTCOME_ENQUEUED
        );
    }

    #[test]
    fn recv_received_packs_message_and_cap() {
        let msg = Message {
            label: 0xAA,
            params: [0xB0, 0xB1, 0xB2],
        };
        let cap = CapHandle::from_raw(7, 3);
        let r = encode_recv_outcome(RecvOutcome::Received {
            msg,
            cap: Some(cap),
        });
        assert_eq!(r.status, 0);
        assert_eq!(r.payload[0], RECV_OUTCOME_RECEIVED); // x1
        assert_eq!(r.payload[1], 0xAA); // x2 label
        assert_eq!(r.payload[2], 0xB0); // x3 param0
        assert_eq!(r.payload[3], 0xB1); // x4 param1
        assert_eq!(r.payload[4], 0xB2); // x5 param2
        assert_eq!(decode_cap_handle(r.payload[5]), Some(cap)); // x6 cap
    }

    #[test]
    fn recv_received_without_cap_packs_null_sentinel() {
        let msg = Message::default();
        let r = encode_recv_outcome(RecvOutcome::Received { msg, cap: None });
        assert_eq!(r.payload[0], RECV_OUTCOME_RECEIVED);
        assert_eq!(r.payload[5], NULL_CAP_HANDLE);
        assert_eq!(decode_cap_handle(r.payload[5]), None);
    }

    #[test]
    fn recv_pending_packs_pending_code_and_zeroes_rest() {
        let r = encode_recv_outcome(RecvOutcome::Pending);
        assert_eq!(r.status, 0);
        assert_eq!(r.payload[0], RECV_OUTCOME_PENDING);
        // x2..x7 zeroed for determinism.
        assert_eq!(&r.payload[1..], &[0, 0, 0, 0, 0, 0]);
    }

    #[test]
    fn decode_send_message_reads_label_and_params() {
        let args = [0xEEEE, 0x11, 0x22, 0x33, 0x44, NULL_CAP_HANDLE];
        let msg = decode_send_message(args);
        assert_eq!(msg.label, 0x11); // x1
        assert_eq!(msg.params, [0x22, 0x33, 0x44]); // x2..x4
    }

    #[test]
    fn syscall_return_with_payload_sets_indexed_word() {
        let r = SyscallReturn::ok().with_payload::<2>(0x99);
        assert_eq!(r.payload[2], 0x99);
        assert_eq!(r.status, 0);
        // Builder chains compose; each `::<IDX>` is a compile-time-bounded index
        // (an out-of-range `::<7>` would fail to compile, not panic).
        let r2 = SyscallReturn::ok()
            .with_payload::<0>(0x11)
            .with_payload::<6>(0x77);
        assert_eq!(r2.payload[0], 0x11);
        assert_eq!(r2.payload[6], 0x77);
    }
}
