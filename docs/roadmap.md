# Roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone or understanding product sequencing
Last reviewed: 2026-09-05

This roadmap tracks capability outcomes. Live state belongs in [`current-state.md`](current-state.md); detailed active dependencies and slice acceptance belong in bounded workstreams.

## Milestones

| Milestone | Status | Outcome / remaining gate |
| --- | --- | --- |
| M0 — Repository/contracts | DONE | foundation, immutable contracts and orchestrator integrated |
| M1 — Black-box evaluation | IMPLEMENTED / EVIDENCE PENDING | representative real-endpoint lifecycle evidence |
| M2 — Runtime performance | IMPLEMENTED / EVIDENCE PENDING | repeatability/load evidence on controlled hardware |
| M3 — Run store/comparison | IMPLEMENTED / EVIDENCE PENDING | representative compatible + incompatible run pairs |
| M4 — Workload evaluation | IMPLEMENTED / EVIDENCE PENDING | workload packs on representative models |
| M5 — Resource-aware local evaluation | IMPLEMENTED / SOFTWARE POLICY + EVIDENCE PENDING | finish device-aware policy; then real identity/telemetry/device evidence |
| M6 — Regression automation | IMPLEMENTED / PRODUCTIZATION + EVIDENCE PENDING | close any product projection gap; then real baseline/candidate evidence |
| M7 — Local product UI | **DONE** | decision-first desktop product, Light-first appearance, browser acceptance and built-product lifecycle integrated |
| M8 — External benchmark ecosystem | DEFERRED | start only when real product evidence exposes a concrete coverage gap |
| M9 — Additional task families | FUTURE | ASR/embeddings/reranking/vision after the text product stabilizes |

M1-M9 are a **coverage and maturity map**, not the implementation sequence. A value slice may consume only the parts of several milestones required to unlock one usable end-to-end outcome.

## Incremental value-delivery order

Operational development is organized by [`workstreams/incremental-value-delivery.md`](workstreams/incremental-value-delivery.md). Deterministic software converges incrementally on `dev`; representative `REAL_ENVIRONMENT` acceptance is run after the planned software modifications converge on the final candidate head.

| Slice | Value unlocked | Current state |
| --- | --- | --- |
| VALUE-01 | Real single-model evidence loop: connect -> inference -> Run/Sample evidence -> `.plab.zip` | SOFTWARE DONE / REAL PENDING |
| VALUE-02 | Real model decision: 2+ candidates -> comparable evidence -> recommendation/no-rank | SOFTWARE DONE / REAL PENDING |
| VALUE-03 | Configuration decision: choose supported model + quantization + configuration | SOFTWARE ACTIVE |
| VALUE-04 | Device-aware decision: real performance/resource evidence informs the trade-off | SOFTWARE ACTIVE |
| VALUE-05 | Confidence/repeatability: controlled variability supports or weakens the recommendation | SOFTWARE DECOMPOSITION NEXT |
| VALUE-06 | Regression workflow: baseline vs candidate -> explicit policy outcome | SOFTWARE DECOMPOSITION NEXT |
| VALUE-07 | LLS evaluation cutover: PL owns new evaluation; LLS remains serving/runtime owner | PRE-CUTOVER DONE / EVIDENCE-BLOCKED |
| VALUE-08 | Low-friction distribution: launch/connect/evaluate without repository-development setup | A/B/C SOFTWARE DONE / REAL PENDING |

The graph is intentionally not waterfall. VALUE-03, VALUE-04 and VALUE-08 software have progressed in parallel where ownership is independent. Later slices may reuse already-implemented engines without duplicating ownership.

## Current value frontier

Current executable frontier: **finish software convergence before representative acceptance**.

```text
current dev
  -> finish configuration-search software
  -> finish device-aware decision-policy software
  -> close only the missing repeatability/regression product orchestration around existing engines
  -> keep destructive LLS cutover blocked by its real cross-repo evidence
  -> fresh exact-head PRE_REAL on final dev
  -> consolidated REAL_ENVIRONMENT campaign
```

The final real phase proves the product claims on representative Local LLM Server models/devices; it should confirm residual fidelity gaps rather than discover ordinary deterministic product defects.

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
- unique build/source identity, immutable package publication, manifest/checksum, build delta, bounded retention and package smoke/cleanup;
- configless distributed ZIP launch through artifact-owned `launch.py`, safe loopback connection preference and packaged acceptance.

M7 software/productization is complete for the current text-generation scope. Real-device evidence remains separate because synthetic CI cannot establish hardware performance, telemetry, thermal or device-specific claims.

## Specialized evidence and migration tracks

Representative-device protocol/evidence remains owned by [`workstreams/representative-device-evidence.md`](workstreams/representative-device-evidence.md). Its execution is intentionally held until the planned software convergence is complete, then VALUE-01/02/03/04/05/06/08 consume the retained evidence campaign.

Local LLM Server replacement/deprecation/removal remains owned by [`workstreams/local-llm-migration.md`](workstreams/local-llm-migration.md). VALUE-07 destructive cutover executes only after the migration's real-environment gates are satisfied.

## Product maturity

**Engine-capable** — integrated core can execute, measure and compare evidence through CLI/CI.

**Product-software complete for the current local UI/distribution baseline** — M7 surfaces, browser acceptance, built-product lifecycle and configless distributed launch are integrated.

**Evidence-backed local benchmark product** — VALUE-01..05 demonstrate the product promise on representative real endpoints/devices.

**Engineering regression platform** — evidence-backed product + VALUE-06 real baseline/candidate policy evidence.

**Low-friction local product** — VALUE-08 software is integrated; representative clean-install/use smoke remains.

**Broader platform** — only then add justified M8 integrations and selected M9 task families.

## Explicitly deferred

- hosted SaaS control plane;
- distributed multi-runner scheduling;
- public global leaderboard;
- automatic universal one-number ranking;
- autonomous model serving/downloading inside Performance Lab;
- cross-device efficiency claims over incomparable sensors;
- external benchmark bridges without demonstrated need;
- native Electron/Tauri/PyInstaller/DMG/MSI packaging without an explicit product requirement.
