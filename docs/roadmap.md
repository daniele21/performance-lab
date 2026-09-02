# Roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone or understanding product sequencing
Last reviewed: 2026-08-24

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
| M7 — Local product UI | **DONE** | Compare, Library/Settings, J1-J6 browser acceptance and built-product lifecycle integrated |
| M8 — External benchmark ecosystem | DEFERRED | start only when real product evidence exposes a concrete coverage gap |
| M9 — Additional task families | FUTURE | ASR/embeddings/reranking/vision after the text product stabilizes |

## M7 — Local product UI

Goal: make Performance Lab the primary local benchmark/evaluation product without moving inference-runtime ownership into it.

Integrated on `dev`:

- task-model-first Overview;
- Model -> Scenario -> Test -> Review;
- server-owned run launch/progress/cancellation/reconnect;
- Runs and immutable Run Detail;
- compatibility-first Compare/regression;
- secondary read-only Library/Settings;
- versioned UI read/preflight contracts;
- executable semantic design system and loopback composition root;
- Playwright Chromium J1-J6 browser acceptance, compact/wide checks and reduced-motion behavior;
- unique built-product/source identity, immutable package publication, manifest/checksum, build delta, bounded retention and package smoke/cleanup.

M7 software/productization is complete. Real-device evidence is intentionally tracked separately because synthetic CI cannot establish hardware performance, telemetry, thermal or device-specific claims. Local LLM Server deprecation/removal is also a separate migration lifecycle rather than a UI-completion gate.

## Active evidence and migration tracks

Representative evidence: [`workstreams/representative-device-evidence.md`](workstreams/representative-device-evidence.md)

1. run a real Local LLM Server target through a representative suite/workload;
2. retain the execution fingerprint and `.plab.zip`;
3. exercise identity and `/status` telemetry on the real device;
4. repeat/load the same controlled target;
5. preserve representative comparison/regression outcomes.

LLS migration: [`workstreams/local-llm-migration.md`](workstreams/local-llm-migration.md)

1. map every overlapping evaluation workflow and consumer;
2. establish replacement parity plus history/data policy;
3. deprecate before removal;
4. remove redundant paths only after cross-repo and real-runtime evidence.

## Product maturity

**Engine-capable** — integrated core can execute and compare evidence through CLI/CI.

**Product-software complete for the current local UI scope** — M7 surfaces, browser acceptance and built-product lifecycle are integrated.

**Evidence-backed local benchmark product** — product software + representative M1-M5 evidence.

**Engineering regression platform** — evidence-backed product + representative M6 CI gate evidence.

**Broader platform** — only then add justified M8 integrations and selected M9 task families.

## Explicitly deferred

- hosted SaaS control plane;
- distributed multi-runner scheduling;
- public global leaderboard;
- automatic universal one-number ranking;
- autonomous model serving/downloading inside Performance Lab;
- cross-device efficiency claims over incomparable sensors;
- external benchmark bridges without demonstrated need.
