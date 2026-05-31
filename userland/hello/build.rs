//! Build script for `tyrne-userland-hello`.
//!
//! Passes the userland linker script (`hello.ld`) to the linker with an
//! absolute path, mirroring `bsp-qemu-virt/build.rs`. The script fixes the
//! image at the userspace base VA with the entry at offset 0 (ADR-0029/0039).

fn main() {
    let manifest_dir = std::env::var("CARGO_MANIFEST_DIR")
        .expect("CARGO_MANIFEST_DIR must be set by Cargo when running build scripts");

    println!("cargo:rustc-link-arg=-T{manifest_dir}/hello.ld");
    println!("cargo:rerun-if-changed=hello.ld");
    println!("cargo:rerun-if-changed=build.rs");
}
