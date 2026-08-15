# Telemetry and resource measurement

Status: active
Document type: feature-specification
Owner: telemetry
Canonical scope: telemetry.measurement
Read when: adding resource collectors, instrumented endpoint metrics, correlation logic or telemetry persistence
Last reviewed: 2026-08-15

## 1. Goal

Telemetry enriches benchmark evidence with hardware/runtime resource measurements without making resource instrumentation a prerequisite for endpoint evaluation.

The telemetry design must preserve the distinction between:

- measurements observed by Performance Lab;
- measurements reported by the inference service/runtime;
- measurements collected from the host/device operating system;
- values that are unavailable or cannot be attributed safely.

## 2. Capability levels

### Level 0 — black-box endpoint

No cooperation from the runtime is required.

Available measurements may include:

- client-observed request latency;
- TTFT for streaming endpoints;
- completion/error/timeout;
- token usage when the API reports it.

Unavailable by default:

- model process memory;
- VRAM/unified memory;
- CPU/GPU utilization attributable to inference;
- thermal state;
- energy;
- internal model load or KV-cache metrics.

### Level 1 — co-located host observation

Performance Lab can inspect the same host on which inference runs.

Possible measurements:

- system memory;
- process memory if process identity is known;
- system/process CPU;
- load average;
- platform-specific GPU metrics;
- thermal/energy signals where accessible.

Every metric records its attribution scope. System-level values must not be represented as model-process values.

### Level 2 — instrumented inference service/device

A cooperating endpoint exposes a small telemetry contract or sidecar.

Recommended metadata:

- service/runtime name and version;
- model identity/revision/quantization;
- hardware identity;
- model residency state;
- process memory;
- device/GPU memory;
- CPU/GPU utilization;
- thermal state;
- runtime-native load/prefill/decode measurements;
- optional energy/power.

This level provides the strongest evidence for local-device model comparisons.

## 3. Collector contract

Conceptual interface:

```text
probe() -> CollectorCapabilities
start(run_context) -> CollectorSession
sample(session) -> Measurement[]
stop(session) -> CollectorSummary
```

Collectors must:

- fail independently from inference;
- report permission/capability failure explicitly;
- identify metric provenance and unit;
- expose sampling interval/overhead metadata;
- support clean cancellation and shutdown.

## 4. Measurement schema

Every measurement should contain:

- metric ID;
- value;
- unit;
- measurement scope;
- collector/provider ID and version;
- provenance (`lab_observed`, `host_observed`, `endpoint_reported`, `runtime_native`);
- timestamp/time basis;
- run ID;
- optional request/sample ID;
- quality/availability flag;
- optional attribution notes.

## 5. Metric naming

Metric names should encode semantics rather than presentation labels.

Examples:

```text
memory.process.rss_bytes
memory.process.pss_bytes
memory.device.used_bytes
cpu.process.utilization_pct
gpu.device.utilization_pct
thermal.state
power.device.watts
energy.run.joules
runtime.model_load_ms
runtime.prefill_tokens_per_second
runtime.decode_tokens_per_second
```

Do not reuse one metric name for different scopes or units.

## 6. Sampling protocol

Resource sampling is a benchmark protocol input.

Record:

- sampling interval;
- collector startup delay;
- whether samples include warmup;
- pre-run baseline window when applicable;
- post-run cooldown window when applicable;
- dropped sample count;
- estimated collector overhead where known.

Changing these semantics changes the telemetry protocol version in the execution fingerprint.

## 7. Request correlation

For co-located measurements using the same monotonic clock, telemetry can be correlated to request/sample windows precisely.

For remote devices, clock offsets/drift may prevent precise event-level correlation. Until synchronization is implemented, remote measurements should be scoped to run windows or to server-generated request IDs/timestamps whose semantics are documented.

Do not imply millisecond-level causal alignment when clocks are not synchronized.

## 8. Peak memory

Peak memory is only meaningful when the scope is clear.

Examples:

- peak process RSS during measured run;
- peak process PSS during measured run;
- peak device GPU memory;
- peak system used memory.

The report should always show scope and provenance near the value.

## 9. Thermal evidence

Thermal state should be treated as contextual evidence because sustained local inference can throttle performance.

When supported, capture:

- start thermal state;
- peak/worst thermal state;
- thermal-throttling indicators;
- state at each measured request or coarse run intervals.

A benchmark performed under materially different thermal conditions should surface that identity/environment difference before interpreting latency deltas.

## 10. Energy and power

Energy measurement is platform-specific and often approximate.

Rules:

- store raw source/provenance;
- distinguish instantaneous power from integrated energy;
- record sampling/integration methodology;
- avoid cross-device energy comparisons when sensors/methods differ materially;
- mark estimated values as estimates.

## 11. Instrumented endpoint contract

A future optional endpoint extension can expose safe metadata through a dedicated endpoint such as a namespaced Performance Lab capability route.

The contract should be versioned and may include:

```text
GET capabilities
GET runtime identity
GET telemetry snapshot
```

Potential future control hooks for valid controlled-cold tests:

```text
POST unload
POST reset-cache
```

Control hooks are optional and must never be assumed for third-party endpoints. They should require explicit user configuration because unloading or resetting an inference service is a mutating action.

## 12. Privacy and security

Telemetry must not persist:

- prompts or outputs;
- authentication tokens;
- signed URLs;
- arbitrary environment variables;
- command lines that may contain secrets;
- private file paths unless explicitly sanitized.

Host/process discovery should collect only fields needed for benchmark attribution.

## 13. Failure behavior

Examples of typed availability states:

- `AVAILABLE`;
- `UNAVAILABLE_UNSUPPORTED`;
- `UNAVAILABLE_PERMISSION`;
- `UNAVAILABLE_REMOTE`;
- `UNAVAILABLE_PROCESS_UNKNOWN`;
- `COLLECTOR_ERROR`;
- `PARTIAL`.

Inference continues when a non-required collector fails. The run report records the telemetry degradation.

## 14. Comparison rules

Resource regressions require compatible metric semantics.

Before comparing peak memory or CPU/GPU utilization, verify:

- same metric ID/scope/unit;
- compatible collector version/protocol;
- compatible run window/warmup policy;
- compatible host/device identity when making same-device regression claims.

Different devices can still be intentionally compared as a configuration trade-off, but not as a same-environment regression.

## 15. Initial implementation priority

1. implement collector interfaces and unavailable states;
2. add portable host CPU/memory collection where reliable;
3. design the instrumented endpoint telemetry schema;
4. integrate a real local inference service/device;
5. only then add platform-specific GPU/thermal/energy collectors driven by concrete hardware use cases.

This keeps the MVP useful without making platform telemetry the critical path.
