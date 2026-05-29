//! Capability subsystem.
//!
//! Every privileged action in Tyrne requires the caller to hold a
//! capability that authorizes it. A capability is an unforgeable,
//! move-only kernel-held token, referenced from userspace (eventually)
//! and from the kernel's own code (now) through an opaque handle.
//!
//! The representation — index-based arena, generation-tagged handles,
//! explicit derivation tree, cascading revocation — is pinned in
//! [ADR-0014][adr-0014]. The architectural role of capabilities lives in
//! [`security-model.md`][sec] and [architectural principle P1][p1].
//!
//! [adr-0014]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0014-capability-representation.md
//! [adr-0016]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0016-kernel-object-storage.md
//! [sec]: https://github.com/HodeTech/Tyrne/blob/main/docs/architecture/security-model.md
//! [p1]: https://github.com/HodeTech/Tyrne/blob/main/docs/standards/architectural-principles.md#p1--no-ambient-authority
//!
//! ## Status (T-001 + T-002)
//!
//! - [`Capability`] is move-only (not `Copy`, not `Clone`).
//! - [`CapRights`] carries the table-management rights (`DUPLICATE`,
//!   `DERIVE`, `REVOKE`, `TRANSFER`) plus the IPC rights that landed
//!   with their subsystems (`SEND`, `RECV`, `NOTIFY`); reserved bits are
//!   masked away by [`CapRights::from_raw`] at the future ABI boundary.
//! - [`CapObject`] is a typed enum that names a kernel object by its
//!   typed handle — [`super::obj::TaskHandle`] / [`super::obj::EndpointHandle`]
//!   / [`super::obj::NotificationHandle`] / [`super::mm::AddressSpaceHandle`]
//!   — following [ADR-0016][adr-0016]. `MemoryRegion` arrives in Phase B4+.
//! - [`CapabilityTable`] implements
//!   [`cap_copy`][CapabilityTable::cap_copy],
//!   [`cap_derive`][CapabilityTable::cap_derive],
//!   [`cap_revoke`][CapabilityTable::cap_revoke], and
//!   [`cap_drop`][CapabilityTable::cap_drop] with zero `unsafe`.
//!
//! What v1 deliberately omits: IPC integration, multi-core safety,
//! persistent capabilities, badge schemes. Each has a named open question
//! in [ADR-0014][adr-0014] or a later ADR.

mod rights;
mod table;

pub use rights::CapRights;
pub use table::{CapHandle, CapabilityTable, CAP_TABLE_CAPACITY, MAX_DERIVATION_DEPTH};

use crate::mm::AddressSpaceHandle;
use crate::obj::{EndpointHandle, NotificationHandle, TaskHandle};

/// Kinds of kernel object a capability can refer to.
///
/// The discriminator for a capability's [`CapObject`]; `CapObject`
/// carries the actual typed handle. `MemoryRegion` is reserved here but
/// has no `CapObject` variant until Phase B's B4+ work introduces
/// frame-ownership semantics; `AddressSpace` was added in T-018 with
/// the live [`AddressSpace`][crate::mm::AddressSpace] kernel-object
/// landing per [ADR-0028][adr-0028].
///
/// [adr-0028]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0028-address-space-data-structure.md
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum CapKind {
    /// Refers to a task kernel object.
    Task,
    /// Refers to an IPC endpoint kernel object.
    Endpoint,
    /// Refers to an asynchronous notification kernel object.
    Notification,
    /// Refers to an address-space kernel object (per
    /// [ADR-0028][adr-0028]; T-018 commit 2). The
    /// [`CapObject::AddressSpace`] variant carries the typed
    /// [`AddressSpaceHandle`].
    ///
    /// [adr-0028]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0028-address-space-data-structure.md
    AddressSpace,
    /// Refers to a physical memory region (Phase B4+).
    MemoryRegion,
}

/// Typed reference to a kernel object.
///
/// Each variant carries the [typed handle][crate::obj] of its kind, so
/// passing a `TaskHandle` where an `EndpointHandle` is expected is a
/// compile-time error. The discriminator matches [`CapKind`] one-to-one
/// for every kind that has live kernel-object storage; `MemoryRegion`
/// is in `CapKind` but has no `CapObject` variant until Phase B4+
/// introduces frame-ownership semantics. `AddressSpace` landed with
/// T-018 (per [ADR-0028][adr-0028]).
///
/// [adr-0028]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0028-address-space-data-structure.md
///
/// `Debug` is a **hand-written, redacting** impl (not derived): it prints the
/// object *kind* but redacts the wrapped typed handle (slot index +
/// generation). This is the same kernel-internal-identity hazard the
/// [`Capability`] redaction (K3-9 / [ADR-0030][adr-0030cap]) addresses —
/// closed here at the source so a `CapObject` formatted directly (e.g. into a
/// future error or a userspace-reachable log) cannot leak the handle either.
///
/// [adr-0030cap]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
#[derive(Copy, Clone, Eq, PartialEq)]
pub enum CapObject {
    /// Capability naming a [`Task`][crate::obj::Task] kernel object.
    Task(TaskHandle),
    /// Capability naming an [`Endpoint`][crate::obj::Endpoint] kernel object.
    Endpoint(EndpointHandle),
    /// Capability naming a [`Notification`][crate::obj::Notification] kernel object.
    Notification(NotificationHandle),
    /// Capability naming an [`AddressSpace`][crate::mm::AddressSpace]
    /// kernel object (per [ADR-0028][adr-0028]; T-018 commit 2).
    ///
    /// [adr-0028]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0028-address-space-data-structure.md
    AddressSpace(AddressSpaceHandle),
}

impl CapObject {
    /// Return the [`CapKind`] discriminator matching this object.
    #[must_use]
    pub const fn kind(self) -> CapKind {
        match self {
            Self::Task(_) => CapKind::Task,
            Self::Endpoint(_) => CapKind::Endpoint,
            Self::Notification(_) => CapKind::Notification,
            Self::AddressSpace(_) => CapKind::AddressSpace,
        }
    }
}

impl core::fmt::Debug for CapObject {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        // Show the kind (benign, useful for diagnostics) but redact the
        // wrapped typed handle (slot index + generation) — kernel-internal
        // identity per K3-9 / ADR-0030. The wrapped handle types keep their
        // derived `Debug` for kernel-internal traces (scheduler, arena) where
        // the slot/generation is the useful information and never crosses to
        // userspace; `CapObject` is redacted because it is the type a
        // capability (or a future error) carries toward a log boundary.
        f.debug_struct("CapObject")
            .field("kind", &self.kind())
            .finish()
    }
}

/// A capability.
///
/// Deliberately **not** `Copy` and **not** `Clone`. Duplication happens
/// only through [`CapabilityTable::cap_copy`], which requires the caller
/// to hold the [`CapRights::DUPLICATE`] authority on the source. The
/// Rust type system enforces the move-only discipline by construction.
///
/// `Debug` is a **hand-written, redacting** impl (not derived): it prints
/// the `rights` (authority bits — useful for diagnostics and not
/// unforgeable) but redacts the named object as `<redacted>`. The object
/// names a kernel object by typed handle (slot index + generation), which
/// is kernel-internal identity that must never leak across a
/// userspace-reachable log path such as the future `console_write` syscall.
/// Per [ADR-0030][adr-0030] §"Security of the taxonomy split" and B5
/// sub-item 6 (K3-9 — security review §6).
///
/// [adr-0030]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0030-syscall-abi.md
pub struct Capability {
    rights: CapRights,
    object: CapObject,
}

impl core::fmt::Debug for Capability {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        // Redact the named object; keep rights visible. `format_args!`
        // (rather than a `&str`) emits the placeholder without surrounding
        // quotes, so the output reads `object: <redacted>`, not
        // `object: "<redacted>"`.
        f.debug_struct("Capability")
            .field("rights", &self.rights)
            .field("object", &format_args!("<redacted>"))
            .finish()
    }
}

impl Capability {
    /// Construct a capability with the given rights over `object`. The
    /// [`CapKind`] is derived from the `object`'s variant, so
    /// kind-and-object cannot disagree by construction.
    #[must_use]
    pub const fn new(rights: CapRights, object: CapObject) -> Self {
        Self { rights, object }
    }

    /// Return the capability's kind, derived from its object variant.
    #[must_use]
    pub const fn kind(&self) -> CapKind {
        self.object.kind()
    }

    /// Return the capability's rights.
    #[must_use]
    pub const fn rights(&self) -> CapRights {
        self.rights
    }

    /// Return the capability's typed object reference.
    #[must_use]
    pub const fn object(&self) -> CapObject {
        self.object
    }
}

/// Errors returned by capability-table operations.
///
/// `#[non_exhaustive]` so that future additions (introduced by later
/// ADRs as new operations land) are not breaking changes.
#[non_exhaustive]
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum CapError {
    /// The capability table is full; no free slot.
    CapsExhausted,
    /// The handle does not refer to a currently-allocated slot, either
    /// because the slot is free or because the handle's generation is
    /// stale (the slot was freed and reused or revoked).
    InvalidHandle,
    /// `cap_copy` or `cap_derive` was asked to grant rights the source
    /// capability does not itself hold.
    WidenedRights,
    /// The caller's rights on the source capability do not include the
    /// authority required for the operation (for example, `DUPLICATE` for
    /// `cap_copy`, `DERIVE` for `cap_derive`, `REVOKE` for `cap_revoke`).
    InsufficientRights,
    /// `cap_derive` would produce a capability whose depth exceeds
    /// [`MAX_DERIVATION_DEPTH`].
    DerivationTooDeep,
    /// `cap_drop` was called on a capability that still has descendants.
    /// The caller must `cap_revoke` the subtree first so orphaned
    /// children cannot outlive their parent.
    HasChildren,
    /// The capability's [`CapKind`] is not the one the operation
    /// requires. Used by typed resolution helpers (e.g.,
    /// `resolve_address_space_cap` in T-018 commit 3) when a caller
    /// hands a wrong-kind capability to an operation that has a
    /// specific kind contract — `cap_map(endpoint_cap, ...)` returns
    /// `CapError::WrongKind` via the wrapper's
    /// `AddressSpaceError::CapError(_)` passthrough.
    WrongKind,
}

#[cfg(test)]
mod tests {
    use super::{CapObject, CapRights, Capability};
    use crate::obj::TaskHandle;

    #[test]
    fn debug_redacts_named_object_but_keeps_rights() {
        // K3-9 (ADR-0030 §"Security of the taxonomy split"): a `Capability`'s
        // `Debug` must not leak the kernel object it names — no kind, no slot
        // index, no generation — but may show the (non-unforgeable) rights.
        let cap = Capability::new(
            CapRights::SEND | CapRights::RECV,
            CapObject::Task(TaskHandle::test_handle(0xAB, 7)),
        );
        let shown = format!("{cap:?}");

        // The named object is redacted.
        assert!(
            shown.contains("object: <redacted>"),
            "object must be redacted, got: {shown}"
        );
        assert!(
            !shown.contains("Task"),
            "object kind must not leak, got: {shown}"
        );
        assert!(
            !shown.contains("171"),
            "handle index (0xAB = 171) must not leak, got: {shown}"
        );
        // Rights stay visible for diagnostics (`CapRights` derives `Debug`).
        assert!(
            shown.contains("rights"),
            "rights field must be shown, got: {shown}"
        );
    }

    #[test]
    fn capobject_debug_redacts_handle_but_shows_kind() {
        // Defense-in-depth: even formatting a bare `CapObject` (not wrapped in
        // a `Capability`) must not leak the handle's slot index / generation.
        let obj = CapObject::Task(TaskHandle::test_handle(0xAB, 7));
        let shown = format!("{obj:?}");

        // The kind is shown (benign, useful for diagnostics)...
        assert!(shown.contains("Task"), "kind should be shown, got: {shown}");
        // ...but the wrapped handle's identity is redacted.
        assert!(
            !shown.contains("171"),
            "handle index (0xAB = 171) must not leak, got: {shown}"
        );
        assert!(
            !shown.contains("SlotId") && !shown.contains("generation"),
            "handle internals must not leak, got: {shown}"
        );
    }
}
