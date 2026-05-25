# Phase F — Smart-home deployment

**Exit bar:** A real physical device in the maintainer's smart-home setup runs Tyrne as its firmware, communicating with a hub (Matter controller or MQTT broker) and reacting to real events.

**Scope:** The project's reason to exist. The plumbing from Phase E gets specialized drivers; one or more smart-home protocols are selected; the first deployable device is built.

**Out of scope:** A generic smart-home platform for others to use (possible long-term but not in this phase); voice assistants; cloud connectivity.

---

## Milestone F1 — GPIO driver on Pi 4

GPIO control on BCM2711. Fundamental because most smart-home peripherals (sensors, relays, LEDs) sit on GPIO pins.

### Sub-breakdown

1. **ADR-0053 — GPIO service interface.** Pin granularity, capability per pin vs. per bank; direction / pull-up / drive-strength configuration.
2. **`tyrne-driver-gpio-bcm2711`** driver task.
3. **Client library** `tyrne-gpio` with typed pin handles.

### Acceptance criteria

- ADR-0053 Accepted.
- Driver toggles a GPIO pin observable externally (an LED, a scope).

## Milestone F2 — I2C and SPI drivers

Most smart-home sensors use one of these. Covers the BCM2711 peripherals.

### Sub-breakdown

1. **ADR-0054 — I2C service interface.**
2. **ADR-0055 — SPI service interface.** (Separate ADR because of different capability semantics — SPI has chip-select per device, I2C has addresses.)
3. **Drivers** `tyrne-driver-i2c-bcm2711`, `tyrne-driver-spi-bcm2711`.
4. **Test clients** that read a known sensor (e.g., BME280 on I2C, an MCP SPI flash) to verify end-to-end.

### Acceptance criteria

- ADRs Accepted.
- One real I2C sensor read returns plausible values.
- One real SPI device read returns plausible values.

## Milestone F3 — Protocol choice (Matter / MQTT / both)

The smart-home communication protocol. Matter is the modern open standard; MQTT is the lightweight alternative.

### Sub-breakdown

1. **ADR-0056 — Smart-home protocol.** Weighed by: open-source library availability, power profile, interop with the maintainer's existing hub, security posture.
2. **Implementation** — either a port of an existing Rust crate (preferred) or a minimal subset implementation from scratch (accepted cost).
3. **Security review** of the protocol implementation per [`analysis/reviews/security-reviews/`](../../analysis/reviews/security-reviews/).

### Acceptance criteria

- ADR-0056 Accepted.
- End-to-end: Tyrne device sends a heartbeat / state update to a real hub.

## Milestone F4 — First smart-home device

A chosen device — e.g., a temperature sensor node, a smart plug, an environmental monitor — running Tyrne as its full firmware.

### Sub-breakdown

1. **Device choice** — specific hardware with power and mechanical suitability.
2. **Integration** — wiring F1–F3 together into a coherent application running on Pi 4 hardware.
3. **Reliability test** — 7-day uptime under realistic load without crashes or memory growth.
4. **Guide** `docs/guides/first-smart-home-device.md`.
5. **Business review** — the first real "production" deployment.

### Acceptance criteria

- Device runs 7 days uninterrupted.
- Its state is reflected in the hub and reacts to commands.
- Guide reproducible.

## Milestone F5 — Secure field update

A deployed device runs Tyrne as its firmware (F4) with a 7-day-uptime expectation; there must be a way to deliver a new kernel/userspace image to an already-running device without a physical re-flash. This milestone establishes that path. Scope is sketched at a high level here; the detailed mechanism is deferred to its own ADR.

### Sub-breakdown (high level — detail deferred to ADR)

1. **ADR-0057 — Field-update / OTA scheme.** High-level scope only at plan time; the design is deferred to the ADR itself. It must cover, at minimum:
   - **Image transport** — how a new image reaches the device (pulled over the network service from E6, or staged via the storage service from E4; the choice and its trust assumptions).
   - **Image verification before activation** — signature and/or measurement verification of the candidate image against a trusted key/manifest before it is allowed to become the active image. Ties directly into the cryptographic primitives (Phase G's crypto ADR, ADR-0059) and measured-boot work in Phase G (G1 / G2); F5 may have to pull those forward or ship a minimal verifier and harden it in G.
   - **A/B (dual-bank) image layout with automatic rollback** — two image slots so an update is written to the inactive slot and only made active after it boots and passes a health check; a failed boot rolls back to the last-known-good slot automatically (boot-counter / watchdog discipline).
   - **Update-authority capability model** — which capability authorizes triggering an update and writing the inactive slot, so "who may push an image to this device" is an explicit, capability-gated decision rather than ambient authority.

### Acceptance criteria (provisional)

- ADR-0057 Accepted.
- A new image can be delivered to a running device, verified, activated on the next boot, and automatically rolled back if it fails to come up — demonstrated end-to-end on Pi 4 hardware.

### Phase F closure

Milestone F4 is a genuine milestone: Tyrne becomes real when this ships. Subsequent phases tighten the security story (Phase G) and expand the platform base (Phase H).

## ADR ledger for Phase F

| ADR | Purpose | Expected state | Note |
|-----|---------|----------------|------|
| ADR-0053 | GPIO service interface | F1 | renumbered 2026-05-22, was ADR-0043 (cascade from the Phase C/D renumbering) |
| ADR-0054 | I2C service interface | F2 | renumbered 2026-05-22, was ADR-0044 (cascade) |
| ADR-0055 | SPI service interface | F2 | renumbered 2026-05-22, was ADR-0045 (cascade) |
| ADR-0056 | Smart-home protocol | F3 | renumbered 2026-05-22, was ADR-0046 (cascade) |
| ADR-0057 | Field-update / OTA scheme | F5 | new 2026-05-22 (master-review MR-021 — light placeholder; detailed design deferred to the ADR). ADR-0057 was previously also used by phase-i.md (I3, power management); phase-i was renumbered in this same pass (I3 → ADR-0068), so ADR-0057 is now uniquely this F5 placeholder — see the §Downstream-renumbering note in [phase-e.md](phase-e.md). |

Numbers are tentative; final numbers are assigned when the ADR is actually written, per [ADR-0013](../../decisions/0013-roadmap-and-planning.md).

## Open questions carried into Phase F

- **Wi-Fi on Pi 4.** The Broadcom Wi-Fi chip requires proprietary firmware; Tyrne's policy rejects blobs. Options: use Ethernet instead on Pi 4 (simplest), use USB Wi-Fi dongles with open-source firmware, or accept a documented exception for firmware that lives outside the kernel (in-scope for an ADR).
- **Battery operation.** Power-management is substantial; may belong in Phase I alongside mobile.
- **Encryption at rest** on device storage — crosses into Phase G.
- **Field update / OTA (F5).** How much of the verification stack (signatures, measured boot) must land in F5 versus being pulled forward from Phase G (G1 / G2). Whether the A/B dual-bank layout is decided here or in the Pi 4 memory-layout ADR (ADR-0045). What the trust root for the update-signing key is, and where it lives on-device. Whether the update path reuses the E6 network service or the E4 storage service for transport.
