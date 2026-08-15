# Plan changelog

Status: active
Document type: workstream-state
Owner: repository
Canonical scope: planning.change-history
Read when: understanding why the implementation plan, dependencies, milestone boundaries or priorities changed over time
Last reviewed: 2026-08-15

This is the append-oriented history of **material planning changes**. It is not a commit log and must not duplicate routine task status changes from [`current-state.md`](current-state.md).

A material plan change includes:

- adding/removing/splitting/merging a task;
- changing a dependency or critical path;
- changing milestone scope or exit criteria;
- changing architecture boundaries that affect implementation order;
- deferring or promoting a capability;
- changing an acceptance/evidence requirement.

## Entry template

```text
## YYYY-MM-DD — <short decision title>

Affected: <task IDs / milestones>

Previous assumption:
- ...

Decision:
- ...

Reason / evidence:
- ...

Dependency impact:
- ...

Roadmap impact:
- ...
```

---

## 2026-08-15 — Initial repository plan established

Affected: FND, ADP, DAT, EVAL, PERF, TEL, STO, CLI, REG, UI; M0-M9

Previous assumption:

- The project existed as a product concept: an independent lab calls an LLM exposed by another service, runs benchmarks/test datasets and measures performance on a device.
- Evaluation functionality had previously been considered partly inside an inference harness, but ownership boundaries were not yet formalized in this repository.

Decision:

- AI Performance Lab is an independent evaluation control plane; inference/model runtime lifecycle remains external to core.
- The evaluated identity is the complete execution fingerprint, not the model name alone.
- Capability, runtime performance and resource efficiency remain separate result dimensions.
- Basic endpoint evaluation is black-box; host/device/runtime telemetry is optional progressive instrumentation.
- Work is split into explicit parallel lanes: repository/contracts, adapters, datasets, capability evaluation, runtime performance, telemetry, storage/comparison, CLI, regression/CI, UI and external integrations.
- `current-state.md` owns live status; `implementation-plan.md` owns target/dependencies; `roadmap.md` owns milestone sequencing; this file owns material plan-history rationale.

Reason / evidence:

- A model's practical suitability depends on model + quantization + runtime + configuration + hardware + workload.
- Tightly coupling evaluation to one serving runtime would prevent comparison across local servers/devices and would duplicate infrastructure responsibilities.
- Requiring telemetry for all runs would unnecessarily block a useful black-box MVP.
- Keeping live status separate from durable target specifications reduces stale/contradictory documentation.

Dependency impact:

- FND-002 core schemas become the major fan-out point.
- ADP-001, DAT-001, TEL-001 and STO-001 should start in parallel once FND-002 stabilizes.
- EVAL-001 and PERF-001 should progress in parallel rather than sequentially.
- UI and external framework bridges are kept off the engine MVP critical path.

Roadmap impact:

- M0-M3 define the engine MVP foundation.
- M4 adds workload-specific evaluation.
- M5 adds resource-aware local-device evidence.
- M6 turns the engine into a regression/CI system.
- M7-M9 expand usability and ecosystem only after core evidence semantics stabilize.

## 2026-08-15 — Python foundation and dimension-specific compatibility fixed

Affected: FND-001, FND-002, M0, downstream ADP/DAT/TEL/STO/REG

Previous assumption:

- The primary language, schema library, license and exact comparability invariants were intentionally open until implementation began.
- A naive compatibility rule could have treated any execution-fingerprint difference as non-comparable.

Decision:

- Use Python 3.12+ with Pydantic v2, Ruff, mypy strict, pytest and a shared `python scripts/validate.py` local/CI gate.
- Adopt MIT licensing.
- Persist/export immutable versioned domain values; unsupported schema versions are rejected rather than guessed.
- Treat unknown identity as explicit null/not-observed state.
- Make raw endpoint credentials unrepresentable in persisted endpoint configuration.
- Compare fingerprints by result dimension: dataset/evaluator/template/protocol invariants for capability; hardware/load/protocol invariants for runtime; hardware/telemetry/protocol invariants for resource evidence.
- Do **not** automatically reject comparisons because model, quantization, runtime or generation configuration changed: those are expected experimental variables.

Reason / evidence:

- The product must evaluate differences between model/runtime/configuration choices, so full-fingerprint equality would defeat its core use case.
- Dataset/evaluator/hardware/measurement-protocol changes can create misleading deltas and therefore require typed non-comparability reasons.
- Python provides the lowest-friction path to benchmark/dataset ecosystems while keeping model serving external.
- Immutable schema-first values let storage, adapters and telemetry lanes proceed independently without coupling the domain to a database or transport.

Dependency impact:

- FND-002 now unlocks FND-003, ADP-001, DAT-001, TEL-001 and STO-001 in parallel.
- STO-002/REG-001 must consume the domain compatibility contract rather than inventing separate rules.
- PERF-001 can begin as soon as ADP-001 defines normalized streaming events.
- Release reproducibility still needs an exact dependency-lock strategy before a release candidate; this does not block M0 implementation.

Roadmap impact:

- M0 moves from planning-only into implementation/validation.
- No milestone scope changes; M0 still requires plugin/registry interfaces and deterministic fakes before exit.
