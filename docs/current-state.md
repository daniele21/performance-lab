# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Read when: determining what is integrated, what is blocked, what can start now, or what the next implementation block is
Last reviewed: 2026-08-15

This is the single operational ledger for AI Performance Lab. Capability history belongs in [`roadmap.md`](roadmap.md); target behavior and dependencies belong in [`implementation-plan.md`](implementation-plan.md); material plan revisions belong in [`plan-changelog.md`](plan-changelog.md).

## Current phase

**M0 is complete. The planned engine/regression path through DAT-004 and REG-003, CI reproducibility hardening, Local LLM Server telemetry integration and first-party execution-identity discovery are integrated on `dev`. M1-M6 remain primarily evidence-gated rather than implementation-blocked.**

The integrated line covers:

- runtime-agnostic domain/fingerprint/plugin contracts and orchestration;
- OpenAI-compatible black-box inference with evidence-based capability probing;
- deterministic local datasets, custom mappings, a generic diagnostic suite and a first versioned workload pack;
- deterministic evaluators plus optional provenance-rich rubric judging;
- single-request, repeatability and concurrent load protocols;
- optional host and runtime-native telemetry with explicit provenance;
- client-side runtime polling for `daniele21/local-llm-server` through `/status`;
- first-party Local LLM Server execution identity through `local-llm-identity-v1` and `GET /v1/runtime/identity`;
- immutable SQLite evidence, portable bundles, retention policy and compatible comparison;
- executable `run`, explicit baseline regression, versioned threshold policy and CI-safe machine-readable automation;
- constrained CI dependency snapshots validated on Python 3.12 and 3.13.

INT-002 maps observed Local LLM Server model artifact, runtime configuration and hardware identity into the immutable execution fingerprint before the evaluation lifecycle begins. The producer remains independent from Performance Lab and generic endpoints remain valid when the identity endpoint is unavailable.

There is **no active core implementation blocker**. The highest-value work is now a representative evidence campaign against real local models/runtimes/devices. New abstractions should be added only when that evidence reveals a concrete coverage gap.

## Integration lines

- `main` remains the stable/release-oriented line.
- `dev` is the canonical integration line for ongoing implementation.
- Parallel work branches from the latest green `dev` and targets `dev` through a PR.
- Promotion from `dev` to `main` is deliberate and should follow milestone/release evidence rather than routine feature completion.

## Integrated capability baseline

### Foundation — DONE

- **FND-001**: Python 3.12+ package/toolchain, Ruff, mypy strict, pytest and GitHub Actions validation on 3.12/3.13.
- **FND-002**: immutable/versioned domain schemas, canonical fingerprints and dimension-specific comparability. `RuntimeIdentity` carries an optional effective serving `config_digest` when explicitly observed.
- **FND-003**: narrow plugin protocols, explicit registry and deterministic fakes.
- **FND-004**: evaluation lifecycle, content-safe progress, typed failures and immutable terminal publication.

### Endpoint, datasets and evaluation — DONE

- **ADP-001..002**: OpenAI-compatible inference plus evidence-based capability discovery.
- **DAT-001..004**: deterministic JSONL/CSV/custom mappings, diagnostic starter suite and first versioned `structured-document-extraction` workload pack.
- **EVAL-001..002**: deterministic evaluators plus optional LLM/rubric judge with explicit provenance.

### Runtime, identity and telemetry — DONE for the implemented core

- **PERF-001**: setup/total latency, streaming TTFT and token throughput with available/unavailable semantics and cold/warm classification — DONE.
- **PERF-002**: fixed-count/bounded-duration concurrency profiles, throughput/reliability and queue-delay/backpressure evidence — DONE.
- **PERF-003**: repeatability summaries, raw samples and qualified percentile reporting — DONE.
- **TEL-001..003**: optional collector lifecycle, host/process evidence and generic runtime-native telemetry contract — DONE.
- **INT-001**: `local-llm-server` integration using the normal OpenAI-compatible inference API plus optional root-level `/status` polling, with `RUNTIME` provenance and no server-side Performance Lab dependency — DONE.
- **INT-002**: strict `local-llm-identity-v1` consumer, optional/required identity discovery, runtime config digest, hardware conflict detection and pre-run fingerprint freezing — **DONE**. The aligned Local LLM Server producer and Performance Lab consumer both passed their supported CI matrices and were merged to `dev`.

The serving and identity contracts are documented in [`local-llm-server-integration.md`](local-llm-server-integration.md) and [`local-llm-identity-contract.md`](local-llm-identity-contract.md).

### Persistence, comparison and regression automation — DONE

- **STO-001..003**: immutable SQLite publication, portable evidence bundles, compatible comparison and pre-publication retention policy.
- **CLI-001..003**: probe/inspect, end-to-end `run --config`, and machine-readable regression automation.
- **REG-001..003**: explicit immutable baseline, versioned threshold policy and CI regression gate with safe `NOT_COMPARABLE` semantics.
- **REL-001**: committed CI dependency constraints plus validation that direct dependencies and installed versions match the reproducibility snapshot on the supported Python matrix.

## Validation evidence

Every merged Performance Lab implementation slice above passed the repository gate on Python 3.12 and 3.13:

```text
ruff format --check
ruff check
mypy --strict
pytest
```

INT-002 has deterministic fake-server coverage for direct identity mapping, end-to-end fingerprint freezing, backward-compatible optional discovery and hardware conflicts. Its final consumer head passed the Python 3.12/3.13 repository gate. The aligned Local LLM Server producer also passed lint and deterministic tests on Python 3.10/3.11/3.12 before merge.

Offline integration tests exercise real local HTTP boundaries where appropriate, including OpenAI-compatible inference, end-to-end CLI execution, runtime telemetry, identity discovery and CI regression behavior. This is **implementation evidence**, not representative benchmark-product evidence.

## Evidence still required

The remaining milestone constraints are empirical:

- **M1**: a representative resident local model must complete the frozen end-to-end lifecycle; retain fingerprint and bundle, including discovered model/runtime/hardware identity when available.
- **M2**: repeated and concurrent/load runs on representative hardware must demonstrate interpretable latency/TTFT/throughput/reliability and saturation behavior.
- **M3**: preserve representative compatible and incompatible real-run comparisons beyond fixtures, including identity differences such as quantization/runtime config where available.
- **M4**: execute the structured-document workload pack against representative models and preserve scenario evidence.
- **M5**: run the integrated `local-llm-server` status collector and identity provider against an actual serving stack/device and validate the usefulness of both dynamic telemetry and frozen execution identity.
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
| TEL-001..003 | DONE | — | optional host + generic runtime-native telemetry |
| INT-001 local-llm-server telemetry | DONE | — | OpenAI inference + optional `/status` polling integrated |
| INT-002 local-llm-server identity | DONE | — | shared `local-llm-identity-v1` producer/consumer integrated and CI-green |
| STO-001..003 | DONE | — | immutable storage/comparison/retention |
| CLI-001..003 | DONE | — | inspect/run/automation surfaces |
| REG-001..003 | DONE | — | baseline/policy/CI integration complete |
| REL-001 CI reproducibility snapshot | DONE | — | constrained dependency environment validated on 3.12/3.13 |
| UI-001 run setup IA | PLANNED | yes | not required for evidence campaign |
| UI-002 comparison visualization | READY | yes | stable comparison/regression read models available |

## Parallel work now unlocked

```text
                    integrated engine
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
  real endpoint        real runtime      real CI
 evidence campaign   identity+telemetry  regression
          │               │                │
          └───────────────┬┴────────────────┘
                          ▼
                 release evidence set

 Parallel, non-blocking:
 UI-002 comparison UI / additional workload packs
```

## Immediate next block

1. **Representative endpoint evidence** — run the starter suite and structured-document pack against one or more actual `local-llm-server` resident models and preserve run bundles plus frozen identity.
2. **Performance evidence** — repeat the same target with warm/cold and concurrent profiles to establish repeatability and saturation behavior.
3. **Real runtime evidence** — preserve both `/v1/runtime/identity` and `/status`-derived evidence and determine whether their current boundaries are sufficient before extending either protocol.
4. **Regression evidence** — select an explicit baseline and run `regress-ci` on a real candidate, preserving JSON artifact and CI summary.
5. In parallel, progress UI-002 and/or additional workload packs; defer EVAL-003 until evidence demonstrates a real need.

## Resolved architectural decisions

- Python 3.12+ core; PEP 621 + setuptools.
- Pydantic v2 immutable/versioned domain values.
- Explicit plugin registry/protocol boundaries rather than import-time magic discovery.
- OpenAI-compatible API as reference transport, not product ownership boundary.
- SQLite local persistence with working versus immutable completed evidence.
- Portable ZIP evidence bundle independent from SQLite internals.
- Deterministic evaluators first; judge/rubric evaluation opt-in with explicit provenance.
- Black-box evaluation remains valid without telemetry or first-party identity discovery.
- Runtime-native telemetry is optional and separately provenance-tagged.
- `local-llm-server` remains independent: Performance Lab consumes public inference, optional `/status`, and optional versioned identity endpoints rather than adding a Performance Lab dependency to the server.
- Provider-specific response fields are never guessed into canonical identity.
- Local LLM Server is authoritative for identity fields it explicitly reports; conflicting explicit hardware metadata fails before fingerprint freeze.
- Dataset mapping is explicit; source inspection does not guess semantic columns.
- Workload packs compose normal suites/datasets/evaluators and do not branch the engine by scenario.
- Baselines are explicit and immutable; no implicit latest-run baseline.
- Compatibility is evaluated before deltas/thresholds.
- Regression policies are versioned; unknown direction/evidence yields `NOT_EVALUATED`, not an invented verdict.
- CI resource comparison is conservative by default unless runner identity is explicitly controlled.
- Raw prompt/output content is not part of persisted `Run` evidence.

Still intentionally open:

- local UI/control-plane topology;
- representative real-endpoint/device/CI evidence campaign;
- additional workload packs based on real use cases;
- external benchmark bridge only if native evidence exposes a coverage gap;
- a stronger cross-platform release lock mechanism only if the release process requires more than the current validated CI constraint snapshot.

## Update protocol

When a task changes state:

1. update the table above;
2. update `Immediate next block` if priority changes;
3. update [`roadmap.md`](roadmap.md) when milestone outcome/status changes;
4. update [`implementation-plan.md`](implementation-plan.md) only when scope/dependency/acceptance criteria change;
5. append to [`plan-changelog.md`](plan-changelog.md) for material plan changes, not routine status movement.
