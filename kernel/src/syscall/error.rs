//! The userspace-facing syscall error space, [`SyscallError`].
//!
//! Per [ADR-0030][adr-0030], a syscall returns a **status word** in `x0`: `0`
//! means `Ok` (the payload registers carry the result), any non-zero value is
//! a stable [`SyscallError`] discriminant. `SyscallError` **composes** from the
//! in-kernel error spaces ([`CapError`] and [`IpcError`]) via `From` impls per
//! the [error-handling standard §7 "preserve root cause"][err] — the dispatcher
//! never collapses a distinct cap/IPC failure into a generic "internal error".
//!
//! ## Stable numeric status encoding
//!
//! [`SyscallError::as_status`] is the canonical encoder the dispatcher uses to
//! fill `x0`. The integers it produces are a **stable ABI contract** pinned by
//! the host tests in this module; a future `tyrne-user` crate (Phase B6) decodes
//! them. The layout is blocked so the composed spaces stay visually distinct:
//!
//! | Range          | Meaning                                            |
//! |----------------|----------------------------------------------------|
//! | `0`            | `Ok` (reserved — never a `SyscallError`)           |
//! | `1`–`3`        | top-level [`SyscallError`] variants                |
//! | `0x101`–`0x1FF`| [`SyscallError::Cap`] — `0x100 \| `[`CapError`] code |
//! | `0x201`–`0x2FF`| [`SyscallError::Ipc`] — `0x200 \| `[`IpcError`] code  |
//!
//! Because [`CapError`] / [`IpcError`] are `#[non_exhaustive]` *but defined in
//! this same crate*, the per-variant encoders below match them **exhaustively
//! without a wildcard** — adding a variant to either is a compile error here
//! until its stable code is assigned, which is exactly the safeguard a stable
//! ABI wants.
//!
//! [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
//! [err]: https://github.com/HodeTech/Tyrne/blob/main/docs/standards/error-handling.md

use crate::cap::CapError;
use crate::ipc::IpcError;

/// The status word value reserved for a successful syscall (`x0 == 0`).
///
/// Userspace branches structurally on this single value: `x0 == OK_STATUS`
/// means "read the payload from `x1`–`x7`", any other value is a
/// [`SyscallError`] discriminant. Fixed by [ADR-0030][adr-0030].
///
/// [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
pub const OK_STATUS: u64 = 0;

/// High bit-block of a [`SyscallError::Cap`] status code (`0x100 | cap_code`).
const CAP_STATUS_BASE: u64 = 0x100;
/// High bit-block of a [`SyscallError::Ipc`] status code (`0x200 | ipc_code`).
const IPC_STATUS_BASE: u64 = 0x200;

/// The error half of a syscall's `Result`-shaped return, per [ADR-0030][adr-0030].
///
/// `#[non_exhaustive]` so address-space / loader variants can land additively
/// with their first syscall consumer (Phase B6+) without a breaking change. The
/// `Cap` / `Ipc` variants **compose** the in-kernel error spaces rather than
/// re-inventing a parallel flat space, keeping the userspace-facing and
/// in-kernel taxonomies in agreement (the K2-5 motivation in [ADR-0030][adr-0030]).
///
/// [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
#[non_exhaustive]
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum SyscallError {
    /// `x8` named no syscall in the v1 set — number `0` (reserved-invalid), a
    /// number above the v1 ceiling, or a debug-gated number (`console_write`)
    /// in a non-debug build. See [ADR-0031][adr-0031].
    ///
    /// [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md
    BadSyscallNumber,
    /// An argument was structurally invalid in a way the syscall could detect
    /// before performing its operation (reserved for future v1 syscalls that
    /// validate argument shape; no v1 producer today).
    BadArgument,
    /// A user pointer (or `[ptr, ptr + len)` range) fell outside the active
    /// address space's accessible region, or the range wrapped past
    /// `usize::MAX`. Produced by `copy_from_user` / `copy_to_user`; the kernel
    /// never dereferenced the pointer.
    FaultAddress,
    /// A capability-table failure, composed from [`CapError`] via [`From`].
    /// Carries the exact cap-side variant (e.g. a `console_write` debug-console
    /// capability that is stale / wrong-kind / lacks `CONSOLE_WRITE`).
    Cap(CapError),
    /// An IPC failure, composed from [`IpcError`] via [`From`]. Carries the
    /// exact IPC-side variant (`StaleHandle` / `WrongObjectKind` /
    /// `MissingRight` / ...) for `send` / `recv`.
    Ipc(IpcError),
}

impl SyscallError {
    /// Encode this error as the stable non-zero `x0` status word.
    ///
    /// The inverse of the conceptual `tyrne-user` decoder (Phase B6). Never
    /// returns [`OK_STATUS`] (`0`) — that value is reserved for success. The
    /// concrete integers are the stable ABI contract pinned by this module's
    /// host tests; see the module-level table.
    #[must_use]
    pub const fn as_status(self) -> u64 {
        match self {
            Self::BadSyscallNumber => 1,
            Self::BadArgument => 2,
            Self::FaultAddress => 3,
            Self::Cap(e) => CAP_STATUS_BASE | cap_error_code(e),
            Self::Ipc(e) => IPC_STATUS_BASE | ipc_error_code(e),
        }
    }
}

impl From<CapError> for SyscallError {
    fn from(e: CapError) -> Self {
        Self::Cap(e)
    }
}

impl From<IpcError> for SyscallError {
    fn from(e: IpcError) -> Self {
        Self::Ipc(e)
    }
}

/// Stable per-variant code for [`CapError`], OR-ed into [`CAP_STATUS_BASE`].
///
/// Exhaustive without a wildcard (same crate): a new [`CapError`] variant
/// breaks the build here until it is assigned a code — the intended ABI guard.
const fn cap_error_code(e: CapError) -> u64 {
    match e {
        CapError::CapsExhausted => 1,
        CapError::InvalidHandle => 2,
        CapError::WidenedRights => 3,
        CapError::InsufficientRights => 4,
        CapError::DerivationTooDeep => 5,
        CapError::HasChildren => 6,
        CapError::WrongKind => 7,
    }
}

/// Stable per-variant code for [`IpcError`], OR-ed into [`IPC_STATUS_BASE`].
///
/// Exhaustive without a wildcard (same crate): a new [`IpcError`] variant
/// breaks the build here until it is assigned a code — the intended ABI guard.
const fn ipc_error_code(e: IpcError) -> u64 {
    match e {
        IpcError::StaleHandle => 1,
        IpcError::WrongObjectKind => 2,
        IpcError::MissingRight => 3,
        IpcError::QueueFull => 4,
        IpcError::InvalidTransferCap => 5,
        IpcError::ReceiverTableFull => 6,
        IpcError::PendingAfterResume => 7,
    }
}

#[cfg(test)]
mod tests {
    use super::{SyscallError, OK_STATUS};
    use crate::cap::CapError;
    use crate::ipc::IpcError;

    #[test]
    fn ok_status_is_zero_and_no_error_encodes_to_it() {
        assert_eq!(OK_STATUS, 0);
        // Every error must encode to a non-zero status; `0` is reserved for Ok.
        let all = [
            SyscallError::BadSyscallNumber,
            SyscallError::BadArgument,
            SyscallError::FaultAddress,
            SyscallError::Cap(CapError::InvalidHandle),
            SyscallError::Ipc(IpcError::StaleHandle),
        ];
        for e in all {
            assert_ne!(e.as_status(), OK_STATUS, "{e:?} must not encode to Ok");
        }
    }

    #[test]
    fn top_level_status_codes_are_stable() {
        assert_eq!(SyscallError::BadSyscallNumber.as_status(), 1);
        assert_eq!(SyscallError::BadArgument.as_status(), 2);
        assert_eq!(SyscallError::FaultAddress.as_status(), 3);
    }

    #[test]
    fn cap_error_from_round_trips_and_encodes_in_cap_block() {
        // `From<CapError>` preserves the root cause (no flattening).
        assert_eq!(
            SyscallError::from(CapError::WrongKind),
            SyscallError::Cap(CapError::WrongKind)
        );
        // Stable codes in the 0x100 block.
        assert_eq!(
            SyscallError::Cap(CapError::CapsExhausted).as_status(),
            0x101
        );
        assert_eq!(
            SyscallError::Cap(CapError::InvalidHandle).as_status(),
            0x102
        );
        assert_eq!(
            SyscallError::Cap(CapError::WidenedRights).as_status(),
            0x103
        );
        assert_eq!(
            SyscallError::Cap(CapError::InsufficientRights).as_status(),
            0x104
        );
        assert_eq!(
            SyscallError::Cap(CapError::DerivationTooDeep).as_status(),
            0x105
        );
        assert_eq!(SyscallError::Cap(CapError::HasChildren).as_status(), 0x106);
        assert_eq!(SyscallError::Cap(CapError::WrongKind).as_status(), 0x107);
    }

    #[test]
    fn ipc_error_from_round_trips_and_encodes_in_ipc_block() {
        // `From<IpcError>` preserves the root cause (no flattening).
        assert_eq!(
            SyscallError::from(IpcError::MissingRight),
            SyscallError::Ipc(IpcError::MissingRight)
        );
        // Stable codes in the 0x200 block.
        assert_eq!(SyscallError::Ipc(IpcError::StaleHandle).as_status(), 0x201);
        assert_eq!(
            SyscallError::Ipc(IpcError::WrongObjectKind).as_status(),
            0x202
        );
        assert_eq!(SyscallError::Ipc(IpcError::MissingRight).as_status(), 0x203);
        assert_eq!(SyscallError::Ipc(IpcError::QueueFull).as_status(), 0x204);
        assert_eq!(
            SyscallError::Ipc(IpcError::InvalidTransferCap).as_status(),
            0x205
        );
        assert_eq!(
            SyscallError::Ipc(IpcError::ReceiverTableFull).as_status(),
            0x206
        );
        assert_eq!(
            SyscallError::Ipc(IpcError::PendingAfterResume).as_status(),
            0x207
        );
    }

    #[test]
    fn cap_and_ipc_status_blocks_do_not_collide() {
        // The two composed spaces occupy disjoint numeric blocks, so a decoder
        // can route a status to the right sub-space by its high bits.
        let cap = SyscallError::Cap(CapError::WrongKind).as_status();
        let ipc = SyscallError::Ipc(IpcError::WrongObjectKind).as_status();
        assert_ne!(cap, ipc);
        assert_eq!(cap & 0xF00, 0x100);
        assert_eq!(ipc & 0xF00, 0x200);
    }
}
