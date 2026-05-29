//! Syscall subsystem — the EL0→EL1 boundary's kernel-side half (Phase B5 / [T-021]).
//!
//! This module is the **architecture-agnostic, panic-free, host-testable** core
//! of the syscall path: it decodes the register ABI, validates the caller's
//! capabilities, performs each operation through an existing kernel primitive,
//! and encodes a typed result. It owns no hardware — the `SVC` trap trampoline,
//! the register save/restore frame, and the EL0↔EL1 transition live in the BSP
//! (`bsp-qemu-virt/src/vectors.s` + `syscall.rs`), which builds a
//! [`SyscallContext`] from its statics and calls [`dispatch`].
//!
//! It instantiates two Accepted ADRs:
//!
//! - [ADR-0030][adr-0030] — the calling convention (`x8` = number, `x0`–`x5` =
//!   arguments, `x0` = status, `x1`–`x7` = payload, `SVC #0`) and the
//!   [`error::SyscallError`] space that composes [`crate::cap::CapError`] /
//!   [`crate::ipc::IpcError`].
//! - [ADR-0031][adr-0031] — the five-syscall v1 set (`send` / `recv` /
//!   `task_yield` / `task_exit` / `console_write`), number `0` reserved-invalid,
//!   every object-naming syscall capability-gated ([P1 / P4][principles]).
//!
//! ## Module layout
//!
//! - [`error`] — [`SyscallError`] + `From<CapError>` / `From<IpcError>` + the
//!   stable numeric status encoding ([`SyscallError::as_status`]).
//! - [`abi`] — the register frame types ([`SyscallArgs`] / [`SyscallReturn`] /
//!   [`SyscallEffect`]), the [`SyscallNumber`] decode (with the release
//!   debug-gate), and the value↔register packing (`Message`, outcomes,
//!   `Option<CapHandle>` with the null sentinel).
//! - [`user_access`] — [`UserAccessWindow`] + [`copy_from_user`] /
//!   [`copy_to_user`]: validated, never-raw-deref access to user memory.
//! - [`dispatch`] — the [`dispatch`] entry point + the per-syscall handlers +
//!   the debug-console capability check.
//!
//! [T-021]: https://github.com/HodeTech/Tyrne/blob/main/docs/analysis/tasks/phase-b/T-021-syscall-dispatch.md
//! [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
//! [adr-0031]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0031-initial-syscall-set.md
//! [principles]: https://github.com/HodeTech/Tyrne/blob/main/docs/standards/architectural-principles.md

pub mod abi;
pub mod dispatch;
pub mod error;
pub mod user_access;

pub use abi::{
    decode_cap_handle, decode_required_cap_handle, decode_send_message, encode_cap_handle,
    encode_recv_outcome, encode_send_outcome, SyscallArgs, SyscallEffect, SyscallNumber,
    SyscallReturn, NULL_CAP_HANDLE, RECV_OUTCOME_PENDING, RECV_OUTCOME_RECEIVED,
    SEND_OUTCOME_DELIVERED, SEND_OUTCOME_ENQUEUED,
};
pub use dispatch::{dispatch, SyscallContext};
pub use error::{SyscallError, OK_STATUS};
pub use user_access::{copy_from_user, copy_to_user, UserAccessWindow};
