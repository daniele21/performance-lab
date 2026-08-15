# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Read when: determining what is integrated, what is blocked, what can start now, or what the next implementation block is
Last reviewed: 2026-08-15

This is the single operational ledger for AI Performance Lab. Capability history belongs in [`roadmap.md`](roadmap.md); target behavior and dependencies belong in [`implementation-plan.md`](implementation-plan.md); material plan revisions belong in [`plan-changelog.md`](plan-changelog.md).

## Current phase

**M0 is complete. M1, M2, M3, M4, M5 and M6 are active; the engine implementation has reached regression automation.**

The integrated `dev` line now contains the stable domain/plugin foundation, OpenAI-compatible black-box execution, evidence-based capability probing, deterministic and optional rubric evaluation, a bundled diagnostic suite, custom dataset mapping, single-request and load protocols, repeatability statistics, host and runtime-native telemetry, immutable SQLite/ZIP evidence, compatible comparison, retention policy, executable `run` CLI, explicit baselines and versioned regression policies.

The remaining critical-path implementation is **CLI-003 machine-readable automation**, followed by **REG-003 CI integration**. Product evidence remains deliberately separate from implementation status: representative real-endpoint runs, load/repeatability evidence and device/runtime correlation are still required before claiming the corresponding product milestones complete.

## Integration lines

- `main` remains the stable/release-oriented line.
- `dev` is the canonical integration line for ongoing implementation.
- Parallel work branches from the latest green `dev` and targets `dev` through a PR.
- Promotion from `dev` to `main` is deliberate and should follow milestone/release evidence rather than routine feature completion.

## Integrated capability baseline

### Foundation — DONE

- **FND-001**: Python 3.12+ package/toolchain, Ruff, mypy strict, pytest and GitHub Actions validation on 3.12/3.13.
- **FND-002**: immutable/versioned domain schemas, canonical fingerprints and dimension-specific comparability.
- **FND-003**: narrow plugin protocols, explicit registry and deterministic fakes.
- **FND-004**: evaluation lifecycle, content-safe progress, typed failures and immutable terminal publication.

### Endpoint, datasets and evaluation — implementation slice DONE

- **ADP-001**: OpenAI-compatible probe/generation/SSE streaming, auth-by-env, usage/error normalization and cancellation.
- **ADP-002**: declared/observed/effective capability evidence with explicit `UNKNOWN` semantics and optional active checks.
- **DAT-001**: JSONL/CSV loading, explicit mapping, split filtering, seeded sampling and exact-sample SHA-256 identity.
- **DAT-002**: authored-in-repository diagnostic starter suite across instruction following, factual QA, reasoning, math, classification and structured JSON.
- **DAT-003**: versioned reusable custom-dataset import mapping plus source-shape inspection without semantic field guessing.
- **EVAL-001**: deterministic evaluators and score aggregation.
- **EVAL-002**: optional rubric/LLM judge with explicit judge model, rubric, prompt-template and generation provenance; deterministic scoring remains the default.

### Runtime and telemetry — implementation slice DONE

- **PERF-001**: setup/total latency, streaming TTFT and token throughput with available/unavailable semantics and cold/warm classification.
- **PERF-002**: fixed-count/bounded-duration concurrency profiles, throughput/reliability and queue-delay/backpressure evidence.
- **PERF-003**: repeatability summaries, raw samples and qualified percentile reporting.
- **TEL-001**: optional collector lifecycle and failure isolation.
- **TEL-002**: stdlib host/process CPU, RSS/load where available and collector overhead.
- **TEL-003**: optional versioned runtime-native telemetry handshake with runtime/model/hardware identity and `RUNTIME` provenance.

No unavailable metric is silently represented as zero.

### Persistence, comparison and regression — implementation slice DONE through REG-002

- **STO-001**: SQLite working/completed separation, atomic immutable publication and portable ZIP evidence bundles with integrity checks.
- **STO-002**: identity-first compatible run comparison and per-dimension deltas only when interpretable.
- **STO-003**: versioned pre-publication evidence retention; raw prompt/output content remains structurally non-persistable.
- **CLI-001**: endpoint `probe` and run/fingerprint `inspect`.
- **CLI-002**: end-to-end `run --config` path from endpoint probe through starter suite/orchestrator to SQLite and `.plab.zip`.
- **REG-001**: explicit immutable baseline binding and compatibility-first regression read model.
- **REG-002**: versioned threshold policy with `PASS`, `FAIL`, `NOT_COMPARABLE` and `NOT_EVALUATED` semantics.

## Validation evidence

Every task marked `DONE` below passed the repository gate on Python 3.12 and 3.13 before merge:

```text
ruff format --check
ruff check
mypy --strict
pytest
```

Offline integration tests exercise real local HTTP boundaries where appropriate, including OpenAI-compatible streaming, end-to-end CLI execution and runtime-native telemetry. This is **implementation evidence**, not representative benchmark-product evidence.

Still required for product evidence:

- representative real local-model endpoint runs through the whole lifecycle;
- repeated/load runs showing protocol repeatability and saturation behavior;
- runtime/device correlation against a real serving stack;
- CI regression evidence once CLI-003/REG-003 are integrated.

## Workstream status

| Task | Status | Can start? | Blocks / notes |
| --- | --- | --- | --- |
| FND-001 repository foundation | DONE | — | validated foundation |
| FND-002 domain schemas | DONE | — | fingerprint + compatibility owner |
| FND-003 plugin/registry contracts | DONE | — | shared extension boundary + fakes |
| FND-004 orchestrator lifecycle | DONE | — | lifecycle integrated |
| ADP-001 OpenAI-compatible adapter | DONE | — | reference transport integrated |
| ADP-002 endpoint capability probe | DONE | — | evidence-based capability states |
| DAT-001 dataset/task loading | DONE | — | deterministic materialization |
| DAT-002 starter general-purpose suite | DONE | — | diagnostic, not universal ranking |
| DAT-003 custom dataset import | DONE | — | reusable explicit mapping/config |
| DAT-004 workload packs | READY | yes | DAT-003 + EVAL-002 now integrated |
| EVAL-001 deterministic evaluators | DONE | — | objective scoring baseline |
| EVAL-002 judge/rubric evaluation | DONE | — | optional and provenance-rich |
| EVAL-003 external benchmark bridge | PLANNED | later | after native evidence stabilizes |
| PERF-001 single-request protocol | DONE | — | timing boundary integrated |
| PERF-002 throughput/concurrency | DONE | — | load/backpressure protocol integrated |
| PERF-003 statistics/repeatability | DONE | — | qualified percentiles integrated |
| TEL-001 telemetry collector contract | DONE | — | optional lifecycle |
| TEL-002 local host collector | DONE | — | host/process evidence |
| TEL-003 instrumented endpoint telemetry | DONE | — | runtime-native protocol integrated |
| STO-001 immutable run store | DONE | — | SQLite + portable bundle |
| STO-002 compatible comparison queries | DONE | — | identity-first deltas |
| STO-003 retention/artifact policy | DONE | — | pre-publication evidence minimization |
| CLI-001 inspect/probe commands | DONE | — | developer inspection surface |
| CLI-002 run command | DONE | — | executable end-to-end quality run |
| CLI-003 automation mode | IN PROGRESS | active | JSON schema + stable exit-code gate under CI validation |
| REG-001 baseline/compatibility engine | DONE | — | explicit immutable baseline |
| REG-002 policy file | DONE | — | compatibility-aware threshold policy |
| REG-003 CI integration | READY | after CLI-003 merge | final Wave-3 convergence |
| UI-001 run setup IA | PLANNED | prototype possible | not engine critical path |
| UI-002 comparison visualization | READY | yes | read models now stable enough for implementation |

## Parallel work now unlocked

```text
                 integrated engine + regression policy
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
       CLI-003             DAT-004              UI-002
 automation gate        workload packs      compare/regression UI
          │
          ▼
       REG-003
      CI integration
```

`EVAL-003` and additional transport/device adapters remain intentionally deferred until native end-to-end evidence demonstrates a concrete coverage gap.

## Immediate next implementation block

1. **CLI-003** — finish validation of stable JSON automation output and deterministic exit codes.
2. **REG-003** — publish CI-friendly summary + machine-readable result while preserving hardware comparability semantics.
3. In parallel, **DAT-004** may begin with the first versioned practical workload pack; **UI-002** may consume the now-stable comparison/regression read models.
4. After the critical path is green, run a representative endpoint evidence campaign instead of adding more abstraction by default.

## Resolved architectural decisions

- Python 3.12+ core; PEP 621 + setuptools.
- Pydantic v2 immutable/versioned domain values.
- Explicit plugin registry/protocol boundaries rather than import-time magic discovery.
- OpenAI-compatible API as reference transport, not product ownership boundary.
- SQLite local persistence with working versus immutable completed evidence.
- Portable ZIP evidence bundle independent from SQLite internals.
- Deterministic evaluators first; judge/rubric evaluation opt-in with explicit provenance.
- Black-box evaluation remains valid without telemetry.
- Runtime-native telemetry is optional and separately provenance-tagged.
- Dataset mapping is explicit; source inspection does not guess semantic columns.
- Baselines are explicit and immutable; no implicit latest-run baseline.
- Compatibility is evaluated before deltas/thresholds.
- Regression policies are versioned; unknown direction/evidence yields `NOT_EVALUATED`, not an invented verdict.
- Raw prompt/output content is not part of persisted `Run` evidence.

Still intentionally open:

- dependency lock/release reproducibility mechanism before release candidate;
- local UI/control-plane topology;
- first workload-pack composition/versioning (`DAT-004`);
- representative real-endpoint/device evidence campaign;
- whether `REG-003` ships in v0.1 or immediately after, based on final CI runner-identity semantics.

## Known blockers / evidence gaps

No external implementation blocker is active. Remaining constraints are evidence/product gates:

- M1 requires a representative real endpoint completing the frozen lifecycle;
- M2 requires repeatability/load evidence on a representative endpoint, not only protocol tests;
- M3 needs representative compatible/incompatible run comparison evidence beyond fixtures;
- M4 needs at least one practical workload pack;
- M5 needs first real runtime/device integration evidence;
- M6 needs CLI-003 + REG-003 and a CI run demonstrating safe comparability behavior.

## Update protocol

When a task changes state:

1. update the table above;
2. update `Immediate next implementation block` if the critical path changed;
3. update [`roadmap.md`](roadmap.md) when milestone outcome/status changes;
4. update [`implementation-plan.md`](implementation-plan.md) only when scope/dependency/acceptance criteria change;
5. append to [`plan-changelog.md`](plan-changelog.md) for material plan changes, not routine status movement.
