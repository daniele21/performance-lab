# Roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone, understanding sequencing or identifying deferred product direction
Last reviewed: 2026-08-15

This document tracks capability-level milestones. Live task status and the immediate next work block belong in [`current-state.md`](current-state.md). Detailed dependencies belong in [`implementation-plan.md`](implementation-plan.md).

## Milestone summary

| Milestone | Status | Main outcome | Remaining evidence / convergence |
| --- | --- | --- | --- |
| M0 — Repository and contracts | **Done** | validated foundation, domain contracts, plugin interfaces/fakes and orchestration boundary | complete |
| M1 — First black-box evaluation | **In progress** | versioned quality evaluation against an OpenAI-compatible endpoint | representative real-endpoint lifecycle evidence |
| M2 — Runtime performance evidence | **In progress** | TTFT/latency/throughput/reliability with repeatable protocols | representative repeatability/load evidence |
| M3 — Run store and comparison | **In progress** | immutable evidence, identity diffs and compatible comparison | representative cross-run comparison evidence |
| M4 — Custom workload evaluation | **In progress** | reusable custom mappings plus first versioned practical workload pack | representative workload execution evidence |
| M5 — Resource-aware local evaluation | **In progress** | host and runtime-native telemetry with explicit provenance | first real runtime/device integration |
| M6 — Regression automation | **In progress** | baseline, policy, machine-readable gate and conservative CI integration | representative CI regression evidence |
| M7 — Local product UI | Planned | configure, run, inspect and compare visually | engine evidence remains higher priority; UI read models are available |
| M8 — External benchmark ecosystem | Planned | bridge mature frameworks without copying their tasks into core | only if native evidence shows a concrete coverage gap |
| M9 — Additional AI task families | Future | ASR, embeddings, reranking and vision through generic contracts | after text core/product evidence |

## M0 — Repository and contracts — DONE

Goal: establish a project that can evolve without coupling the core to a model runtime or UI.

Implemented and validated:

- Python 3.12+ repository/toolchain and shared local/CI validation;
- immutable versioned domain schemas and explicit unknown semantics;
- deterministic execution fingerprint identity and dimension-specific compatibility;
- privacy-safe endpoint credential references;
- narrow plugin protocols, explicit registry and deterministic fakes;
- evaluation orchestration lifecycle with typed progress/failure boundaries;
- clean-checkout validation on Python 3.12 and 3.13.

Exit gate: **satisfied**.

## M1 — First black-box capability evaluation — IN PROGRESS

Goal: connect to an OpenAI-compatible endpoint and obtain trustworthy quality scores from a versioned suite.

Implementation integrated:

- OpenAI-compatible streaming/non-streaming adapter and typed transport semantics;
- evidence-based capability probe with declared/observed/unknown states;
- deterministic dataset materialization and sampling;
- compact authored diagnostic starter suite;
- deterministic evaluator primitives and optional provenance-rich rubric judge;
- orchestrator lifecycle and executable `performance-lab run --config` path;
- immutable result publication and portable bundle.

Remaining evidence:

- run the frozen lifecycle against at least one representative real local-model endpoint;
- retain the resulting execution fingerprint and evidence bundle.

Implementation tests do not substitute for representative endpoint evidence.

## M2 — Runtime performance evidence — IN PROGRESS

Goal: measure serving behavior independently from quality scoring.

Implementation integrated:

- request setup/total latency and streaming TTFT;
- output-token throughput when observable;
- explicit unavailable metric semantics;
- cold/warmup/measured-warm classification;
- fixed-count and bounded-duration concurrency/load profiles;
- reliability counters and queue-delay/backpressure evidence;
- repeatability summaries and qualified percentile reporting.

Remaining evidence:

- repeated and load runs against a representative endpoint;
- demonstrate stable protocol identity and interpretable saturation/repeatability behavior.

## M3 — Run store and compatible comparison — IN PROGRESS

Goal: make results useful across changes rather than disposable single runs.

Implementation integrated:

- SQLite durable store with mutable working versus immutable completed evidence;
- atomic terminal publication;
- portable run ZIP export/import with integrity checks;
- identity-first compatible comparison using domain-owned rules;
- capability/runtime/resource deltas only when interpretable;
- versioned evidence-retention policy with raw prompt/output structurally excluded.

Remaining evidence:

- preserve a representative compatible pair and a representative incompatible pair;
- demonstrate that identity differences and typed incompatibility remain clear outside fixtures.

## M4 — Custom workload evaluation — IN PROGRESS

Goal: answer “which model is best for my scenario?” rather than only generic benchmark questions.

Implementation integrated:

- JSONL/CSV ingestion;
- source-shape inspection without semantic guessing;
- versioned reusable field mapping/configuration;
- deterministic local dataset snapshot identity;
- deterministic and optional rubric evaluators as workload building blocks;
- workload-pack contract outside the generic engine;
- first versioned `structured-document-extraction` pack with six authored records, JSON Schema adherence and deterministic field correctness.

Remaining evidence:

- execute the pack against representative models/endpoints and preserve scenario evidence;
- add further packs only for concrete reusable scenarios.

Candidate future packs include meeting intelligence and PII/entity extraction.

## M5 — Resource-aware local evaluation — IN PROGRESS

Goal: correlate inference quality/performance with device resource cost.

Implementation integrated:

- optional telemetry collector lifecycle and typed availability states;
- host/process CPU, RSS/load where observable and collector overhead;
- versioned runtime-native instrumentation handshake;
- runtime/model/hardware identity capture;
- endpoint-only, host-observed and runtime-native provenance remain distinct.

Remaining evidence:

- first integration with a real local/device serving project;
- stronger real run-window correlation;
- later GPU/VRAM/unified-memory, thermal and reliable energy collectors only where justified.

## M6 — Regression automation — IN PROGRESS

Goal: move evaluation into normal software/model engineering iteration.

Implementation integrated:

- explicit immutable baseline binding;
- compatibility-first regression read model;
- versioned threshold policy;
- absolute/relative regression tolerances;
- explicit direction when a metric's better/worse semantics are unknown;
- `PASS`, `FAIL`, `NOT_COMPARABLE`, `NOT_EVALUATED` decision semantics;
- stable machine-readable JSON gate and deterministic exit codes;
- CI command that writes a JSON artifact and GitHub Step Summary;
- reusable local GitHub composite action;
- resource rules forced to `NOT_COMPARABLE` on uncontrolled CI runners.

Implemented flow:

```text
run candidate
-> compare to explicit baseline
-> reject incomparable dimensions
-> apply versioned thresholds
-> emit machine-readable decision
-> apply conservative CI runner semantics
-> publish JSON artifact + CI summary
```

Remaining evidence:

- preserve a representative CI execution showing real baseline/candidate behavior;
- demonstrate both normal threshold decisions and safe `NOT_COMPARABLE` behavior where resource comparability is uncontrolled.

## M7 — Local product UI

Goal: make evaluation approachable without weakening evidence semantics.

Primary surfaces:

- Targets;
- New Evaluation;
- Live Run;
- Results;
- Compare;
- Datasets/Suites;
- Baselines/Policies;
- Telemetry/Settings.

Comparison/regression read models are stable enough for UI implementation, but UI is not required to prove the engine or evidence semantics.

## M8 — External benchmark ecosystem

Goal: reuse mature benchmark ecosystems while keeping Performance Lab focused on orchestration, local-device evidence and regression.

Potential outcomes:

- external-runner adapter;
- configuration translation;
- framework/task/version provenance;
- normalized result import and artifact retention;
- explicit distinction between native and external evaluator evidence.

Do not implement by default. Add an integration only when the native evidence campaign demonstrates a concrete benchmark coverage need.

## M9 — Additional AI task families

Future after text-generation contracts and representative product evidence stabilize.

Candidate families:

- ASR: WER/CER, real-time factor, latency, memory;
- embeddings: retrieval quality, throughput, dimensionality/storage cost;
- rerankers: ranking quality and latency;
- vision/multimodal: task-specific accuracy plus image/token runtime cost.

The core should gain task-family contracts, not provider-specific special cases.

## Product maturity boundaries

### Engine implementation slice

The planned text-generation engine/regression path is implemented through DAT-004 and REG-003. This is an implementation statement, not a representative-performance claim.

### Evidence-backed engine MVP

Requires representative M1/M2/M3 evidence: real endpoint lifecycle, repeatability/load behavior and real compatible/incompatible comparison evidence.

### Practical local evaluation product

Evidence-backed engine MVP + representative M4 workload evidence + M5 runtime/device evidence.

### Engineering regression platform

Practical product + representative M6 CI regression evidence.

### Broader platform

M7 UI + justified M8 ecosystem integrations + selected M9 task families.

## Immediate roadmap emphasis

The next milestone work should primarily create **evidence**, not more framework surface:

1. run starter-suite and structured-document-pack evaluations against representative real endpoints;
2. collect repeatability/concurrency evidence on the same controlled targets;
3. integrate runtime-native telemetry with a real serving stack where feasible;
4. select explicit baseline/candidate runs and exercise `regress-ci` in a real CI workflow;
5. preserve bundles, fingerprints and regression artifacts as milestone evidence;
6. in parallel, prepare release reproducibility and optionally build UI-002 from the stable read models.

## Deferred until evidence justifies them

- distributed multi-runner scheduling;
- hosted SaaS control plane;
- public global leaderboard;
- automatic one-number model ranking;
- autonomous model downloading/serving;
- privileged device control as a requirement;
- arbitrary generated-code execution without a hardened sandbox;
- cross-device energy-efficiency ranking using incomparable sensor methods;
- external benchmark adapters without a demonstrated native-coverage gap.
