# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Read when: determining what is integrated, what is blocked, what can start now, or what the next implementation block is
Last reviewed: 2026-08-15

This is the single operational ledger for AI Performance Lab. Capability history belongs in [`roadmap.md`](roadmap.md); target behavior and dependencies belong in [`implementation-plan.md`](implementation-plan.md); material plan revisions belong in [`plan-changelog.md`](plan-changelog.md).

## Current phase

**M0 is complete. M1, M2, M3 and M5 are now in parallel implementation.**

The repository has crossed the foundation boundary: domain contracts, extension interfaces, deterministic fakes, the reference OpenAI-compatible adapter, deterministic dataset materialization, deterministic evaluators, an evaluation orchestrator, single-request runtime measurement, optional host telemetry, immutable local persistence and the first developer CLI are integrated on `dev`.

The next critical objective is no longer infrastructure bootstrap. It is to turn these primitives into a repeatable end-to-end product path with endpoint capability discovery, a starter benchmark suite, repeated/load benchmarking, compatible run comparison and a CLI `run` command.

## Integration lines

- `main` remains the stable/release-oriented line.
- `dev` is the canonical integration line for ongoing implementation.
- Parallel work branches from the latest green `dev` and normally targets `dev` through a PR.
- Promotion from `dev` to `main` is deliberate and should follow a milestone/release evidence decision rather than routine feature completion.

## Integrated capability baseline

### Foundation — DONE

- **FND-001**: Python 3.12+ package, PEP 621/setuptools, Ruff, mypy strict, pytest, shared validation command, GitHub Actions 3.12/3.13, MIT and branch policy.
- **FND-002**: immutable/versioned Pydantic domain schemas, explicit unknown semantics, canonical serialization/fingerprints and dimension-specific comparability.
- **FND-003**: narrow plugin protocols, explicit registry and deterministic inference/dataset/evaluator/telemetry/exporter fakes.
- **FND-004**: evaluation lifecycle with frozen input validation, content-safe progress events, typed partial failures, optional telemetry, working-state persistence hooks and immutable terminal result publication.

M0 exit gate is satisfied: downstream lanes implement against shared contracts without importing each other's concrete implementations.

### Endpoint and dataset path — DONE for first slice

- **ADP-001**: OpenAI-compatible model probe, non-streaming chat completion, SSE streaming, environment-variable auth, usage normalization, typed transport/protocol errors and cooperative cancellation. Tests use a real local HTTP/SSE server.
- **DAT-001**: JSONL/CSV loading, explicit field mapping, split filtering, arbitrary sample caps, deterministic seeded sampling and SHA-256 identity of the exact selected record set.
- **EVAL-001**: deterministic exact/normalized match, numeric tolerance, classification accuracy, set precision/recall/F1, regex validity, JSON parsing/schema adherence, field extraction and score aggregation.

### Runtime and telemetry evidence — first slice DONE

- **PERF-001**: client-boundary request setup time, total latency, streaming TTFT, token usage and output-token throughput with explicit `available/unavailable` semantics and cold/warmup/measured-warm classification.
- **TEL-001**: optional collector lifecycle, typed availability/outcome and collector failure isolation.
- **TEL-002**: stdlib-only local host collector for attributable process CPU, CPU-core utilization, peak RSS where supported, host load where supported and collector overhead.

No metric is silently represented as zero when it is not observable.

### Persistence and developer control plane — first slice DONE

- **STO-001**: SQLite working/completed separation, atomic terminal publication, immutable completed-run conflicts and versioned portable ZIP bundles with SHA-256 integrity checks.
- **CLI-001**: `probe` for OpenAI-compatible endpoints and `inspect` for versioned `Run`/`ExecutionFingerprint` JSON, including JSON output for automation and credential references via environment-variable names only.

## Validation evidence

All completed implementation tasks above have individually passed the repository validation gate on Python 3.12 and 3.13 before merge. The combined `dev` integration also passed the full validation workflow after the second-wave merges.

The repository gate currently includes:

```text
ruff format --check
ruff check
mypy --strict
pytest
```

This is implementation evidence, not yet benchmark-product evidence. We still need representative end-to-end evaluation runs, repeatability/load evidence and comparison/regression validation before calling the engine MVP complete.

## Workstream status

| Task | Status | Can start? | Blocks / notes |
| --- | --- | --- | --- |
| FND-001 repository foundation | DONE | — | validated foundation |
| FND-002 domain schemas | DONE | — | fingerprint + compatibility owner |
| FND-003 plugin/registry contracts | DONE | — | shared extension boundary + fakes |
| FND-004 orchestrator lifecycle | DONE | — | end-to-end lifecycle primitive available |
| ADP-001 OpenAI-compatible adapter | DONE | — | reference transport integrated |
| ADP-002 endpoint capability probe | READY | yes | distinguish declared/observed/unknown support |
| DAT-001 dataset/task loading | DONE | — | deterministic materialization integrated |
| DAT-002 starter general-purpose suite | READY | yes | now unblocked by EVAL-001 |
| DAT-003 custom dataset import | READY | yes | extend reusable mapping/configuration UX/contracts |
| DAT-004 workload packs | PLANNED | after DAT-003 + workload templates | practical-product milestone |
| EVAL-001 deterministic evaluators | DONE | — | deterministic scoring baseline integrated |
| EVAL-002 judge/rubric evaluation | READY | yes, non-critical | keep isolated from deterministic score path |
| EVAL-003 external benchmark bridge | PLANNED | later | defer until native engine path is exercised end to end |
| PERF-001 single-request protocol | DONE | — | client-boundary timing integrated |
| PERF-002 throughput/concurrency | READY | yes | parallel with PERF-003 |
| PERF-003 statistics/repeatability | READY | yes | repeated-run statistics and confidence evidence |
| TEL-001 telemetry collector contract | DONE | — | optional lifecycle integrated |
| TEL-002 local host collector | DONE | — | portable host/process evidence integrated |
| TEL-003 instrumented endpoint telemetry | READY | yes, optional | runtime-native integration lane |
| STO-001 immutable run store | DONE | — | SQLite + portable bundle integrated |
| STO-002 compatible comparison queries | READY | yes | must consume domain compatibility rules |
| STO-003 retention/artifact policy | READY | yes | parallel with STO-002 |
| CLI-001 inspect/probe commands | DONE | — | developer surface integrated |
| CLI-002 run command | READY | yes | orchestrator + dataset + evaluator + store now available |
| CLI-003 automation mode | PLANNED | after REG-001/REG-002 | CI-facing command semantics |
| REG-001 baseline/compatibility engine | PLANNED | after STO-002 | next convergence point after comparison queries |
| REG-002 policy file | PLANNED | after REG-001 | parallel with later UI/workloads |
| REG-003 CI integration | PLANNED | after CLI-003 + policy | engineering-platform milestone |
| UI-001 run setup IA | PLANNED | prototype only | production implementation waits for run/read model to stabilize |
| UI-002 comparison visualization | PLANNED | after STO-002/REG-001 | not engine critical path |

## Parallel work now unlocked

The next wave should deliberately avoid serial execution:

```text
                         integrated engine primitives
                                   │
        ┌──────────────┬───────────┼───────────┬──────────────┬──────────────┐
        ▼              ▼           ▼           ▼              ▼              ▼
     ADP-002         DAT-002     PERF-002     PERF-003       STO-002        CLI-002
 capability map     starter      concurrency  statistics    comparison     run command
                    suite
        │              │           │           │              │              │
        └──────────────┴───────────┴───────────┴──────────────┴──────────────┘
                                   │
                         end-to-end engine evidence
                                   │
                              REG-001 next
```

Additional non-critical parallel lanes: `DAT-003`, `TEL-003`, `STO-003`, `EVAL-002`.

## Immediate next implementation block

Prioritize six independent streams:

1. **ADP-002** — capability discovery with observed/declared/unknown states and probe evidence;
2. **DAT-002** — small versioned general-purpose starter suite using deterministic evaluators;
3. **PERF-002** — fixed-concurrency/throughput protocol with reliability counters;
4. **PERF-003** — repeated-run statistics, percentiles and repeatability evidence;
5. **STO-002** — compatible comparison queries and identity diffs using the existing domain compatibility owner;
6. **CLI-002** — wire config → dataset snapshot → endpoint → orchestrator → store into a real executable run path.

These streams should run in parallel. `REG-001` starts when STO-002 is stable; the first engine-MVP integration scenario starts as soon as DAT-002 + CLI-002 are green.

## Resolved architectural decisions

- Python 3.12+ core;
- PEP 621 + setuptools;
- Pydantic v2 immutable/versioned domain values;
- explicit plugin registry/protocol boundaries rather than import-time magic discovery;
- OpenAI-compatible API as reference transport, not product ownership boundary;
- SQLite for first local run persistence;
- separate working versus immutable completed evidence;
- portable ZIP run bundle independent from SQLite internals;
- deterministic evaluators first; judge-based scoring optional;
- black-box evaluation works without host telemetry;
- unavailable runtime/resource metrics remain explicit rather than fabricated.

Still intentionally open:

- configuration file format for CLI-002;
- dependency lock/release reproducibility mechanism before release candidate;
- instrumented runtime telemetry transport (`TEL-003`);
- local UI/control-plane topology;
- exact starter-suite dataset composition and redistribution strategy (`DAT-002`).

## Known blockers / evidence gaps

No external blocker is active. Remaining constraints are product/evidence dependencies:

- M1 cannot close until a compact starter suite and richer capability probe exist and a representative endpoint completes the whole lifecycle;
- M2 requires repeatability/concurrency protocols beyond single-request timing;
- M3 requires comparison queries and identity-diff reporting beyond immutable storage;
- M5 requires runtime-native/device correlation before resource-aware evaluation is complete;
- regression automation cannot start before compatible comparison semantics are queryable end to end.

## Update protocol

When a task changes state:

1. update the table above;
2. update `Immediate next implementation block` if the critical path changed;
3. update [`roadmap.md`](roadmap.md) when milestone outcome/status changes;
4. update [`implementation-plan.md`](implementation-plan.md) only when scope/dependency/acceptance criteria change;
5. append to [`plan-changelog.md`](plan-changelog.md) for material plan changes, not routine status movement.
