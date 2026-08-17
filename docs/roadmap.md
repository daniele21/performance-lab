# Roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone or understanding product sequencing
Last reviewed: 2026-08-17

This roadmap tracks capability outcomes. Live status belongs in [`current-state.md`](current-state.md); detailed active dependencies belong in bounded workstreams.

## Milestones

| Milestone | Status | Outcome / remaining gate |
| --- | --- | --- |
| M0 — Repository/contracts | DONE | foundation, immutable contracts and orchestrator integrated |
| M1 — Black-box evaluation | IMPLEMENTED / EVIDENCE PENDING | retain representative real-endpoint lifecycle evidence |
| M2 — Runtime performance | IMPLEMENTED / EVIDENCE PENDING | repeatability/load evidence on controlled hardware |
| M3 — Run store/comparison | IMPLEMENTED / EVIDENCE PENDING | representative compatible + incompatible run pairs |
| M4 — Workload evaluation | IMPLEMENTED / EVIDENCE PENDING | execute workload packs on representative models |
| M5 — Resource-aware local evaluation | IMPLEMENTED / EVIDENCE PENDING | real identity/telemetry/device evidence |
| M6 — Regression automation | IMPLEMENTED / EVIDENCE PENDING | real baseline/candidate CI evidence |
| M7 — Local product UI | **ACTIVE** | productize tested models, run creation/live monitoring, evidence detail and comparison |
| M8 — External benchmark ecosystem | DEFERRED | start only when real product evidence exposes a concrete coverage gap |
| M9 — Additional task families | FUTURE | ASR/embeddings/reranking/vision after text product stabilizes |

## M7 — Local product UI — ACTIVE

Goal: turn the integrated engine into the primary local benchmark/evaluation product without moving inference-runtime ownership into Performance Lab.

ADR 0004 makes M7 a product-ownership milestone, not a cosmetic layer:

- Performance Lab becomes the benchmark/evaluation UX and evidence-history owner.
- Local LLM Server remains the serving/runtime control plane.
- Local LLM Server evaluation is migrated/deprecated only after Performance Lab replacement parity is proven.

Primary surfaces:

- Overview / tested models;
- New Evaluation;
- Live Run;
- Results / Run Detail;
- Compare / regression;
- Suites;
- Baselines / policies;
- Targets / devices.

The active dependency DAG and acceptance gates live in [`workstreams/ui-productization.md`](workstreams/ui-productization.md).

M7 exit requires more than visual parity: typed application contracts, cancellation/recovery/resource cleanup, built-product Playwright evidence, exact evidence/comparison semantics and the staged Local LLM Server migration gate.

## Parallel evidence track

UI productization does not pause the representative evidence campaign. In parallel with M7 foundation work:

1. run a real Local LLM Server target through the starter suite;
2. retain fingerprint + `.plab.zip`;
3. exercise identity and `/status` telemetry on the real device;
4. repeat/load the same controlled target;
5. preserve a real baseline/candidate regression outcome.

This real evidence should inform UI read models and prevent fixture-only assumptions from becoming product contracts.

## Product maturity

**Engine-capable** — current integrated core can execute and compare evidence through CLI/CI.

**Usable local benchmark product** — M7 core surfaces are product-tested and representative M1–M5 evidence exists.

**Engineering regression platform** — usable product + representative M6 CI gate evidence.

**Broader platform** — only then add justified M8 integrations and selected M9 task families.

## Explicitly deferred

- hosted SaaS control plane;
- distributed multi-runner scheduling;
- public global leaderboard;
- automatic universal one-number ranking;
- autonomous model serving/downloading inside Performance Lab;
- cross-device efficiency claims over incomparable sensors;
- external benchmark bridges without demonstrated need.
