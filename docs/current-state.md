# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Read when: determining what is integrated, what is blocked, what can start now, or what the next implementation block is
Last reviewed: 2026-08-15

This is the single operational ledger for AI Performance Lab. Capability history belongs in [`roadmap.md`](roadmap.md); target behavior and dependencies belong in [`implementation-plan.md`](implementation-plan.md); material plan revisions belong in [`plan-changelog.md`](plan-changelog.md).

## Current phase

**M0 — Repository and contracts / in progress.**

FND-001 and FND-002 are complete. The executable Python foundation and canonical immutable domain contracts passed the clean-checkout repository gate on Python 3.12 and 3.13. The next M0 work is the plugin/registry boundary and deterministic fakes, while adapter, dataset, telemetry and storage lanes can now proceed independently.

## Integration lines

- `main` is the stable, release-oriented line.
- `dev` is the canonical integration line for ordinary feature, fix, dependency, documentation and UX/UI work once created from this validated foundation.
- Parallel work should branch from the latest green `dev` and target `dev`.
- Promotion from validated `dev` to `main` is deliberate; ordinary work should no longer land directly on `main` after the bootstrap phase.

## Integrated implementation baseline

### FND-001 — repository foundation — DONE

- Python 3.12+ `src/` package layout;
- PEP 621 project metadata and setuptools build backend;
- bounded runtime/development dependencies;
- Pydantic v2 as the domain validation/serialization dependency;
- Ruff formatting/linting, mypy strict and pytest;
- `python scripts/validate.py` as the shared local/CI validation command;
- GitHub Actions matrix on Python 3.12 and 3.13;
- MIT license;
- contribution and branch/integration policy;
- no model runtime, HTTP client, database, CLI or UI dependency in core.

### FND-002 — canonical domain contracts — DONE

Implemented immutable strict schemas for:

- `Target` and `EndpointProfile`;
- `ExecutionFingerprint`;
- `EvaluationSuite`, `TaskSpec` and `DatasetSnapshot`;
- `Run` and `SampleExecution`;
- `Measurement` and `Score`;
- model/runtime/hardware/generation/load/telemetry identity values.

Also integrated:

- schema version `1`;
- deterministic canonical JSON and SHA-256 fingerprint identity;
- unsupported-version rejection rather than guessed migration;
- explicit `null = unknown/not observed` semantics for optional identity fields;
- authentication by environment-variable reference only; raw credentials are not representable;
- dimension-specific typed compatibility results.

Initial compatibility invariants:

- capability comparison requires matching dataset snapshots, evaluator versions, prompt-template version and benchmark protocol;
- runtime comparison requires matching hardware identity, load profile and benchmark protocol;
- resource comparison requires matching hardware identity plus telemetry level/protocol/collector identity and benchmark protocol;
- model, quantization, runtime and generation settings may differ because they are valid experimental variables.

These decisions are recorded in ADR 0001 and ADR 0002.

## Validation evidence

The foundation is merge-ready against the current repository gate:

- 10 deterministic domain tests cover serialization round-trip, stable fingerprints, unknown/null semantics, schema rejection, capability/runtime/resource compatibility, lifecycle validation and immutability;
- GitHub Actions run `31879526929` passed the full `python scripts/validate.py` gate on Python 3.12 and 3.13 at commit `d118c02e1fc451659e42e81216f885b691c2a5ad`;
- the gate includes Ruff format, Ruff lint, mypy strict and pytest from a clean checkout.

This evidence closes FND-001 and FND-002. It does not yet prove real endpoint behavior, runtime performance or device telemetry.

## Workstream status

| Task | Status | Can start? | Blocks / notes |
| --- | --- | --- | --- |
| FND-001 repository foundation | DONE | — | clean-checkout CI green on 3.12/3.13 |
| FND-002 domain schemas | DONE | — | immutable/versioned contracts + compatibility tests green |
| FND-003 plugin/registry contracts | READY | yes | next critical M0 block; owns extension interfaces and fakes |
| FND-004 orchestrator lifecycle | PLANNED | after FND-003 + ADP-001 interface | converges quality/perf/storage |
| ADP-001 OpenAI-compatible adapter | READY | yes | may run in parallel with DAT/TEL/STO |
| ADP-002 endpoint capability probe | PLANNED | after ADP-001 | staged after reference adapter |
| DAT-001 dataset/task loading | READY | yes | materialization/snapshot contract; do not duplicate FND schemas |
| DAT-002 starter general-purpose suite | PLANNED | after DAT-001 + evaluator primitives | content may be prepared independently |
| DAT-003 custom dataset import | PLANNED | after DAT-001 | parallel lane |
| DAT-004 workload packs | PLANNED | after custom import/evaluators | later practical-product milestone |
| EVAL-001 deterministic evaluators | PLANNED | after FND-003 + DAT-001 | parallel with PERF-001 |
| EVAL-002 judge/rubric evaluation | PLANNED | after score model stable | not MVP critical |
| EVAL-003 external benchmark bridge | PLANNED | after native contracts stabilize | later integration lane |
| PERF-001 single-request protocol | READY | after normalized ADP event interface | can develop against adapter fake |
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

```text
                 validated FND-002
                       │
        ┌──────────────┼──────────────┬──────────────┬──────────────┐
        ▼              ▼              ▼              ▼              ▼
     FND-003         ADP-001        DAT-001        TEL-001        STO-001
   interfaces       inference       datasets       telemetry      persistence
   + fakes          adapter         loading        contract       store
        │              │
        └──────┬───────┘
               ▼
            FND-004
          orchestrator
```

`PERF-001` can start as soon as ADP-001 exposes the normalized streaming event contract; it does not need to wait for the complete OpenAI-compatible implementation.

## Immediate next implementation block

Start five independent streams from the validated foundation:

1. **FND-003** — plugin/registry protocols and deterministic fakes;
2. **ADP-001** — OpenAI-compatible non-streaming/streaming adapter and normalized events;
3. **DAT-001** — dataset record loading, deterministic materialization and snapshot identity;
4. **TEL-001** — collector lifecycle, availability and provenance contracts;
5. **STO-001** — immutable completed-run persistence and partial working-state boundary.

Then begin `PERF-001` against the ADP fake/interface and converge toward `FND-004` only after a deterministic adapter + dataset/evaluator path exists.

Do not start production UI implementation or external benchmark-framework integration yet.

## Open architectural decisions

Resolved:

- primary language/runtime: Python 3.12+;
- build/package metadata: PEP 621 + setuptools;
- domain validation/serialization: Pydantic v2;
- initial license: MIT;
- immutable/versioned domain and dimension-specific comparability strategy.

Still open in their owning workstreams:

- plugin discovery/registration mechanism (`FND-003`);
- durable run database/artifact storage technology (`STO-001`);
- configuration file format (`CLI`/orchestrator);
- local API/UI process topology (`UI`/control plane);
- first instrumented telemetry transport (`TEL-003`);
- exact dependency-lock/release reproducibility mechanism before a release candidate.

## Known blockers

No external blocker exists. Remaining constraints are architectural/evidence-related:

- FND-004 requires FND-003 plus the ADP-001 inference interface;
- meaningful TTFT cannot be claimed for non-streaming endpoints;
- resource efficiency cannot be claimed when telemetry scope/provenance is unknown;
- comparison queries must consume, not duplicate, domain compatibility semantics;
- real endpoint, load and device claims require later integration evidence.

## Update protocol

When a task changes state:

1. update the table above;
2. update `Immediate next implementation block` if the critical path changed;
3. update [`roadmap.md`](roadmap.md) only when milestone outcome/status changes;
4. update [`implementation-plan.md`](implementation-plan.md) only when scope/dependency/acceptance criteria change;
5. append to [`plan-changelog.md`](plan-changelog.md) for every material plan change, not routine status movement.
