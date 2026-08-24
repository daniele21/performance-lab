# Representative device evidence

Status: active
Owner: Performance Lab evidence
Canonical scope: evidence.representative-device
Last reviewed: 2026-08-24

## Goal

Validate the assumptions that synthetic CI cannot prove by running representative models through a real Local LLM Server/device path and retaining auditable evidence.

This workstream does not change benchmark semantics merely to fit a device. It proves where the existing contracts hold, surfaces unsupported/unknown telemetry honestly and bounds the product claims that can be made.

## Durable owners

- [`../evaluation-and-benchmarking.md`](../evaluation-and-benchmarking.md) — benchmark/evaluator semantics;
- [`../telemetry.md`](../telemetry.md) — measurement/provenance rules;
- [`../output-and-evidence-reference.md`](../output-and-evidence-reference.md) — persisted/exported evidence;
- [`../local-llm-server-integration.md`](../local-llm-server-integration.md) — LLS integration boundary;
- [`../local-llm-identity-contract.md`](../local-llm-identity-contract.md) — runtime/device/model identity.

## Remaining gates

| Task | State | Acceptance |
| --- | --- | --- |
| EVID-001 representative run | READY | real endpoint completes; fingerprint and retained `.plab.zip` identify model/runtime/device/suite/datasets/config |
| EVID-002 repeat/load evidence | PLANNED | controlled repeated runs document warmup/load assumptions, variability and failures without hiding denominators |
| EVID-003 telemetry validation | PLANNED | supported sensors/metrics have explicit scope/unit/provenance; unavailable data remains typed |
| EVID-004 comparison/regression evidence | PLANNED | representative compatible and incompatible pairs preserve comparison reasons and valid-delta boundaries; at least one regression policy outcome is retained where applicable |

## Evidence rules

- A hosted CI run or mocked endpoint cannot satisfy a representative hardware claim.
- A model name alone is not evidence identity.
- Record exact runtime version, model revision/artifact/quantization when obtainable, device identity/class and benchmark protocol inputs.
- Preserve failed/interrupted samples and measurement denominators; do not report only successful cases.
- Thermal/resource claims require the actual measurement protocol and supported sensors.
- Keep raw sensitive prompts/outputs out of aggregate-safe evidence unless explicitly required and handled under the documented sensitive-data boundary.

## Completion gate

Complete when the representative runs needed for the current M1-M6 claims are retained and reproducible, their limitations are reflected in canonical evidence/telemetry docs, and no fixture-only assumption is presented as a real-device fact.

After completion, update `current-state.md`/roadmap and delete this workstream by default. Git history owns the plan history.
