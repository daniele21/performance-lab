# Incremental value delivery

Status: active
Owner: Performance Lab product delivery
Read when: selecting or implementing the next end-to-end value slice

## Goal

Deliver Performance Lab through small vertical slices that each unlock observable user value end to end, instead of completing capability areas M1-M6 sequentially before the product outcome can be exercised.

Each slice should, where applicable, cross the full path from user intent through execution and evidence to an interpretable result:

```text
UI / entry point -> canonical application/domain contract -> real or representative execution -> retained evidence -> user-visible result -> sufficient E2E evidence
```

M1-M9 in `docs/roadmap.md` remain the capability/maturity coverage map. This workstream owns delivery order and slice acceptance only. Detailed representative-device evidence remains owned by `representative-device-evidence.md`; Local LLM Server cutover detail remains owned by `local-llm-migration.md`.

## Non-goals

- Do not rebuild already-integrated M1-M7 capabilities merely to match the slice numbering.
- Do not add broad benchmark ecosystems, ASR, embeddings, reranking or vision before the current text-generation product exposes a concrete need.
- Do not move model serving, residency or runtime lifecycle ownership into Performance Lab.
- Do not make real-device claims from hosted fixtures or browser-only evidence.
- Do not require every later slice before shipping value from an earlier accepted slice.

## Invariants

- The product question remains: for this use case on this device, which available model + quantization + configuration is the best evidence-backed fit, and why?
- Quality, Performance and Resources remain separate; compatibility precedes rankings/deltas; unknown/unavailable evidence is never fabricated.
- Model + quantization + frozen configuration + endpoint/device/runtime identity remain explicit when known.
- Search ranges/capabilities come from canonical backend/runtime contracts; the browser never invents them.
- Every slice is accepted by the cheapest evidence environment sufficient for its claim; real-device claims require `REAL_ENVIRONMENT` evidence.
- A slice is `DONE` only when its user-visible loop, failure/recovery semantics, retained evidence and applicable validation agree.
- Parallel lanes must have explicit non-conflicting write ownership and one convergence gate; they must not implement competing sources of truth.

## Work graph

| ID | User value unlocked | Owns/writes | Depends on | Parallel | State |
| --- | --- | --- | --- | --- | --- |
| VALUE-01 | **Real single-model evidence loop** — one real target/model can be discovered, tested, inspected and exported | PL real-target integration/evidence path; representative evidence artifacts | current PRE_REAL readiness | internal A/B/C parallel lanes | ACTIVE |
| VALUE-02 | **Real model decision** — compare 2+ real candidates for one use case/device and return an explainable recommendation or explicit no-rank | campaign decision journey + real comparison evidence | VALUE-01 | no | BLOCKED |
| VALUE-03 | **Configuration decision** — answer which supported configuration should be used, not only which model | capability-backed optimization/search path + real config evidence | VALUE-02 | yes, with VALUE-04/08 | BLOCKED |
| VALUE-04 | **Device-aware decision** — device performance/resource evidence materially informs the trade-off | telemetry/resource provenance + result presentation | VALUE-02 | yes, with VALUE-03/08 | BLOCKED |
| VALUE-05 | **Confidence / repeatability** — recommendation includes controlled variability rather than one lucky run | repeated-load protocol/evidence + variability interpretation | VALUE-04 | yes, with late VALUE-03 | BLOCKED |
| VALUE-06 | **Regression workflow** — known-good baseline vs candidate produces an evidence-backed policy outcome | baseline/regression execution + retained real evidence | VALUE-02, VALUE-05 | no | BLOCKED |
| VALUE-07 | **LLS evaluation cutover** — Performance Lab fully owns new evaluation while LLS remains serving/runtime owner | cross-repo cutover; `local-llm-migration.md` is detailed owner | VALUE-03 + LLS EV-3 + real PL replacement evidence | no | BLOCKED |
| VALUE-08 | **Low-friction distribution** — normal users can launch/connect/evaluate without repo-development setup | packaging/launch/onboarding/product-owned connection flow | VALUE-02 | yes, with VALUE-03..07 | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

The graph is deliberately not a single chain. After VALUE-02, configuration optimization, device-aware evidence and distribution may proceed in parallel when ownership does not conflict.

## VALUE-01 execution graph

VALUE-01 is split only where ownership is independent. The first three lanes start from the same `dev` base and may merge in any order; the real-device execution is the single convergence gate.

| ID | Work | Owns/writes | Depends on | Parallel | State |
| --- | --- | --- | --- | --- | --- |
| VALUE-01A / #117 | Real built-browser loop against Local LLM Server | target-environment Playwright spec/config + bounded browser launcher | current product contracts | yes, B/C | ACTIVE |
| VALUE-01B / #118 | Evidence completeness + portability verifier | real-runtime verifier + deterministic verifier tests | canonical Run/store/bundle contracts | yes, A/C | ACTIVE |
| VALUE-01C / #119 | Exact-head real-run operator entry point | existing real-runtime smoke/runbook + deterministic readiness tests | PRE_REAL contract + canonical CLI | yes, A/B | ACTIVE |
| VALUE-01D / #120 | Retained representative device execution | retained RUNTIME-1 artifact set and state transition only | A + B + C integrated; exact-head PRE_REAL PASS | no | BLOCKED |

Integration rule: A/B/C may not change benchmark, recommendation, persistence or serving semantics merely to simplify the real run. If a lane exposes a genuine product defect, fix its canonical owner in a separate coherent change and revalidate affected lanes.

## Current executable slice

`VALUE-01 — Real single-model evidence loop`, with `VALUE-01A`, `VALUE-01B` and `VALUE-01C` executable in parallel.

User outcome:

> Connect a real Local LLM Server/OpenAI-compatible target on a representative device, run one real model through Performance Lab, inspect trustworthy run/sample evidence, and retain a portable evidence bundle.

Acceptance:

- a current applicable PRE_REAL/Built Product readiness gate is passing before the real run starts;
- a real target is connected and `/v1/models` discovery succeeds;
- when supplied by the provider, runtime identity and `/status` telemetry are captured with explicit provenance rather than guessed;
- a real inference-backed **Test a model** run completes against one representative model;
- Run Detail identifies the frozen model/quantization/configuration/endpoint/device/runtime evidence that is actually known;
- at least one sample can be inspected with execution outcome and evaluator-owned evidence under the configured retention mode;
- the completed run is retained in the canonical store and exported as `.plab.zip`;
- unavailable identity/telemetry/content remains explicitly typed as unavailable/unknown/not-retained;
- the retained real-environment evidence is sufficient for a fresh reviewer to reproduce or bound the claim.

Validation/evidence:

- repository-owned `pre_real_e2e` / Built Product evidence must be current for the implementation head;
- targeted deterministic tests remain green for any code touched by the slice;
- final acceptance requires one retained `real-runtime-device` / `RUNTIME-1` execution, not a hosted fixture.

Detailed real-device artifact/protocol requirements are owned by `representative-device-evidence.md`.

## Later slice acceptance

### VALUE-02 — Real model decision

- same use case + same representative device;
- at least two real model/quantization candidates;
- compatible evidence is compared only where the contracts permit it;
- explicit decision policy is visible before the recommendation;
- Performance Lab returns model + quantization + frozen configuration with backend-owned rationale, or an explicit no-rank reason;
- exact-case evidence remains drillable for materially differentiating cases.

### VALUE-03 — Configuration decision

- use only adapter/runtime-declared mutable parameters and ranges;
- compare at least two supported configurations for a real candidate;
- preserve quantization as candidate identity, never a sweep parameter;
- result answers which model + quantization + configuration should be used under the explicit policy;
- unsupported/non-mutable parameters remain observational rather than fake controls.

### VALUE-04 — Device-aware decision

- retain real latency/throughput evidence and resource evidence that the device/runtime can support truthfully;
- every metric carries scope/unit/provenance;
- unavailable sensors remain unavailable;
- resource evidence may affect the recommendation only when comparable and policy-relevant.

### VALUE-05 — Confidence / repeatability

- run a controlled repeated-load protocol with documented warmup/load assumptions;
- retain denominators, failed/interrupted attempts and variability rather than only successful runs;
- expose enough variability/confidence evidence to distinguish a stable recommendation from an unstable result.

### VALUE-06 — Regression workflow

- establish a real known-good baseline and a real candidate under an explicit compatible protocol;
- retain at least one policy PASS/FAIL outcome with the evidence that produced it;
- incompatible dimensions never produce false deltas or regression verdicts.

### VALUE-07 — LLS evaluation cutover

- all gates in `local-llm-migration.md` are satisfied, including EV-3 and a real PL replacement run;
- legacy LLS evaluation creation is frozen/disabled/removed according to that workstream while historical evidence keeps its original identity;
- `/v1/models`, `/v1/chat/completions`, `/v1/runtime/identity`, `/status` and runtime/resource behavior remain intact in cross-repo smoke;
- Performance Lab continues to execute evaluation after the legacy path is disabled.

### VALUE-08 — Low-friction distribution

- normal product usage does not require manually running pnpm/build steps or editing repository development state;
- launch reaches a usable local product with bounded lifecycle/cleanup;
- endpoint/device connection can be established through product-owned UX or a minimal supported launch contract;
- first-run path reaches **Find best setup** with no hidden developer-only prerequisite;
- packaged/smoke/E2E evidence proves the distributed artifact, not only a source checkout.

## Integration points

- `representative-device-evidence.md` owns real-device protocol, retained artifacts and telemetry/repeatability evidence. VALUE-01/02/04/05/06 consume that evidence instead of duplicating its protocol.
- `local-llm-migration.md` owns cross-repository replacement/deprecation/removal semantics. VALUE-07 is the user-value gate that decides when that cutover is worth completing.
- `design/ux-contract.json` remains the experience/decision owner; value slices must not create a second task model.
- M1-M9 in `docs/roadmap.md` remain coverage/maturity labels, not the execution sequence.

## Delivery rule

Prefer the smallest slice that creates a new usable loop. Do not begin a broad subsystem merely because a later slice may need it. When a slice reveals a concrete coverage gap, add only the capability needed to close that slice and update the owning durable contract/test in the same change.

A slice may ship before later slices are complete. Feedback from the shipped slice is allowed to reshape later slices, provided invariants and accepted evidence contracts remain explicit.

## Durable documentation destinations

- `docs/roadmap.md`: capability maturity plus the current value-delivery ordering model.
- `docs/current-state.md`: current executable VALUE slice and blockers only.
- `docs/evaluation-and-benchmarking.md`, `docs/telemetry.md`, `docs/output-and-evidence-reference.md`, `docs/ci-regression.md`: durable behavior only when a slice changes those contracts.
- `docs/local-llm-server-integration.md` / ADRs: durable ownership/cutover outcomes when VALUE-07 completes.
- `design/`: only when a slice materially changes the settled user task/experience contract.
- executable tests/contracts and retained evidence remain the primary proof of behavior.

## Completion

This workstream is complete when the current text-generation product can demonstrate the full product promise through accepted real evidence and can be launched through the intended distribution path, while any deliberately deferred M8/M9 expansion remains explicitly non-blocking.

On completion, transfer durable outcomes to their canonical owners, update `docs/current-state.md`, and delete this workstream by default.