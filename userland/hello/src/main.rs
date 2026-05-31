//! # tyrne-userland-hello
//!
//! Tyrne's first real userspace program (B6). It runs in EL0 in its own address
//! space, greets through a `console_write` syscall, and exits via `task_exit` —
//! the EL0↔EL1 round-trip the B5 EL1-stub proxy could not prove.
//!
//! This is a `#![no_std] #![no_main]` raw-flat image per [ADR-0029][adr-0029]:
//! the loader maps the objcopy'd bytes at a fixed userspace VA with the entry
//! instruction at **offset 0**, so [`_start`] is placed first via the
//! `.text._start` section + the `hello.ld` linker script. There is no `.data`
//! or `.bss` — the image region maps `USER | EXECUTE` (no `WRITE`), so the
//! greeting is a read-only string literal (`.rodata`, in-image) and there are
//! no writable globals. The build pipeline (cargo → `rust-objcopy -O binary` →
//! `include_bytes!`) is [ADR-0039][adr-0039] / T-027.
//!
//! [adr-0029]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0029-initial-userspace-image-format.md
//! [adr-0039]: https://github.com/HodeTech/Tyrne/blob/main/docs/decisions/0039-userland-build-pipeline.md

#![no_std]
#![no_main]

use tyrne_user::{console_write, task_exit, HELLO_CONSOLE_CAP};

/// The greeting emitted via `console_write`. A read-only `.rodata` literal that
/// lives inside the mapped image region (`USER | EXECUTE`) — gate #1 admits a
/// read of a `USER` page, so the buffer pointer translates and the bytes copy.
static GREETING: &[u8] = b"hello from userspace\n";

/// Userspace entry point. Placed at **offset 0** of the raw-flat image (the
/// loader sets `ELR_EL1` to the image base, so the first instruction executed
/// is this function's first instruction). Greets, then exits — never returns.
///
/// `#[no_mangle]` gives the linker the bare `_start` symbol (the `hello.ld`
/// `ENTRY`); `#[link_section = ".text._start"]` + the script's `KEEP` place it
/// first in `.text` so offset 0 is the entry.
#[no_mangle]
#[link_section = ".text._start"]
pub extern "C" fn _start() -> ! {
    // Ignore the result: the v1 demo has no fallback path if the console write
    // is rejected — it exits cleanly either way (the kernel reports the exit).
    let _ = console_write(HELLO_CONSOLE_CAP, GREETING);
    task_exit(0)
}

/// Panic handler (required for `#![no_std]`). Unwinding is disabled
/// (`panic=abort` for the bare-metal target), so this just exits the task with
/// a distinct non-zero code rather than attempting to unwind.
#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    task_exit(101)
}
