# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Read when: determining what is integrated, what is blocked, what can start now, or what the next implementation block is
Last reviewed: 2026-08-15

This is the single operational ledger for AI Performance Lab. Capability history belongs in [`roadmap.md`](roadmap.md); target behavior and dependencies belong in [`implementation-plan.md`](implementation-plan.md); material plan revisions belong in [`plan-changelog.md`](plan-changelog.md).

## Current phase

**M0 — Repository and contracts / implementation in validation.**

The repository now contains the executable Python foundation and canonical immutable domain contracts. The first network adapter, dataset loader, telemetry collector and durable store are not integrated yet.

## Integrated implementation baseline

### Repository foundation

- Python 3.12+ `src/` package layout;
- PEP 621 project metadata with bounded runtime/dev dependencies;
- Pydantic v2 as the domain validation/serialization dependency;
- Ruff + mypy strict + pytest repository gate;
- `python scripts/validate.py` as the shared local/CI validation command;
- GitHub Actions validation on Python 3.12 and 3.13;
- MIT license;
- contribution and branch/integration policy;
- no model runtime, HTTP client, database, CLI or UI dependency in core.

### Canonical domain contracts

Implemented immutable strict schemas for:

- `Target`;
- `EndpointProfile`;
- `ExecutionFingerprint`;
- `EvaluationSuite`;
- `DatasetSnapshot`;
- `Run`;
- `SampleExecution`;
- `Measurement`;
- `Score`;
- generation/load/telemetry/model/runtime/hardware identities.

Also integrated:

- schema version `1`;
- deterministic canonical JSON and SHA-256 fingerprint identity;
- unsupported-version rejection rather than guessed migration;
- explicit `null = unknown/not observed` semantics for optional identity fields;
- authentication by environment-variable reference only; raw credentials are not representable;
- dimension-specific typed compatibility results.

### Initial compatibility invariants

- capability comparison requires matching dataset snapshots, evaluator versions, prompt-template version and benchmark protocol;
- runtime comparison requires matching hardware identity, load profile and benchmark protocol;
- resource comparison requires matching hardware identity plus telemetry level/protocol/collector identity and benchmark protocol;
- model, quantization, runtime and generation settings may differ because they are valid experimental variables.

These decisions are recorded in ADR 0001 and ADR 0002.

## Validation evidence

Locally exercised before integration:

- Python compilation;
- 10 deterministic domain tests covering round-trip serialization, stable fingerprints, unknown/null semantics, schema rejection, capability/runtime/resource compatibility, immutable values and lifecycle validation.

Repository-wide Ruff/mypy/pytest CI must still confirm the clean-checkout gate on the committed tree before FND-001/FND-002 move from `VALIDATION` to `DONE`.

## Workstream status

| Task | Status | Can start? | Blocks / notes |
| --- | --- | --- | --- |
| FND-001 repository foundation | VALIDATION | yes | implementation committed; waiting clean-checkout CI |
| FND-002 domain schemas | VALIDATION | yes | implementation + tests committed; waiting clean-checkout CI |
| FND-003 plugin/registry contracts | READY | yes | next critical M0 block |
| FND-004 orchestrator lifecycle | PLANNED | after FND-003 + ADP-001 interface | converges quality/perf/storage |
| ADP-001 OpenAI-compatible adapter | READY | yes | may run in parallel with DAT/TEL/STO |
| ADP-002 endpoint capability probe | PLANNED | after ADP-001 | staged after reference adapter |
| DAT-001 dataset/task schema | READY | yes | extend domain with load/materialization contracts, not duplicate FND models |
| DAT-002 starter general-purpose suite | PLANNED | after DAT-001 + evaluator primitives | content may be prepared independently |
| DAT-003 custom dataset import | PLANNED | after DAT-001 | parallel lane |
| DAT-004 workload packs | PLANNED | after custom import/evaluators | later practical-product milestone |
| EVAL-001 deterministic evaluators | PLANNED | after FND-003 + DAT-001 | parallel with PERF-001 |
| EVAL-002 judge/rubric evaluation | PLANNED | after score model stable | not MVP critical |
| EVAL-003 external benchmark bridge | PLANNED | after native contracts stabilize | later integration lane |
| PERF-001 single-request protocol | READY | yes after ADP interface portion | can develop against adapter fake |
| PERF-002 throughput/concurrency | PLANNED | after PERF-001 | Wave 2 |
| PERF-003 statistics/repeatability | PLANNED | after PERF-001 | parallel with PERF-002 |
| TEL-001 telemetry collector contract | READY | yes | optional parallel lane |
| TEL-002 local host collector | PLANNED | after TEL-001 | not MVP critical |
| TEL-003 instrumented endpoint telemetry | PLANNED | after TEL-001 + capability model | independent integration |
| STO-001 immutable run store | READY | yes | persistence technology decision belongs here |
| STO-002 compatible comparison queries | PLANNED | after STO-001 | consumes FND compatibility results |
| STO-003 retention/artifact policy | PLANNED | after STO-001 | parallel with result engine |
| CLI-001 inspect/probe commands | PLANNED | after FND-003/ADP interface; fakes permitted | early developer surface |
| CLI-002 run command | PLANNED | after orchestrator + result path | MVP critical |
| CLI-003 automation mode | PLANNED | after regression engine | CI prerequisite |
| REG-001 baseline/compatibility engine | PLANNED | after STO-002 | regression critical path |
| REG-002 policy file | PLANNED | after REG-001 | parallel with UI/custom workload |
| REG-003 CI integration | PLANNED | after CLI-003 + policy | engineering-platform milestone |
| UI-001 run setup IA | PLANNED | prototype work can start early | implementation waits for read models |
| UI-002 comparison visualization | PLANNED | after comparison engine | not engine MVP critical |

## Parallel work now unlocked

FND-002 has stabilized enough to begin separate implementation lanes without serializing them:

```text
Stream A: FND-003  plugin/registry contracts + deterministic fakes
Stream B: ADP-001  OpenAI-compatible inference adapter
Stream C: DAT-001  dataset/task loading and snapshot materialization
Stream D: TEL-001  telemetry collector interface
Stream E: STO-001  immutable run persistence
```

`PERF-001` may begin against the ADP interface/fake as soon as the streaming event contract is defined.

## Immediate next implementation block

1. Confirm clean-checkout CI for FND-001/FND-002 and close them if green.
2. Start **FND-003, ADP-001, DAT-001, TEL-001 and STO-001 in parallel**.
3. Keep FND-003 contract changes small; shared-domain changes must land before dependent lanes diverge.
4. Begin PERF-001 against the normalized adapter event contract once ADP-001 defines it.
5. Converge the lanes into FND-004 only after at least one adapter + dataset/evaluator path can be exercised deterministically.

Do not start production UI implementation or external benchmark-framework integration yet.

## Open architectural decisions

Resolved:

- primary language/runtime: Python 3.12+;
- build/package metadata: PEP 621 + setuptools;
- domain validation/serialization: Pydantic v2;
- initial license: MIT;
- immutable/versioned domain and dimension-specific comparability strategy.

Still open in their owning workstreams:

- durable run database/artifact storage technology (`STO-001`);
- configuration file format (`CLI`/orchestrator);
- plugin discovery/registration mechanism (`FND-003`);
- local API/UI process topology (`UI`/control plane);
- first instrumented telemetry transport (`TEL-003`);
- exact dependency-lock/release reproducibility mechanism before a release candidate.

## Known blockers

No external blocker exists. Remaining blockers are sequencing/evidence constraints:

- FND-001/FND-002 require clean-checkout CI before `DONE`;
- FND-004 requires the plugin boundary plus inference adapter interface;
- meaningful TTFT cannot be claimed for non-streaming endpoints;
- resource efficiency cannot be claimed when telemetry scope/provenance is unknown;
- comparison queries must not reimplement compatibility semantics outside the domain owner.

## Update protocol

When a task changes state:

1. update the table above;
2. update `Immediate next implementation block` if the critical path changed;
3. update [`roadmap.md`](roadmap.md) only when milestone outcome/status changes;
4. update [`implementation-plan.md`](implementation-plan.md) only when scope/dependency/acceptance criteria change;
5. append to [`plan-changelog.md`](plan-changelog.md) for every material plan change, not routine status movement.
