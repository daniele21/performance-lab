# Roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone or understanding product sequencing
Last reviewed: 2026-08-23

This roadmap tracks capability outcomes. Live state belongs in [`current-state.md`](current-state.md); detailed active dependencies belong in bounded workstreams.

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
| M7 — Local product UI | **ACTIVE / CORE PATH INTEGRATED** | Compare, Library/Settings, browser acceptance, release lifecycle and migration gates |
| M8 — External benchmark ecosystem | DEFERRED | start only when real product evidence exposes a concrete coverage gap |
| M9 — Additional task families | FUTURE | ASR/embeddings/reranking/vision after the text product stabilizes |

## M7 — Local product UI

Goal: make Performance Lab the primary local benchmark/evaluation product without moving inference-runtime ownership into it.

Integrated on `dev`:

- task-model-first Overview;
- Model -> Scenario -> Test -> Review;
- server-owned run launch/progress/cancellation/reconnect;
- Runs and immutable Run Detail;
- versioned UI read/preflight contracts;
- executable semantic design system and loopback composition root.

Remaining product surfaces/gates:

- compatibility-first Compare / regression;
- secondary Library / Settings;
- focused Playwright J1-J6 and accessibility/adaptive evidence;
- representative Local LLM Server/device evidence;
- `REL-UI-001` built-product identity/artifact/smoke/cleanup lifecycle;
- staged Local LLM Server evaluation parity/deprecation/removal.

The active dependency DAG and acceptance gates live only in [`workstreams/ui-productization.md`](workstreams/ui-productization.md).

## Parallel evidence track

Representative evidence proceeds independently from remaining UI work:

1. run a real Local LLM Server target through a representative suite/workload;
2. retain the execution fingerprint and `.plab.zip`;
3. exercise identity and `/status` telemetry on the real device;
4. repeat/load the same controlled target;
5. preserve a real baseline/candidate regression outcome.

This evidence must inform product claims and catch fixture-only assumptions, but lack of physical hardware must not serialize unrelated browser implementation.

## Product maturity

**Engine-capable** — integrated core can execute and compare evidence through CLI/CI.

**Usable local benchmark product** — M7 product surfaces and browser acceptance are complete, and representative M1-M5 evidence exists.

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
