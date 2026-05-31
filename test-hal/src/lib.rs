//! # tyrne-test-hal
//!
//! Deterministic fake implementations of [`tyrne_hal`] traits for host-side
//! unit tests of [`tyrne_kernel`]. Not intended to run on any real hardware
//! and not linked into any kernel image; this crate exists so that kernel
//! logic can be exercised on a developer's laptop via `cargo test -p
//! tyrne-kernel`.
//!
//! See [ADR-0006][adr-0006] for the crate-layout rationale and
//! [`docs/standards/testing.md`][testing-doc] for the test discipline this
//! supports.
//!
//! [adr-0006]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0006-workspace-layout.md
//! [testing-doc]: https://github.com/HodeTech/Tyrne/blob/main/docs/standards/testing.md
//!
//! ## Status
//!
//! All six accepted HAL traits now have fakes:
//! [`FakeConsole`] (ADR-0007), [`FakeCpu`] (ADR-0008), [`FakeMmu`]
//! (ADR-0009), [`FakeTimer`] (ADR-0010), [`FakeIrqController`] (ADR-0011),
//! and [`FakeContextSwitch`] (ADR-0020).
//!
//! Two failure-injecting [`tyrne_hal::Mmu`] decorators wrap [`FakeMmu`]
//! so kernel rollback tests can exercise the two error variants the flat
//! `FakeMmu` cannot itself produce: [`OutOfFramesMmu`]
//! ([`tyrne_hal::MmuError::OutOfFrames`]) and [`BlockMappedMmu`]
//! ([`tyrne_hal::MmuError::BlockMapped`]).

mod console;
mod context_switch;
mod cpu;
mod irq_controller;
mod mmu;
mod timer;

pub use console::FakeConsole;
pub use context_switch::{FakeContextSwitch, FakeTaskContext};
pub use cpu::FakeCpu;
pub use irq_controller::FakeIrqController;
pub use mmu::{
    BlockMappedMmu, FakeAddressSpace, FakeMmu, FakeUserMem, OutOfFramesMmu, VecFrameProvider,
};
pub use timer::FakeTimer;
