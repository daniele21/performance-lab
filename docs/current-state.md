# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Read when: determining what is integrated, what is blocked, what can start now, or what the next implementation block is
Last reviewed: 2026-08-15

This is the single operational ledger for AI Performance Lab. Keep it concise and current. Capability history belongs in [`roadmap.md`](roadmap.md); target behavior and dependencies belong in [`implementation-plan.md`](implementation-plan.md); material plan revisions belong in [`plan-changelog.md`](plan-changelog.md).

## Current phase

**M0 — Repository and contracts / planning foundation.**

No evaluation engine implementation is integrated yet. The repository currently contains the initial product, architecture, evaluation, telemetry and delivery specifications needed to begin implementation without coupling the lab to a specific LLM runtime.

## Integrated documentation baseline

The repository now defines:

- product boundary: evaluate external inference endpoints rather than host models in core;
- execution fingerprint as the primary reproducibility/comparison identity;
- separate capability, runtime-performance and resource-efficiency dimensions;
- black-box endpoint evaluation as the minimum integration level;
- optional host/device/runtime telemetry as progressive instrumentation;
- dataset snapshot and deterministic sampling contracts;
- deterministic evaluator primitives plus optional judge-based evaluation;
- controlled versus uncontrolled cold-start semantics;
- immutable completed-run evidence;
- dimension-specific run compatibility;
- explicit baseline/regression semantics;
- workstream IDs, dependencies and parallel execution waves.

## Workstream status

| Task | Status | Can start? | Blocks / notes |
| --- | --- | --- | --- |
| FND-001 repository foundation | READY | yes | immediate next block |
| FND-002 domain schemas | PLANNED | after FND-001 skeleton decision | critical unlock for parallel lanes |
| FND-003 plugin/registry contracts | PLANNED | after FND-002 | parallel after schemas |
| FND-004 orchestrator lifecycle | PLANNED | after FND-002 + adapter interface | converges quality/perf/storage |
| ADP-001 OpenAI-compatible adapter | PLANNED | after FND-002 | can parallelize with DAT/TEL/STO |
| ADP-002 endpoint capability probe | PLANNED | after ADP-001 | not blocking basic non-streaming run if staged carefully |
| DAT-001 dataset/task schema | PLANNED | after FND-002 | parallel lane |
| DAT-002 starter general-purpose suite | PLANNED | after DAT-001 + evaluator primitives | content work can begin conceptually earlier |
| DAT-003 custom dataset import | PLANNED | after DAT-001 | parallel lane |
| DAT-004 workload packs | PLANNED | after custom import/evaluators | later practical-product milestone |
| EVAL-001 deterministic evaluators | PLANNED | after FND-003 + DAT-001 | parallel with PERF-001 |
| EVAL-002 judge/rubric evaluation | PLANNED | after score model stable | not MVP critical path |
| EVAL-003 external benchmark bridge | PLANNED | after native contracts stabilize | later integration lane |
| PERF-001 single-request protocol | PLANNED | after adapter/core schemas | parallel with EVAL-001 |
| PERF-002 throughput/concurrency | PLANNED | after PERF-001 | later Wave 2 |
| PERF-003 statistics/repeatability | PLANNED | after PERF-001 | can parallelize with PERF-002 |
| TEL-001 telemetry collector contract | PLANNED | after measurement schema | optional parallel lane |
| TEL-002 local host collector | PLANNED | after TEL-001 | not MVP critical path |
| TEL-003 instrumented endpoint telemetry | PLANNED | after TEL-001 + capability model | integration can proceed independently |
| STO-001 immutable run store | PLANNED | after FND-002 | parallel lane |
| STO-002 compatible comparison queries | PLANNED | after store + result models | converges M1/M2/M3 |
| STO-003 retention/artifact policy | PLANNED | after STO-001 | parallel with result engine |
| CLI-001 inspect/probe commands | PLANNED | after interfaces; fakes permitted | early developer surface |
| CLI-002 run command | PLANNED | after orchestrator + one result path | MVP critical path |
| CLI-003 automation mode | PLANNED | after regression engine | CI prerequisite |
| REG-001 baseline/compatibility engine | PLANNED | after STO-002 | regression critical path |
| REG-002 policy file | PLANNED | after REG-001 | parallel with UI/custom workload |
| REG-003 CI integration | PLANNED | after CLI-003 + policy | engineering-platform milestone |
| UI-001 run setup IA | PLANNED | mock/prototype work can start early | implementation waits for read models |
| UI-002 comparison visualization | PLANNED | after comparison engine | not engine MVP critical path |

## Parallel work available after FND-002

Once the core schemas and interface boundaries are stable enough, these streams should **not** be serialized:

```text
Stream A: ADP-001  inference adapter
Stream B: DAT-001  dataset/task model
Stream C: TEL-001  telemetry contract
Stream D: STO-001  run persistence
Stream E: CLI-001  command scaffolding against fakes
```

After ADP-001 + DAT-001/FND-003 mature:

```text
Stream F: EVAL-001 quality evaluators
Stream G: PERF-001 runtime measurement
Stream H: STO-003 retention/evidence policy
Stream I: TEL-002 host telemetry
```

FND-004 then converges these into the first end-to-end run.

## Immediate next implementation block

1. **FND-001** — choose implementation stack and create the reproducible repository skeleton.
2. **FND-002** — implement/version the canonical domain schemas and compatibility model.
3. As soon as FND-002 is stable enough, begin **ADP-001, DAT-001, TEL-001 and STO-001 in parallel**.

Do not start the UI implementation or external benchmark-framework integration before the domain/read models are sufficiently stable.

## Open architectural decisions

These are not blockers for documentation but are blockers for implementation details in FND-001/FND-002:

- primary implementation language/runtime;
- dependency/environment management;
- local database/artifact storage technology;
- schema validation/serialization library;
- configuration file format;
- plugin discovery/registration approach;
- local API/UI topology;
- first instrumented telemetry transport.

The chosen decisions should be captured in ADRs once implementation begins.

## Known blockers

No external blocker exists yet. Current blockers are intentional sequencing dependencies:

- implementation work beyond skeleton cannot safely fan out until FND-002 defines stable core identities;
- comparable regression cannot precede immutable run/fingerprint semantics;
- meaningful TTFT cannot be claimed for non-streaming endpoints;
- resource efficiency cannot be claimed when telemetry scope/provenance is unknown.

## Deferred

- additional model/provider adapters beyond the reference endpoint contract;
- distributed runners;
- public leaderboard;
- multimodal/ASR/embeddings/reranking;
- automatic model serving/download;
- arbitrary generated-code execution;
- energy ranking across incomparable devices/sensors.

## Update protocol

When a task changes state:

1. update the table above;
2. update `Immediate next implementation block` if the critical path changed;
3. update [`roadmap.md`](roadmap.md) only when milestone outcome/status changes;
4. update [`implementation-plan.md`](implementation-plan.md) only when scope/dependency/acceptance criteria change;
5. append to [`plan-changelog.md`](plan-changelog.md) for every material plan change, not for routine status movement.
