# Representative device evidence

Status: active
Owner: Performance Lab evidence
Canonical scope: evidence.representative-device
Last reviewed: 2026-09-02

## Goal

Validate the assumptions that synthetic CI cannot prove by running representative models through a real Local LLM Server/device path and retaining auditable evidence.

This workstream does not change benchmark semantics merely to fit a device. It proves where the existing contracts hold, surfaces unsupported/unknown telemetry honestly and bounds the product claims that can be made.

## Delivery coordination

[`incremental-value-delivery.md`](incremental-value-delivery.md) owns the order in which this evidence unlocks product value. This workstream owns the **real-device protocol and retained evidence**, not a separate capability-first execution sequence.

Current consumption:

- `VALUE-01` consumes EVID-001 to prove one real single-model execution/evidence loop;
- `VALUE-02` extends representative evidence to 2+ candidates under one use case/device;
- `VALUE-04` consumes EVID-003 for device-aware resource/performance decisions;
- `VALUE-05` consumes EVID-002 for repeatability/variability;
- `VALUE-06` consumes EVID-004 for real comparison/regression policy evidence.

Do not wait for EVID-001..004 as one monolithic campaign before delivering VALUE-01. Retain each accepted slice as soon as its required evidence is sufficient.

## Durable owners

- [`../evaluation-and-benchmarking.md`](../evaluation-and-benchmarking.md) — benchmark/evaluator semantics;
- [`../telemetry.md`](../telemetry.md) — measurement/provenance rules;
- [`../output-and-evidence-reference.md`](../output-and-evidence-reference.md) — persisted/exported evidence;
- [`../local-llm-server-integration.md`](../local-llm-server-integration.md) — LLS integration boundary;
- [`../local-llm-identity-contract.md`](../local-llm-identity-contract.md) — runtime/device/model identity;
- [`.engineering/pre-real-e2e.json`](../../.engineering/pre-real-e2e.json) — automated acceptance prerequisite before `RUNTIME-1`.

## Remaining gates

| Task | State | Acceptance |
| --- | --- | --- |
| EVID-000 pre-real E2E | DONE | Built Product reports `READY_FOR_REAL_ENVIRONMENT: YES`; J0-J9 retain browser screenshots/traces and packaged J0/J1/J8/J9 retain assembled-product screenshots/traces |
| EVID-001 representative run | ACTIVE | VALUE-01A/B/C integrate first; then #120 re-checks exact-head `PRE_REAL_E2E = PASS`, runs one real endpoint/browser loop and retains verified store + `.plab.zip` + identity/telemetry/media evidence |
| EVID-002 repeat/load evidence | PLANNED | controlled repeated runs document warmup/load assumptions, variability and failures without hiding denominators |
| EVID-003 telemetry validation | PLANNED | supported sensors/metrics have explicit scope/unit/provenance; unavailable data remains typed |
| EVID-004 comparison/regression evidence | PLANNED | representative compatible and incompatible pairs preserve comparison reasons and valid-delta boundaries; at least one regression policy outcome is retained where applicable |

## EVID-001 convergence

The software/readiness work may proceed in parallel, but the representative claim is singular:

- #117 supplies the real built-browser Test -> Run Detail -> Sample Evidence path;
- #118 verifies canonical store/bundle identity, telemetry provenance, local evidence-rich content and portable-bundle privacy boundaries;
- #119 supplies the exact-head PRE_REAL-gated operator run/config/manifest;
- #120 is the only retained `REAL_ENVIRONMENT` acceptance run and may begin only after the first three lanes are integrated.

A green A/B/C CI run is not EVID-001 evidence by itself.

## Evidence rules

- `RUNTIME-1` starts only while the current relevant `PRE_REAL_E2E` evidence is passing; a material edit or target-base movement invalidates older readiness evidence.
- The real environment should confirm residual fidelity gaps, not discover ordinary browser/product workflow defects.
- A hosted CI run or mocked endpoint cannot satisfy a representative hardware claim.
- A model name alone is not evidence identity.
- Record exact runtime version, model revision/artifact/quantization when obtainable, device identity/class and benchmark protocol inputs.
- Preserve failed/interrupted samples and measurement denominators; do not report only successful cases.
- Thermal/resource claims require the actual measurement protocol and supported sensors.
- Keep raw sensitive prompts/outputs out of aggregate-safe evidence unless explicitly required and handled under the documented sensitive-data boundary.

## Completion gate

Complete when the representative runs needed for the current VALUE slices/M1-M6 claims are retained and reproducible, their limitations are reflected in canonical evidence/telemetry docs, and no fixture-only assumption is presented as a real-device fact.

After completion, update `current-state.md`/roadmap and delete this workstream by default.