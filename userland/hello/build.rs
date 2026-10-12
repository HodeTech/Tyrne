//! Build script for `tyrne-userland-hello`.
//!
//! Passes the userland linker script (`hello.ld`) to the linker — **only when
//! building for aarch64 with target OS `none`**. The script fixes the image at the
//! userspace base VA with the entry at offset 0 (ADR-0029/0039) and ASSERTs no
//! `.data`/`.bss`/`.got`. On a HOST build (the `--workspace` member is host-
//! compiled by `cargo check`/`miri`/`llvm-cov`), those ASSERTs would fire
//! against the host std + coverage-instrumentation artifacts at link time, so
//! the script must NOT be applied there — the host build links as an ordinary
//! `std` stub (see `src/main.rs`) and is never run.

fn main() {
    let manifest_dir = std::env::var("CARGO_MANIFEST_DIR")
        .expect("CARGO_MANIFEST_DIR must be set by Cargo when running build scripts");

    // Cargo's target arch AND OS distinguish the bare-metal image from ARM hosts.
    // Keep in sync with src/main.rs, ../tyrne-user/src/lib.rs and bsp-qemu-virt/src/main.rs's bare-metal gate.
    if std::env::var("CARGO_CFG_TARGET_ARCH").as_deref() == Ok("aarch64")
        && std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("none")
    {
        println!("cargo:rustc-link-arg=-T{manifest_dir}/hello.ld");
    }
    println!("cargo:rerun-if-changed=hello.ld");
    println!("cargo:rerun-if-changed=build.rs");
}
