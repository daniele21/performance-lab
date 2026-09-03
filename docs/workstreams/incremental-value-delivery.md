# Incremental value delivery

Status: active
Owner: Performance Lab product delivery
Read when: selecting or implementing the next end-to-end value slice

## Goal

Deliver Performance Lab through small vertical slices that unlock observable user value end to end instead of completing capability areas sequentially.

```text
user intent -> canonical contract -> execution -> retained evidence -> user-visible result -> sufficient E2E evidence
```

M1-M9 in `docs/roadmap.md` remain the capability/maturity map. This workstream owns delivery order and slice acceptance. `representative-device-evidence.md` owns real-device protocol/evidence; `local-llm-migration.md` owns LLS cutover detail.

## Invariants

- Product question: for this use case on this device, which available model + quantization + configuration is the best evidence-backed fit, and why?
- Quality, Performance and Resources stay separate; compatibility precedes rankings/deltas; unknown stays unknown.
- Frozen candidate/configuration and endpoint/device/runtime identity stay explicit when known.
- Search ranges/capabilities come from canonical backend/runtime contracts; the browser never invents them.
- Evidence fidelity follows the claim; real-device claims require `REAL_ENVIRONMENT` evidence.
- Parallel lanes need non-conflicting ownership and one convergence gate.
- A slice is `DONE` only when user loop, failure/recovery, retained evidence and validation agree.

## Work graph

| ID | User value unlocked | Depends on | Parallel | State |
| --- | --- | --- | --- | --- |
| VALUE-01 | **Real single-model evidence loop** — discover, test, inspect and export one real target/model | fresh exact-head PRE_REAL + VALUE-01D | internal lanes complete | ACTIVE |
| VALUE-02 | **Real model decision** — compare 2+ real candidates and return an explainable recommendation/no-rank | VALUE-01D + fresh PRE_REAL + VALUE-02D | software A/B/C integrated | BLOCKED |
| VALUE-03 | **Configuration decision** — choose a supported configuration, not only a model | VALUE-02 real acceptance | VALUE-04/08 | BLOCKED |
| VALUE-04 | **Device-aware decision** — real performance/resource evidence affects the trade-off | VALUE-02 real acceptance | VALUE-03/08 | BLOCKED |
| VALUE-05 | **Confidence / repeatability** — controlled variability supports the recommendation | VALUE-04 | late VALUE-03 | BLOCKED |
| VALUE-06 | **Regression workflow** — real baseline vs candidate produces a policy outcome | VALUE-02, VALUE-05 | no | BLOCKED |
| VALUE-07 | **LLS evaluation cutover** — PL owns new evaluation; LLS stays serving/runtime owner | VALUE-03 + LLS gates | no | BLOCKED |
| VALUE-08 | **Low-friction distribution** — launch/connect/evaluate without repo-development setup | VALUE-02 real acceptance | VALUE-03..07 | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`. After VALUE-02 real acceptance, VALUE-03/04/08 may proceed in parallel where ownership is independent.

## VALUE-01 execution graph

The software/readiness lanes are integrated. The representative-device run remains the acceptance gate.

| ID | Work | Owns/writes | State |
| --- | --- | --- | --- |
| VALUE-01A / #117 | Real built-browser loop against Local LLM Server | target-environment Playwright + bounded browser launcher | DONE |
| VALUE-01B / #118 | Evidence completeness + portability verifier | real-runtime verifier + deterministic tests | DONE |
| VALUE-01C / #119 | Exact-head real-run operator entry point | real-runtime smoke/runbook + readiness tests | DONE |
| VALUE-01D / #120 | Retained representative device execution | RUNTIME-1 artifact set + state transition | READY after fresh PRE_REAL |

PR #141 intentionally moved `dev` to integrate the completed VALUE-02 software for end-to-end testing. Therefore older PRE_REAL handoffs are historical evidence only; #120 must use a fresh PRE_REAL/Built Product PASS for the current `dev` revision.

## Current acceptance — VALUE-01

User outcome:

> Connect a real Local LLM Server target on a representative device, run one real model, inspect trustworthy Run/Sample Evidence, and retain a portable evidence bundle.

Acceptance:

- fresh exact-head PRE_REAL/Built Product readiness passes before the real run;
- real `/v1/models` discovery and inference complete through **Test a model**;
- first-party runtime identity and `/status` telemetry are retained when supplied, with explicit provenance;
- Run Detail and at least one retained Sample Evidence view are inspectable;
- canonical store + `.plab.zip` pass the VALUE-01B verifier; missing/not-retained evidence stays typed;
- one retained `real-runtime-device` / `RUNTIME-1` run is sufficient for a reviewer to reproduce or bound the claim.

`representative-device-evidence.md` owns the detailed real-device protocol/artifact rules.

## VALUE-02 execution graph

The deterministic/software portions are already integrated on `dev`; only representative acceptance remains.

| ID | Work | State |
| --- | --- | --- |
| VALUE-02A / #129 | Configured-target multi-model discovery + candidate evidence attribution | SOFTWARE DONE |
| VALUE-02B / #130 | Real multi-model Campaign/browser harness | SOFTWARE DONE |
| VALUE-02C / #131 | Retained multi-model decision evidence verifier | SOFTWARE DONE |
| VALUE-02D / #132 | Representative 2+ real-model decision | BLOCKED by #120 + fresh PRE_REAL |

VALUE-02 is not `DONE` merely because A/B/C are integrated. Acceptance still requires #120 PASS first and then one retained REAL_ENVIRONMENT #132 run whose browser/backend/verifier evidence agrees.

## Current convergence sequence

```text
current dev
-> fresh exact-head PRE_REAL/Built Product PASS
-> #120 single-model REAL_ENVIRONMENT PASS
-> #132 multi-model REAL_ENVIRONMENT PASS
-> VALUE-02 DONE
-> integrate prepared VALUE-03A / VALUE-04A / VALUE-08A
-> continue VALUE-03 / VALUE-04 / VALUE-08 in parallel
```

Prepared isolated lanes already exist and remain intentionally unmerged until VALUE-02 acceptance:

- VALUE-03A / PR #149 — runtime/model-declared bounded generation domains;
- VALUE-04A / PR #148 — policy-eligible device evidence classification;
- VALUE-08A / PR #147 — artifact-owned launcher.

## Later slice acceptance

| Slice | Minimum acceptance |
| --- | --- |
| VALUE-02 | 2+ real candidates, same use case/device; compatibility and explicit policy precede backend-owned recommendation/no-rank; differentiating evidence remains drillable. |
| VALUE-03 | 2+ supported real configurations using runtime-declared mutable ranges; quantization stays candidate identity; unsupported parameters are not fake controls. |
| VALUE-04 | real latency/throughput/resource measurements retain scope/unit/provenance; unavailable sensors stay unavailable; only comparable policy-relevant evidence affects decisions. |
| VALUE-05 | controlled repeats retain warmup/load assumptions, denominators, failures and variability sufficient to identify unstable recommendations. |
| VALUE-06 | compatible real baseline/candidate retain at least one policy outcome; incompatible dimensions never produce false deltas/verdicts. |
| VALUE-07 | `local-llm-migration.md` gates pass; legacy evaluation creation is frozen/removed while LLS serving/identity/status stay healthy and PL evaluation still works. |
| VALUE-08 | normal usage avoids repo build/edit steps; launch/connection reaches Find best setup; packaged smoke/E2E proves the distributed artifact. |

## Delivery rule

Prefer the smallest slice that creates a new usable loop. Add only capability needed to close that slice; accepted slices may ship before later work and feedback may reshape later slices without weakening invariants.

## Integration points

- `representative-device-evidence.md` owns real-device protocol/artifacts used by VALUE-01/02/04/05/06.
- `local-llm-migration.md` owns replacement/deprecation/removal semantics consumed by VALUE-07.
- `design/ux-contract.json` remains the task/experience owner.
- M1-M9 remain maturity labels, not execution order.

## Completion

Complete when the current text-generation product demonstrates its full promise through accepted real evidence and the intended distribution path. Transfer durable outcomes, update `docs/current-state.md`, then delete this workstream by default.
