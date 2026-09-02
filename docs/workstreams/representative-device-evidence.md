# Representative device evidence

Status: active
Owner: Performance Lab evidence
Canonical scope: evidence.representative-device
Last reviewed: 2026-09-02

## Goal

Validate assumptions that synthetic CI cannot prove by running representative models through a real Local LLM Server/device path and retaining auditable evidence.

This workstream does not change benchmark semantics to fit a device. It proves where existing contracts hold, surfaces unsupported/unknown telemetry honestly and bounds the claims that can be made.

## Delivery coordination

[`incremental-value-delivery.md`](incremental-value-delivery.md) owns delivery order. This workstream owns the **real-device protocol and retained evidence**.

Current consumption:

- `VALUE-01` consumes EVID-001 for one real single-model execution/evidence loop;
- `VALUE-02` extends evidence to 2+ candidates under one use case/device;
- `VALUE-04` consumes EVID-003 for device-aware resource/performance decisions;
- `VALUE-05` consumes EVID-002 for repeatability/variability;
- `VALUE-06` consumes EVID-004 for real comparison/regression policy evidence.

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
| EVID-000 pre-real E2E | DONE | Built Product reports `READY_FOR_REAL_ENVIRONMENT: YES`; required browser/packaged evidence is retained |
| EVID-001 representative run | READY | A/B/C are integrated; refresh exact-head PRE_REAL, then #120 executes one real endpoint/browser loop and retains verified store + `.plab.zip` + identity/telemetry/media evidence |
| EVID-002 repeat/load evidence | PLANNED | controlled repeated runs document warmup/load assumptions, variability and failures without hiding denominators |
| EVID-003 telemetry validation | PLANNED | supported sensors/metrics have explicit scope/unit/provenance; unavailable data remains typed |
| EVID-004 comparison/regression evidence | PLANNED | representative compatible/incompatible pairs preserve comparison reasons and valid-delta boundaries; at least one regression policy outcome is retained where applicable |

## EVID-001 convergence

The software/readiness lanes are integrated:

- #117 supplies the real built-browser Test -> Run Detail -> Sample Evidence path;
- #118 verifies canonical store/bundle identity, telemetry provenance, local evidence-rich content and portable-bundle privacy boundaries;
- #119 supplies the exact-head PRE_REAL-gated operator run/config/manifest;
- #120 is the only retained `REAL_ENVIRONMENT` acceptance run.

The merge commits changed the repository source revision, therefore pre-merge PRE_REAL artifacts are stale for #120 even when the tree content is equivalent. A fresh exact-head PRE_REAL PASS is required before entering the representative environment.

## Evidence rules

- `RUNTIME-1` starts only while current exact-head `PRE_REAL_E2E` evidence is PASS; any material edit or target-base movement invalidates older readiness evidence.
- The real environment should confirm residual fidelity gaps, not discover ordinary browser/product workflow defects.
- Hosted CI or a mocked endpoint cannot satisfy a representative hardware claim.
- A model name alone is not evidence identity.
- Record exact runtime version, model revision/artifact/quantization when obtainable, device identity/class and benchmark protocol inputs.
- Preserve failed/interrupted samples and measurement denominators; do not report only successful cases.
- Thermal/resource claims require the actual measurement protocol and supported sensors.
- Keep raw sensitive prompts/outputs out of aggregate-safe evidence unless explicitly required and handled under the documented sensitive-data boundary.

## Completion gate

Complete when the representative runs needed for current VALUE slices/M1-M6 claims are retained and reproducible, their limitations are reflected in canonical evidence/telemetry docs, and no fixture-only assumption is presented as a real-device fact.

After completion, update `current-state.md`/roadmap and delete this workstream by default.
