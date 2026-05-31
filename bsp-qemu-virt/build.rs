//! Build script for `tyrne-bsp-qemu-virt`.
//!
//! Passes the linker script at the crate root to the linker with an absolute
//! path so resolution does not depend on the linker's working directory.
//! See `docs/decisions/0012-boot-flow-qemu-virt.md` for the memory layout the
//! linker script encodes.
//!
//! Also asserts the userland image (`userland/hello/hello.bin`) that
//! `main.rs` embeds via `include_bytes!` exists, and re-runs when it changes —
//! it is produced by `tools/build-userland.sh` (ADR-0039), which must run
//! before `cargo kernel-build`.

fn main() {
    let manifest_dir = std::env::var("CARGO_MANIFEST_DIR")
        .expect("CARGO_MANIFEST_DIR must be set by Cargo when running build scripts");

    println!("cargo:rustc-link-arg=-T{manifest_dir}/linker.ld");
    println!("cargo:rerun-if-changed=linker.ld");
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=src/boot.s");
    println!("cargo:rerun-if-changed=src/vectors.s");

    // Userland image (ADR-0039 / T-027): `main.rs` embeds this via
    // `include_bytes!`. It is produced by `tools/build-userland.sh`
    // (cargo build -> rust-objcopy) — NOT by this build script (no nested
    // cargo). Fail loudly with the remedy if it is absent, rather than letting
    // `include_bytes!` emit an opaque "file not found".
    let hello_bin = format!("{manifest_dir}/../userland/hello/hello.bin");
    println!("cargo:rerun-if-changed={hello_bin}");
    assert!(
        std::path::Path::new(&hello_bin).exists(),
        "userland image not built: {hello_bin} is missing.\n       \
         Run `tools/build-userland.sh` before `cargo kernel-build` \
         (ADR-0039); `tools/smoke.sh` and CI do this automatically."
    );
}
