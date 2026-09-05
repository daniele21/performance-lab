# Incremental value delivery

Status: active
Owner: Performance Lab product delivery
Read when: selecting or implementing the next end-to-end value slice
Last reviewed: 2026-09-05

## Goal

Deliver Performance Lab through small vertical slices that unlock observable user value end to end instead of completing capability areas sequentially.

```text
user intent -> canonical contract -> execution -> retained evidence -> user-visible result -> sufficient E2E evidence
```

M1-M9 in `docs/roadmap.md` remain the capability/maturity map. This workstream owns delivery order and slice acceptance. `representative-device-evidence.md` owns real-device protocol/evidence; `local-llm-migration.md` owns LLS cutover detail.

## Delivery policy

Development has two explicit layers under repo-template-sw 0.9.2:

1. **Software convergence** — deterministic slices integrate incrementally into `dev` after affected automated E2E and UX/UI evidence pass.
2. **REAL_ENVIRONMENT acceptance** — after planned software convergence, refresh exact-head PRE_REAL on final `dev` and execute representative runtime/device/model evidence as a release gate.

A real-device gate therefore does **not** block an independent deterministic software slice from integrating. Hosted CI or fixture evidence never upgrades a representative claim to PASS.

## Invariants

- Product question: for this use case on this device, which available model + quantization + supported configuration is the best evidence-backed fit, and why?
- Quality, Performance and Resources stay separate; compatibility precedes rankings/deltas; unknown stays unknown.
- Frozen candidate/configuration and endpoint/device/runtime identity stay explicit when known.
- Search ranges/capabilities come from canonical backend/runtime contracts; the browser never invents them.
- Evidence fidelity follows the claim; real-device claims require `REAL_ENVIRONMENT` evidence at release.
- Quantization is candidate identity, never a configuration sweep knob.
- Parallel lanes need non-conflicting ownership and one convergence gate.
- A VALUE slice is `DONE` only when its software and required acceptance evidence agree; `SOFTWARE DONE` is not equivalent to final DONE when representative evidence remains.

## Work graph

| ID | User value unlocked | Software state | Final acceptance |
| --- | --- | --- | --- |
| VALUE-01 | **Real single-model evidence loop** — discover, test, inspect and export one real target/model | SOFTWARE DONE | #120 / EVID-001 release-deferred |
| VALUE-02 | **Real model decision** — compare 2+ candidates and return recommendation/no-rank | SOFTWARE DONE | #132 after #120 at release |
| VALUE-03 | **Configuration decision** — choose supported configuration, not only model | ACTIVE | VALUE-03D after software convergence |
| VALUE-04 | **Device-aware decision** — comparable performance/resource evidence may affect the trade-off | ACTIVE | VALUE-04D / EVID-003 after software convergence |
| VALUE-05 | **Repeatability evidence** — controlled repeats expose variability and failure denominators without an invented confidence score | SOFTWARE DONE | VALUE-05D / EVID-002 release-deferred |
| VALUE-06 | **Regression workflow** — baseline vs candidate produces explicit policy outcome | SOFTWARE DONE | VALUE-06D / EVID-004 release-deferred |
| VALUE-07 | **LLS evaluation cutover** — PL owns new evaluation; LLS stays serving/runtime owner | PRE-CUTOVER IMPLEMENTATION DONE | destructive cutover blocked by migration real evidence |
| VALUE-08 | **Low-friction distribution** — launch/connect/evaluate without repo-development setup | A/B/C SOFTWARE DONE | VALUE-08D release-deferred |

## Integrated software

### VALUE-01

| ID | Work | State |
| --- | --- | --- |
| VALUE-01A / #117 | built-browser real-runtime journey | DONE |
| VALUE-01B / #118 | evidence completeness + portability verifier | DONE |
| VALUE-01C / #119 | exact-head PRE_REAL-gated operator entry point | DONE |
| VALUE-01D / #120 | retained representative execution | REAL_ENVIRONMENT RELEASE-DEFERRED |

### VALUE-02

| ID | Work | State |
| --- | --- | --- |
| VALUE-02A / #129 | configured-target multi-model discovery + attribution | SOFTWARE DONE |
| VALUE-02B / #130 | multi-model Campaign/browser real-runtime harness | SOFTWARE DONE |
| VALUE-02C / #131 | retained multi-model decision verifier | SOFTWARE DONE |
| VALUE-02D / #132 | representative 2+ real-model decision | REAL_ENVIRONMENT RELEASE-DEFERRED |

### VALUE-03

Integrated software:

- canonical runtime/model-declared generation parameter domains;
- exact frozen `configuration_id` + generation identity through plan, Campaign entries and immutable Runs.

Remaining software:

- expand non-Fixed strategies into a deterministic reviewed configuration matrix;
- show declared domains and exact planned configurations through the Optimization/Review UX.

The exact Quick/Standard/Thorough/Custom sampling/cardinality semantics are still a material product contract. Implementation must not invent them from parameter min/max alone.

### VALUE-04

VALUE-04A/B are integrated through PR #153:

- stable measurement identity determines decision eligibility;
- contextual host/runtime telemetry does not become model-resource evidence;
- Campaign Results and same-case views expose Resources as `available`, `unavailable` or `not_comparable`.

Remaining software: VALUE-04C policy extension. It must remain compatibility-first and quality-first with no hidden universal score. The exact resource influence/tie-break semantics must be explicit and versioned before implementation.

### VALUE-05

VALUE-05A/B/C are software-complete through PR #167:

- normal evaluation retains client-boundary request measurements from the same inference call; no second inference is introduced for measurement;
- repeatability cohorts use exact `ExecutionFingerprint.fingerprint_id` equality only;
- the canonical statistics owner supplies mean/median/stddev/CV and qualified p90/p95 across per-Run values;
- failed/cancelled Runs and sample attempts stay explicit denominators and are never converted into zero-valued metrics;
- Run Detail shows exact-fingerprint cohort size, frozen load profile, denominators and variability with progressive disclosure;
- no universal confidence score, stability threshold, winner or PASS/FAIL verdict is invented.

VALUE-05D / EVID-002 remains representative repeated-load acceptance and is release-deferred.

### VALUE-06

VALUE-06A/B/C are integrated through PR #164:

- explicit immutable baseline + candidate regression evaluation reuses the canonical regression engine;
- only user-supplied versioned policies are exposed; no default threshold policy is invented;
- Compare renders compatibility first, then policy identity, typed PASS/FAIL/NOT_COMPARABLE/NOT_EVALUATED outcome, rule rationale and only valid deltas;
- raw comparison remains available when no policy is configured;
- deterministic browser and packaged-product acceptance prove PASS, FAIL and NOT_COMPARABLE software states.

VALUE-06D / EVID-004 is representative acceptance only.

### VALUE-08

VALUE-08A/B/C are software-complete:

- artifact-owned launcher;
- configless first run + safe loopback connection preference;
- distributed ZIP acceptance through `launch.py` + UI connection + Find best setup + bounded evaluation;
- retained machine-readable artifact/runtime/cleanup evidence.

VALUE-08D is representative acceptance only.

## Current convergence sequence

```text
current dev
-> finish VALUE-03B/C software after its sampling contract is explicit
-> finish VALUE-04C after its policy contract is explicit
-> keep VALUE-07 destructive migration gated by its cross-repository real evidence
-> converge docs/contracts/tests on final dev
-> fresh exact-head PRE_REAL/Built Product PASS
-> release-time REAL_ENVIRONMENT phase
```

The final real phase supplies the evidence needed by VALUE-01D, VALUE-02D, VALUE-03D, VALUE-04D/EVID-003, VALUE-05D/EVID-002, VALUE-06D/EVID-004 and VALUE-08D. VALUE-07 removal/cutover happens only after its own LLS/PL evidence gates agree.

## Later slice acceptance

| Slice | Minimum final acceptance |
| --- | --- |
| VALUE-01 | one real candidate completes Test a model -> immutable Run/Sample evidence -> verified `.plab.zip`. |
| VALUE-02 | 2+ real candidates, same use case/device; compatibility and explicit policy precede recommendation/no-rank. |
| VALUE-03 | 2+ supported real configurations using runtime-declared mutable domains; exact configuration identity is retained. |
| VALUE-04 | real latency/throughput/resource measurements retain scope/unit/provenance; unavailable sensors stay unavailable; only comparable policy-relevant evidence may affect a decision. |
| VALUE-05 | controlled repeats retain warmup/load assumptions, denominators, failures and variability sufficient to bound how repeatable the evidence is, without a fabricated confidence verdict. |
| VALUE-06 | compatible real baseline/candidate retain at least one versioned policy outcome; incompatible dimensions never produce false deltas/verdicts. |
| VALUE-07 | `local-llm-migration.md` gates pass; legacy evaluation creation is frozen/removed while LLS serving/identity/status and PL evaluation remain healthy. |
| VALUE-08 | normal usage avoids repo build/edit steps; distributed artifact launches/connects/evaluates; representative desktop smoke passes. |

## Delivery rule

Prefer the smallest slice that creates a new usable loop. Add only capability needed to close that slice. Do not use a future representative test as an excuse for a waterfall software branch, and do not use fixture CI as a substitute for representative evidence.

## Integration points

- `representative-device-evidence.md` owns real-device protocol/artifacts used by VALUE-01/02/03/04/05/06/08.
- `local-llm-migration.md` owns replacement/deprecation/removal semantics consumed by VALUE-07.
- `design/ux-contract.json` remains the task/experience owner.
- M1-M9 remain maturity labels, not execution order.

## Completion

Complete when the current text-generation product demonstrates its full promise through accepted real evidence and the intended distribution path. Transfer durable outcomes, update `docs/current-state.md`, then delete this workstream by default.
