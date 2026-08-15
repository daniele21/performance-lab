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
| M4 — Custom workload evaluation | **In progress** | reusable custom dataset mapping plus workload-specific suites | first versioned workload pack |
| M5 — Resource-aware local evaluation | **In progress** | host and runtime-native telemetry with explicit provenance | first real runtime/device integration |
| M6 — Regression automation | **In progress** | explicit baselines, versioned threshold policy and machine-readable automation | CLI-003 validation + REG-003 CI integration |
| M7 — Local product UI | Planned | configure, run, inspect and compare visually | engine remains priority; UI read models now available |
| M8 — External benchmark ecosystem | Planned | bridge mature frameworks without copying their tasks into core | after native evidence stabilizes |
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

Integrated:

- OpenAI-compatible streaming/non-streaming adapter and typed transport semantics;
- evidence-based capability probe with declared/observed/unknown states;
- deterministic dataset materialization and sampling;
- compact authored diagnostic starter suite;
- deterministic evaluator primitives and optional provenance-rich rubric judge;
- orchestrator lifecycle and executable `performance-lab run --config` path;
- immutable result publication and portable bundle.

Remaining evidence:

- run the full frozen lifecycle against at least one representative local-model endpoint;
- retain the resulting execution fingerprint and evidence bundle as milestone evidence.

Exit gate remains evidence-based: implementation tests alone do not prove representative endpoint behavior.

## M2 — Runtime performance evidence — IN PROGRESS

Goal: measure serving behavior independently from quality scoring.

Integrated:

- request setup/total latency and streaming TTFT;
- output-token throughput when observable;
- explicit unavailable metric semantics;
- cold/warmup/measured-warm classification;
- fixed-count and bounded-duration concurrency/load profiles;
- reliability counters, queue delay/backpressure evidence;
- repeatability summaries and qualified percentile reporting.

Remaining evidence:

- repeated and load runs against a representative endpoint;
- demonstrate stable protocol identity and interpretable saturation/repeatability evidence.

## M3 — Run store and compatible comparison — IN PROGRESS

Goal: make results useful across changes rather than disposable single runs.

Integrated:

- SQLite durable store with mutable working versus immutable completed evidence;
- atomic terminal publication;
- portable run ZIP export/import with integrity checks;
- identity-first compatible comparison using domain-owned rules;
- capability/runtime/resource delta reporting only when interpretable;
- versioned evidence-retention policy with raw prompt/output structurally excluded.

Remaining evidence:

- preserve a representative pair of compatible runs and one incompatible pair;
- demonstrate that identity differences and typed incompatibility reasons remain clear outside fixtures.

## M4 — Custom workload evaluation — IN PROGRESS

Goal: answer "which model is best for my scenario?" rather than only generic benchmark questions.

Integrated:

- JSONL/CSV ingestion;
- source-shape inspection without semantic guessing;
- versioned reusable field mapping/configuration;
- deterministic local dataset snapshot identity;
- deterministic and optional rubric evaluators available as workload building blocks.

Remaining:

- workload-pack versioning and first practical pack;
- task/evaluator template composition for at least one real scenario.

Candidate first packs:

- meeting intelligence;
- PII/entity extraction;
- structured document extraction.

## M5 — Resource-aware local evaluation — IN PROGRESS

Goal: correlate inference quality/performance with device resource cost.

Integrated:

- optional telemetry collector lifecycle and typed availability states;
- host/process CPU, CPU-core utilization, RSS/load where observable and collector overhead;
- versioned runtime-native instrumentation handshake;
- runtime/model/hardware identity capture;
- endpoint-only, host-observed and runtime-native provenance remain distinct.

Remaining evidence:

- first integration with a real local/device serving project;
- stronger real run-window correlation;
- later GPU/VRAM/unified-memory, thermal and reliable energy collectors where justified.

## M6 — Regression automation — IN PROGRESS

Goal: move evaluation into normal software/model engineering iteration.

Integrated:

- explicit immutable baseline binding;
- compatibility-first regression read model;
- versioned threshold policy;
- absolute/relative regression tolerances;
- explicit direction when a metric's better/worse semantics are not known;
- `PASS`, `FAIL`, `NOT_COMPARABLE`, `NOT_EVALUATED` decision semantics.

In validation / remaining:

- **CLI-003** stable JSON schema and exit-code contract;
- **REG-003** CI-friendly concise summary plus machine-readable artifact;
- ensure CI never claims resource/hardware comparability when runner identity is uncontrolled or differs.

Target flow:

```text
run candidate
-> compare to explicit baseline
-> reject incomparable dimensions
-> apply versioned thresholds
-> emit machine-readable decision
-> publish CI summary/artifact
```

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

The comparison/regression read models are now stable enough for UI work to begin, but UI is not required to prove the engine MVP.

## M8 — External benchmark ecosystem

Goal: reuse mature benchmark ecosystems while keeping Performance Lab focused on orchestration, local-device evidence and regression.

Required outcomes:

- external-runner adapter;
- configuration translation;
- framework/task/version provenance;
- normalized result import and artifact retention;
- explicit distinction between native and external evaluator evidence.

Add integrations only for concrete coverage needs.

## M9 — Additional AI task families

Future after text-generation contracts and product evidence stabilize.

Candidate families:

- ASR: WER/CER, real-time factor, latency, memory;
- embeddings: retrieval quality, throughput, dimensionality/storage cost;
- rerankers: ranking quality and latency;
- vision/multimodal: task-specific accuracy plus image/token runtime cost.

The core should gain task-family contracts, not provider-specific special cases.

## Product maturity boundaries

### Engine MVP

M0 complete + essential M1/M2/M3 implementation + executable CLI run/comparison path. Representative endpoint evidence is still required before declaring this boundary proven.

### Practical local evaluation product

Engine MVP + M4 custom workloads + M5 resource evidence + baseline comparison.

### Engineering regression platform

Practical product + M6 machine-readable automation/CI.

### Broader platform

M7 UI + M8 ecosystem + selected M9 task families.

## Deferred until evidence justifies them

- distributed multi-runner scheduling;
- hosted SaaS control plane;
- public global leaderboard;
- automatic one-number model ranking;
- autonomous model downloading/serving;
- privileged device control as a requirement;
- arbitrary generated-code execution without a hardened sandbox;
- cross-device energy-efficiency ranking using incomparable sensor methods.
