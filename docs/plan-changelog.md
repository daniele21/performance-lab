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
