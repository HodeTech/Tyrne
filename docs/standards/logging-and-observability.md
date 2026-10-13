# Logging and observability

> **Planned — implementation status (2026-10-13):** this is a forward-looking standard. The workspace contains no `tyrne-log` crate, structured logging facade, per-CPU log ring, log service, metric facade or runtime logging-control API. Current kernel diagnostics use the raw HAL `Console` / BSP UART path. The sections below describe intended behavior, not delivered APIs or security guarantees. Implementation choices still require their named future ADRs; secret-redaction and context-safety constraints apply to current diagnostics as well.

How Tyrne diagnostic output should evolve under kernel / `no_std` constraints, and how operators and developers should eventually extract it safely.

## Scope and goals

- Provide **structured, level-controlled, capability-gated logging** that is safe to call from any context in the system, including interrupt service routines.
- Support **tracing** — timing and causal relationships — without the heavyweight infrastructure of desktop observability stacks.
- Guarantee that **secrets never appear in logs**.
- Keep the **storage and transport of logs** out of the kernel; the kernel emits log records via a capability; userspace services handle persistence, egress, and presentation.

## Log levels

Five levels, evaluated in order of increasing severity:

| Level | Use for |
|-------|---------|
| `trace` | Very fine-grained events; path tracing, every IPC, every scheduler decision. Default off even in debug builds. |
| `debug` | State changes useful during development. Default off in release. |
| `info` | Notable expected events. Default on. |
| `warn` | Something is unusual but the system continues. Default on. |
| `error` | A recoverable failure occurred. Default on. |

There is no `fatal`. A fatal condition triggers the panic path (see [error-handling.md](error-handling.md)), which currently prints the QEMU BSP banner and formatted PanicInfo, then spins; it does not supply a general register dump.

## Structured records

The planned facade would emit structured records rather than formatted strings:

```rust
// Conceptual shape, not real code.
struct LogRecord {
    timestamp: MonotonicNanos,
    level: Level,
    target: &'static str,      // e.g. "tyrne::ipc::endpoint"
    message: &'static str,     // short, literal
    fields: &'static [(&'static str, Value)], // typed key-value pairs
    span: Option<SpanId>,      // causal / timing context
    cpu: CpuId,
    task: Option<TaskId>,
}
```

- **`message`** is a short, literal English sentence without interpolation. ("IPC send rejected.")
- **`fields`** carry the variable data. ("endpoint" = EndpointId(7), "reason" = "no receiver").
- Rendering (human-readable vs. JSON vs. binary) is done by the consumer, not the producer.

The rationale is standard observability: searchable, machine-processable logs beat formatted strings.

## Logging APIs

The planned `tyrne-log` facade would provide macros mirroring the `log` crate's shape while producing structured records. It is not a workspace crate; this example is conceptual:

```rust
use tyrne_log::{trace, debug, info, warn, error};

info!(target = "ipc::endpoint", "IPC send rejected", endpoint = id, reason = "no receiver");
```

When the facade exists, crates must use it rather than `log::info!`, `tracing::info!` or `std::println!` directly. Until then, current raw Console/UART diagnostics must respect the secret and context constraints below; there is no facade API to call.

## Context rules

**Planned transport:** the ring, worker and userspace service below are not implemented. In particular, the raw UART path does not provide these ISR-safety or capability-routing properties.

### Kernel mode

- **ISR context:** `trace`/`debug`/`info` may be emitted. The macro writes to a per-CPU lock-free ring buffer; a kernel worker drains the buffer into the log transport at task context. ISRs never block on logging.
- **Task context in kernel:** same facade; same ring path by default.
- **Early boot:** the intended bootstrap sink is BSP UART (see [architecture/hal.md](../architecture/hal.md)). A future boot ring may lose records when full; today output is direct UART without that ring or structured transport.

### Userspace

- Services call the facade; the facade sends the record to a **log service** (a userspace task) via IPC.
- The log service holds the capabilities to any persistent sinks (serial console, flash, network).
- Services **cannot bypass the log service** to reach sinks directly. This is the capability discipline; it also simplifies redaction.

## Secrets and PII

- **No secret may be logged.** Not at any level. Not in debug builds.
- Types that carry secrets (`KeyMaterial`, `CapabilityToken`, `Secret<T>`) do **not** implement `Display` or unredacted `Debug`. Their `Debug` impl prints a type name and an object ID, never the bytes.
- When a function must log about a secret, it logs about its *identity*, not its *value*: `"key rotated", "key_id" = KeyId(42)`.
- PII (user names, device identifiers, network addresses) is treated as sensitive by default. Logs include it only when the subsystem's documented contract says to, and the field is tagged `sensitive = true` so downstream sinks can apply additional controls.

This is not just hygiene: a capability-based OS loses its meaning if capabilities show up in logs.

## Sampling and rate limits

**Planned:** these policies require the future facade/ring/service; no current rate-limiting guarantee is delivered.

- `trace` and `debug` are always candidates for sampling. The facade supports per-target rate limits (records-per-second) to avoid flooding the ring.
- A flooded ring drops the oldest records, not the newest. The log service reports dropped-record counts as an `info` event.
- Rate-limited records should be deterministic (e.g. 1-in-N) rather than time-based, to keep repro logs useful.

## Tracing and spans

**Planned:** span propagation and IDs are a design target, not an existing tracing API.

- Causal / timing context is represented as **spans**. A span is opened before a unit of work and closed after; records emitted inside the span are associated with it.
- Spans carry a parent pointer, allowing causal chains across IPC boundaries.
- Spans have unique 64-bit ids generated from a per-CPU counter + CPU id.

In practice this maps onto the `tracing` crate's model; Tyrne will either adopt `tracing` directly (if a `no_std` subset works) or implement a compatible shape internally. The choice is deferred to an ADR at implementation time.

## Metrics

**Planned:** no metric facade, store, service or metric-read syscall is implemented.

- Metrics are counters, gauges, and histograms, emitted separately from logs.
- The metric facade (planned) lets subsystems register counters at crate init:
  - `ipc_send_total` (counter)
  - `ipc_send_error_total{reason=…}` (counter)
  - `scheduler_context_switch_total` (counter)
  - `capability_table_capacity_used` (gauge)
- Userspace metric service scrapes the kernel's metric store through a capability-gated syscall at operator-configurable intervals.
- Metrics do not replace logs; they summarize what logs detail.

## Dynamic configuration

**Planned:** `LogControlCap`, per-subsystem runtime levels and persistent operator configuration are not implemented.

- Levels can be changed at runtime per subsystem through an operator capability (`LogControlCap`).
- The default configuration in the kernel build is compiled in; runtime changes live until the next reboot unless persisted by an operator service.

## Output destinations

Only direct UART diagnostics exist today; ring retention, operator streaming and persistent logging below are proposed destinations.

- **Serial UART** — the always-available diagnostic channel. Early boot uses it exclusively.
- **Ring buffer in RAM** — retained across warm reboot on boards that support it; inspected via debug port.
- **Operator tool over IPC** — a debug/observability service that a developer can attach to and stream from.
- **Persistent storage** — future service work; no persistent log sink is implemented.

## Log format on the wire

- Binary, versioned, efficient. A single format that renders to JSON or human text offline.
- A future ADR selects the encoding (candidates: `postcard`, a custom TLV). No structured wire format is implemented today; this list does not authorize choosing one before that decision.

## Anti-patterns to reject

- `log::info!("endpoint {}: send failed because {}", id, reason)` — formatted, not structured.
- Logging in a place that allocates (heap-free is a hard rule in kernel).
- Logging an object whose `Debug` impl dumps secret bytes.
- Logging at `error` for expected failures (e.g. a receiver having no pending message when the caller is in non-blocking mode; that is `trace` at most).
- Logging inside a critical section beyond what is necessary.
- Duplicate logging (a layer logs and a caller logs the same event).

## Tooling

**Planned:** none of the structured logging tools below is delivered by this repository. Current diagnosis uses serial output and QEMU traces.

- Ring buffer inspection CLI (planned).
- JSON renderer for offline analysis.
- `grep`-friendly text renderer for quick triage.
- Metric scraper / dashboard integration — open; decided per deployment.

## References

- `tracing` crate: https://docs.rs/tracing/
- OpenTelemetry — the industry standard for spans + metrics: https://opentelemetry.io/
- `log` crate API shape (the familiar facade): https://docs.rs/log/
- Fuchsia logging design — kernel-to-userspace log service model.
- Linux kernel `printk` vs. `tracefs` — the trade-offs we learn from.
