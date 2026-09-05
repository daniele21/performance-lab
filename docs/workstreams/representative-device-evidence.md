# Representative device evidence

Status: active
Owner: Performance Lab evidence
Canonical scope: evidence.representative-device
Last reviewed: 2026-09-05

## Goal

Validate assumptions that synthetic CI cannot prove by running representative models through a real Local LLM Server/device path and retaining auditable evidence.

This workstream does not change benchmark semantics to fit a device. It proves where existing contracts hold, surfaces unsupported/unknown telemetry honestly and bounds the claims that can be made.

## Delivery coordination

[`incremental-value-delivery.md`](incremental-value-delivery.md) owns delivery order. This workstream owns the **real-device protocol and retained evidence**.

The representative campaign is intentionally deferred until the planned deterministic software changes have converged on `dev`. This prevents repeated real runs against moving intermediate heads while preserving the rule that no representative claim can be satisfied by fixture/hosted CI.

Current consumption:

- `VALUE-01` consumes EVID-001 for one real single-model execution/evidence loop;
- `VALUE-02` extends evidence to 2+ candidates under one use case/device;
- `VALUE-03` requires a representative 2+ supported-configuration decision;
- `VALUE-04` consumes EVID-003 for device-aware resource/performance decisions;
- `VALUE-05` consumes EVID-002 for repeatability/variability;
- `VALUE-06` consumes EVID-004 for real comparison/regression policy evidence;
- `VALUE-08` requires a representative clean install/use smoke of the distributed artifact.

## Durable owners

- [`../evaluation-and-benchmarking.md`](../evaluation-and-benchmarking.md) — benchmark/evaluator semantics;
- [`../telemetry.md`](../telemetry.md) — measurement/provenance rules;
- [`../output-and-evidence-reference.md`](../output-and-evidence-reference.md) — persisted/exported evidence;
- [`../local-llm-server-integration.md`](../local-llm-server-integration.md) — LLS integration boundary;
- [`../local-llm-identity-contract.md`](../local-llm-identity-contract.md) — runtime/device/model identity;
- [`.engineering/pre-real-e2e.json`](../../.engineering/pre-real-e2e.json) — automated prerequisite before `RUNTIME-1`.

## Remaining gates

| Task | State | Acceptance |
| --- | --- | --- |
| EVID-000 PRE_REAL capability | IMPLEMENTED | final candidate `dev` must produce a fresh exact-head Built Product/PRE_REAL PASS immediately before the real phase |
| EVID-001 representative run | DEFERRED | #120 executes one real endpoint/browser loop and retains verified store + `.plab.zip` + identity/telemetry/media evidence |
| EVID-002 repeat/load evidence | DEFERRED | controlled repeated runs document warmup/load assumptions, variability and failures without hiding denominators |
| EVID-003 telemetry validation | DEFERRED | supported sensors/metrics have explicit scope/unit/provenance; unavailable data remains typed |
| EVID-004 comparison/regression evidence | DEFERRED | representative compatible/incompatible pairs preserve comparison reasons and valid-delta boundaries; at least one versioned policy outcome is retained |

`DEFERRED` here means deliberately scheduled after software convergence, not blocked by an implementation failure.

## Final real-phase entry gate

Before entering the representative environment:

1. planned software modifications are merged on the intended `dev` candidate;
2. repository health and the exact required deterministic integration gates are green on that head;
3. a fresh exact-head PRE_REAL/Built Product artifact reports readiness for that same source revision;
4. the complete diff/current state is reviewed so the real campaign measures the intended product, not an intermediate branch;
5. the Local LLM Server boundary remains the runtime/serving owner for real model tests.

Any material edit, merge/replay, dependency change or relevant target-base movement after readiness invalidates affected exact-head PRE_REAL evidence and requires refresh before real execution.

## Representative campaign order

The detailed runbooks remain owned by their VALUE issues, but the intended consolidated phase is:

```text
final software-converged dev
-> exact-head PRE_REAL/Built Product
-> VALUE-01D / EVID-001 single-model loop
-> VALUE-02D multi-model decision
-> VALUE-03D supported configuration decision
-> VALUE-04D / EVID-003 telemetry/device validation
-> EVID-002 repeatability/load evidence
-> EVID-004 comparison/regression evidence
-> VALUE-08D clean install/use smoke
```

Runs may be combined only when one retained execution genuinely satisfies each consuming contract; do not infer thermal/repeatability/regression claims from a single unrelated run.

## Evidence rules

- `RUNTIME-1` starts only while current exact-head `PRE_REAL_E2E` evidence is PASS.
- The real environment should confirm residual fidelity gaps, not discover ordinary deterministic browser/product workflow defects.
- Hosted CI or a mocked endpoint cannot satisfy a representative hardware/model claim.
- A model name alone is not evidence identity.
- Record exact runtime version, model revision/artifact/quantization when obtainable, device identity/class and benchmark protocol inputs.
- Record searched generation configuration identity for configuration-decision evidence.
- Preserve failed/interrupted samples and measurement denominators; do not report only successful cases.
- Thermal/resource claims require the actual measurement protocol and supported sensors.
- Unavailable sensors remain unavailable; context-only telemetry is not promoted into decision evidence.
- Keep raw sensitive prompts/outputs out of aggregate-safe evidence unless explicitly required and handled under the documented sensitive-data boundary.

## Completion gate

Complete when the representative runs needed for current VALUE slices/M1-M6 claims are retained and reproducible, their limitations are reflected in canonical evidence/telemetry docs, and no fixture-only assumption is presented as a real-device fact.

After completion, update `current-state.md`/roadmap and delete this workstream by default.
