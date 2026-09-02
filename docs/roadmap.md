# Roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone or understanding product sequencing
Last reviewed: 2026-09-02

This roadmap tracks capability outcomes. Live state belongs in [`current-state.md`](current-state.md); detailed active dependencies and slice acceptance belong in bounded workstreams.

## Milestones

| Milestone | Status | Outcome / remaining gate |
| --- | --- | --- |
| M0 — Repository/contracts | DONE | foundation, immutable contracts and orchestrator integrated |
| M1 — Black-box evaluation | IMPLEMENTED / EVIDENCE PENDING | representative real-endpoint lifecycle evidence |
| M2 — Runtime performance | IMPLEMENTED / EVIDENCE PENDING | repeatability/load evidence on controlled hardware |
| M3 — Run store/comparison | IMPLEMENTED / EVIDENCE PENDING | representative compatible + incompatible run pairs |
| M4 — Workload evaluation | IMPLEMENTED / EVIDENCE PENDING | workload packs on representative models |
| M5 — Resource-aware local evaluation | IMPLEMENTED / EVIDENCE PENDING | real identity/telemetry/device evidence |
| M6 — Regression automation | IMPLEMENTED / EVIDENCE PENDING | real baseline/candidate CI evidence |
| M7 — Local product UI | **DONE** | decision-first desktop product, Light-first appearance, browser acceptance and built-product lifecycle integrated |
| M8 — External benchmark ecosystem | DEFERRED | start only when real product evidence exposes a concrete coverage gap |
| M9 — Additional task families | FUTURE | ASR/embeddings/reranking/vision after the text product stabilizes |

M1-M9 are a **coverage and maturity map**, not the implementation sequence. A value slice may consume only the parts of several milestones required to unlock one usable end-to-end outcome.

## Incremental value-delivery order

Operational development is organized by [`workstreams/incremental-value-delivery.md`](workstreams/incremental-value-delivery.md). The rule is: deliver the smallest vertical slice that creates a new usable loop, validate it at the fidelity required by its claim, gather feedback, then extend the product.

| Slice | Value unlocked | State |
| --- | --- | --- |
| VALUE-01 | Real single-model evidence loop: connect -> real inference -> Run/Sample evidence -> `.plab.zip` | READY |
| VALUE-02 | Real model decision: 2+ candidates -> comparable evidence -> explainable recommendation/no-rank | BLOCKED by VALUE-01 |
| VALUE-03 | Configuration decision: choose supported model + quantization + configuration | BLOCKED by VALUE-02 |
| VALUE-04 | Device-aware decision: real performance/resource evidence informs the trade-off | BLOCKED by VALUE-02 |
| VALUE-05 | Confidence/repeatability: controlled variability supports or weakens the recommendation | BLOCKED by VALUE-04 |
| VALUE-06 | Regression workflow: real baseline vs candidate -> explicit policy outcome | BLOCKED by VALUE-02 + VALUE-05 |
| VALUE-07 | LLS evaluation cutover: PL owns new evaluation; LLS remains serving/runtime owner | BLOCKED by VALUE-03 + migration evidence |
| VALUE-08 | Low-friction distribution: launch/connect/evaluate without repository-development setup | BLOCKED by VALUE-02 |

The graph is intentionally not waterfall. After VALUE-02, VALUE-03, VALUE-04 and VALUE-08 may proceed in parallel when write ownership does not conflict. Later slices may be reshaped by evidence/feedback from earlier accepted slices.

## Current value frontier

Current executable slice: **VALUE-01 — Real single-model evidence loop**.

The first real product claim to prove is deliberately small:

```text
real target/device
  -> discover one real model
  -> Test a model
  -> real inference
  -> immutable Run Detail
  -> sample evidence
  -> portable .plab.zip
```

This establishes the real execution/evidence loop before expanding to multi-model recommendations, configuration optimization, richer device telemetry or regression automation.

## M7 — Local product UI

Goal: make Performance Lab the primary local benchmark/evaluation product without moving inference-runtime ownership into it.

Integrated on `dev`:

- decision-first Overview and four-stage **Find best setup**: Goal -> Models -> Optimization -> Review;
- Campaign progress + Results with compatibility/decision policy before recommendation;
- **Test a model**, Live Run recovery, Runs/Run Detail and sample evidence;
- compatibility-first Compare/regression and secondary Library/Settings;
- Light as canonical appearance with optional Dark/System preference;
- versioned UI read/preflight contracts and executable semantic design system;
- Playwright browser acceptance across supported desktop contexts plus assembled built-product lifecycle;
- unique build/source identity, immutable package publication, manifest/checksum, build delta, bounded retention and package smoke/cleanup.

M7 software/productization is complete for the current text-generation scope. Real-device evidence remains separate because synthetic CI cannot establish hardware performance, telemetry, thermal or device-specific claims.

## Specialized evidence and migration tracks

Representative-device protocol/evidence remains owned by [`workstreams/representative-device-evidence.md`](workstreams/representative-device-evidence.md). VALUE-01/02/04/05/06 consume that evidence incrementally rather than waiting for an entire M1-M6 evidence campaign to complete.

Local LLM Server replacement/deprecation/removal remains owned by [`workstreams/local-llm-migration.md`](workstreams/local-llm-migration.md). VALUE-07 executes only after Performance Lab has already demonstrated the replacement value loop and the migration's real-environment gates are satisfied.

## Product maturity

**Engine-capable** — integrated core can execute and compare evidence through CLI/CI.

**Product-software complete for the current local UI scope** — M7 surfaces, browser acceptance and built-product lifecycle are integrated.

**Evidence-backed local benchmark product** — VALUE-01..05 demonstrate the product promise on representative real endpoints/devices.

**Engineering regression platform** — evidence-backed product + VALUE-06 real baseline/candidate policy evidence.

**Low-friction local product** — VALUE-08 removes repository-development setup from the normal user path.

**Broader platform** — only then add justified M8 integrations and selected M9 task families.

## Explicitly deferred

- hosted SaaS control plane;
- distributed multi-runner scheduling;
- public global leaderboard;
- automatic universal one-number ranking;
- autonomous model serving/downloading inside Performance Lab;
- cross-device efficiency claims over incomparable sensors;
- external benchmark bridges without demonstrated need.