# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Read when: determining what is integrated, what is blocked, what can start now, or what the next implementation block is
Last reviewed: 2026-08-15

This is the single operational ledger for AI Performance Lab. Capability history belongs in [`roadmap.md`](roadmap.md); target behavior and dependencies belong in [`implementation-plan.md`](implementation-plan.md); material plan revisions belong in [`plan-changelog.md`](plan-changelog.md).

## Current phase

**M0 is complete. The planned engine/regression implementation path through DAT-004 and REG-003 is integrated on `dev`. M1-M6 remain evidence-gated rather than implementation-blocked.**

The integrated line now covers:

- runtime-agnostic domain/fingerprint/plugin contracts and orchestration;
- OpenAI-compatible black-box inference with evidence-based capability probing;
- deterministic local datasets, custom mappings, a generic diagnostic suite and a first versioned workload pack;
- deterministic evaluators plus optional provenance-rich rubric judging;
- single-request, repeatability and concurrent load protocols;
- optional host and runtime-native telemetry with explicit provenance;
- immutable SQLite evidence, portable bundles, retention policy and compatible comparison;
- executable `run`, explicit baseline regression, versioned threshold policy and CI-safe machine-readable automation.

There is **no active core implementation blocker**. The highest-value next work is a representative evidence campaign against real local inference endpoints/runtimes. New abstractions or integrations should be added only when that evidence reveals a concrete coverage gap.

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
- **DAT-002**: authored diagnostic starter suite across instruction following, factual QA, reasoning, math, classification and structured JSON.
- **DAT-003**: versioned reusable custom-dataset import mapping plus source-shape inspection without semantic field guessing.
- **DAT-004**: versioned workload-pack contract plus first `structured-document-extraction` pack with schema and field-correctness evaluation.
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

### Persistence, comparison and regression automation — implementation slice DONE

- **STO-001**: SQLite working/completed separation, atomic immutable publication and portable ZIP evidence bundles with integrity checks.
- **STO-002**: identity-first compatible run comparison and per-dimension deltas only when interpretable.
- **STO-003**: versioned pre-publication evidence retention; raw prompt/output content remains structurally non-persistable.
- **CLI-001**: endpoint `probe` and run/fingerprint `inspect`.
- **CLI-002**: end-to-end `run --config` path from endpoint probe through suite/orchestrator to SQLite and `.plab.zip`.
- **CLI-003**: stable JSON regression gate and deterministic exit codes: PASS=0, FAIL=1, ERROR=2, NOT_COMPARABLE=3, NOT_EVALUATED=4.
- **REG-001**: explicit immutable baseline binding and compatibility-first regression read model.
- **REG-002**: versioned threshold policy with `PASS`, `FAIL`, `NOT_COMPARABLE` and `NOT_EVALUATED` semantics.
- **REG-003**: CI regression command, JSON artifact, GitHub Step Summary and reusable composite action; resource rules are forced to `NOT_COMPARABLE` on uncontrolled CI runners.

## Validation evidence

Every task marked `DONE` above passed the repository gate on Python 3.12 and 3.13 before merge:

```text
ruff format --check
ruff check
mypy --strict
pytest
```

Offline integration tests exercise real local HTTP boundaries where appropriate, including OpenAI-compatible streaming, end-to-end CLI execution, runtime-native telemetry and CI regression behavior. This is **implementation evidence**, not representative benchmark-product evidence.

## Evidence still required

The remaining milestone constraints are empirical:

- **M1**: a representative local-model endpoint must complete the frozen end-to-end lifecycle; retain fingerprint and bundle.
- **M2**: repeated and concurrent/load runs on a representative endpoint must demonstrate interpretable latency/TTFT/throughput/reliability and saturation behavior.
- **M3**: preserve representative compatible and incompatible real-run comparisons beyond fixtures.
- **M4**: execute the structured-document workload pack against representative models and preserve scenario evidence.
- **M5**: integrate runtime-native telemetry with at least one real local serving stack/device and validate correlation.
- **M6**: preserve at least one real CI regression-gate run demonstrating PASS/FAIL and safe NOT_COMPARABLE behavior.

## Workstream status

| Task | Status | Can start? | Notes |
| --- | --- | --- | --- |
| FND-001..004 | DONE | — | foundation + orchestrator complete |
| ADP-001..002 | DONE | — | reference endpoint + capability evidence |
| DAT-001..004 | DONE | — | generic/custom datasets + first workload pack |
| EVAL-001..002 | DONE | — | deterministic + optional judge |
| EVAL-003 external benchmark bridge | PLANNED | later | only after evidence shows a concrete coverage gap |
| PERF-001..003 | DONE | — | request/load/statistical protocols |
| TEL-001..003 | DONE | — | optional host + runtime-native telemetry |
| STO-001..003 | DONE | — | immutable storage/comparison/retention |
| CLI-001..003 | DONE | — | inspect/run/automation surfaces |
| REG-001..003 | DONE | — | baseline/policy/CI integration complete |
| UI-001 run setup IA | PLANNED | yes | not required for engine evidence |
| UI-002 comparison visualization | READY | yes | stable comparison/regression read models available |
| Release reproducibility / dependency lock | READY | yes | required before release candidate |

## Parallel work now unlocked

```text
                    integrated engine
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
  real endpoint        real runtime      real CI
 evidence campaign      telemetry       regression
          │               │                │
          └───────────────┬┴────────────────┘
                          ▼
                 release evidence set

 Parallel, non-blocking:
 UI-002 comparison UI / additional workload packs / release lock
```

## Immediate next block

1. **Representative endpoint evidence** — run the starter suite and structured-document pack against one or more real OpenAI-compatible local endpoints and preserve run bundles.
2. **Performance evidence** — repeat the same target with warm/cold and concurrent profiles to establish repeatability and saturation behavior.
3. **Real telemetry evidence** — attach the runtime-native protocol to a real local serving stack where possible; keep black-box runs valid when unavailable.
4. **Regression evidence** — select an explicit baseline and run `regress-ci` on a real candidate, preserving the JSON artifact and CI summary.
5. In parallel, prepare release reproducibility and/or UI-002; defer EVAL-003 until evidence demonstrates need.

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
- Workload packs compose normal suites/datasets/evaluators and do not branch the engine by scenario.
- Baselines are explicit and immutable; no implicit latest-run baseline.
- Compatibility is evaluated before deltas/thresholds.
- Regression policies are versioned; unknown direction/evidence yields `NOT_EVALUATED`, not an invented verdict.
- CI resource comparison is conservative by default unless runner identity is explicitly controlled.
- Raw prompt/output content is not part of persisted `Run` evidence.

Still intentionally open:

- dependency lock/release reproducibility mechanism before release candidate;
- local UI/control-plane topology;
- representative real-endpoint/device/CI evidence campaign;
- additional workload packs based on real use cases;
- external benchmark bridge only if native evidence exposes a coverage gap.

## Update protocol

When a task changes state:

1. update the table above;
2. update `Immediate next block` if priority changes;
3. update [`roadmap.md`](roadmap.md) when milestone outcome/status changes;
4. update [`implementation-plan.md`](implementation-plan.md) only when scope/dependency/acceptance criteria change;
5. append to [`plan-changelog.md`](plan-changelog.md) for material plan changes, not routine status movement.
