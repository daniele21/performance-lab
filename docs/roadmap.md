# Roadmap

Status: active
Document type: roadmap
Owner: repository
Canonical scope: roadmap.repository
Read when: selecting the next capability milestone, understanding sequencing or identifying deferred product direction
Last reviewed: 2026-08-15

This document tracks capability-level milestones. Live task status and the immediate next work block belong in [`current-state.md`](current-state.md). Detailed dependencies belong in [`implementation-plan.md`](implementation-plan.md).

## Milestone summary

| Milestone | Status | Main outcome | Parallel opportunities |
| --- | --- | --- | --- |
| M0 — Repository and contracts | **Done** | validated foundation, domain contracts, plugin interfaces/fakes and orchestration boundary | completed fan-out enables all engine lanes |
| M1 — First black-box evaluation | **In progress** | run a deterministic quality suite against an OpenAI-compatible endpoint | capability probe, starter suite and executable run path in parallel |
| M2 — Runtime performance evidence | **In progress** | TTFT/latency/throughput/reliability with repeatable protocols | concurrency and statistics now parallel |
| M3 — Run store and comparison | **In progress** | immutable fingerprints, history and compatible run comparison | comparison and retention policies in parallel |
| M4 — Custom workload evaluation | Planned | import local datasets and create reusable workload suites | custom mapping can progress beside comparison/telemetry |
| M5 — Resource-aware local evaluation | **In progress** | host/device telemetry and instrumented endpoint correlation | runtime-native telemetry can progress independently |
| M6 — Regression automation | Planned | explicit baselines, threshold policies and machine-readable CLI | begins after compatible comparison queries |
| M7 — Local product UI | Planned | configure, run, inspect and compare evaluations visually | not on engine MVP critical path |
| M8 — External benchmark ecosystem | Planned | bridge established evaluation frameworks without duplicating them | after native end-to-end evidence stabilizes |
| M9 — Additional AI task families | Future | ASR, embeddings, reranking, vision through generic task extensions | independent task-family workstreams after text core |

## M0 — Repository and contracts — DONE

Goal: establish a project that can evolve without coupling the core to a model runtime or UI.

Implemented and validated:

- Python 3.12+ repository/toolchain with common local/CI validation;
- branch/contribution policy and MIT license;
- immutable versioned domain schemas and explicit unknown semantics;
- deterministic execution fingerprint identity and dimension-specific compatibility;
- privacy-safe endpoint credential references;
- narrow plugin protocols and explicit registry;
- deterministic fakes for inference, datasets, evaluation, telemetry, export and external runners;
- evaluation orchestration lifecycle with typed progress/failure boundaries;
- clean-checkout validation on Python 3.12 and 3.13.

Exit gate: **satisfied**. Adapter, dataset, evaluation, telemetry and storage implementations now share stable boundaries without concrete cross-lane imports.

## M1 — First black-box capability evaluation — IN PROGRESS

Goal: connect to an OpenAI-compatible endpoint and obtain trustworthy quality scores from a versioned suite.

Integrated:

- OpenAI-compatible adapter with streaming/non-streaming normalization;
- model listing/basic endpoint probe;
- deterministic dataset materialization and sampling;
- deterministic evaluator primitives;
- orchestrator lifecycle with partial failure semantics;
- per-sample and aggregate quality results;
- immutable result publication primitive.

Remaining:

- richer endpoint capability discovery with declared/observed/unknown states;
- compact versioned general-purpose starter suite;
- executable `run` control-plane path using the integrated primitives;
- representative real-endpoint end-to-end evidence.

Exit gate:

- a local endpoint can be evaluated without Performance Lab knowing how the model is hosted;
- the completed run has a reproducible fingerprint and immutable result bundle;
- unsupported/unknown endpoint features are explicit.

## M2 — Runtime performance evidence — IN PROGRESS

Goal: measure serving behavior independently from quality scoring.

Integrated:

- client-observed request setup and total latency;
- TTFT for streaming endpoints;
- output token throughput when usage/timing are observable;
- explicit unavailable metric semantics;
- cold/warmup/measured-warm classification.

Remaining:

- fixed-concurrency load protocol and reliability counters;
- repeated-run statistics and percentiles;
- repeatability evidence and protocol summaries;
- broader endpoint validation under load.

Exit gate:

- quality and runtime metrics are reported separately;
- no unavailable metric is represented as zero;
- benchmark protocol identity is persisted in the fingerprint;
- repeated/load protocols provide reproducible evidence rather than one-shot timing only.

## M3 — Run store and compatible comparison — IN PROGRESS

Goal: make results useful across changes rather than disposable single runs.

Integrated:

- SQLite durable store;
- working state separated from completed immutable evidence;
- atomic terminal publication;
- portable run ZIP export/import with integrity manifest;
- domain-owned dimension-specific compatibility semantics.

Remaining:

- aggregate/per-sample comparison query model;
- run identity diff;
- capability/runtime/resource delta reporting;
- retention/artifact policy;
- comparison evidence tests across compatible and incompatible runs.

Exit gate:

- a user can select two runs and understand both metric deltas and configuration differences;
- incompatible comparisons return typed reasons rather than misleading percentages.

## M4 — Custom workload evaluation

Goal: answer "which model is best for my scenario?" rather than only public benchmark questions.

Foundation already available:

- JSONL/CSV ingestion;
- explicit field mapping;
- deterministic local dataset snapshot identity.

Remaining milestone outcomes:

- reusable mapping configuration;
- task/evaluator templates for classification, extraction, QA and structured output;
- workload-pack versioning;
- first practical workload packs.

Candidate first workload packs:

- meeting intelligence;
- PII/entity extraction;
- structured document extraction.

Exit gate:

- a user can run the same workload dataset against multiple endpoints/configurations and compare task-relevant quality plus runtime metrics.

## M5 — Resource-aware local evaluation — IN PROGRESS

Goal: correlate inference quality/performance with device resource cost.

Integrated:

- telemetry collector interface and typed availability states;
- optional telemetry lifecycle that does not block black-box evaluation;
- portable process CPU/CPU-core evidence;
- peak RSS where the host exposes it;
- host load where available;
- collector overhead measurement and provenance.

Remaining:

- instrumented inference/runtime telemetry protocol;
- stronger run-window correlation and summary semantics;
- first real integration with a local/device serving project;
- later GPU/VRAM/unified-memory, thermal and reliable energy evidence.

Exit gate:

- the report clearly distinguishes endpoint-only, host-observed and runtime-native evidence;
- resource metrics can be used in compatible comparisons without contaminating basic endpoint evaluation.

## M6 — Regression automation

Goal: move evaluation into normal software/model engineering iteration.

Required outcomes:

- explicit baseline selection;
- versioned threshold policy;
- compatible dimension validation before threshold evaluation;
- stable JSON result schema;
- stable CLI exit codes;
- CI-friendly summary artifact;
- regression pass/fail with per-metric reasons.

Exit gate:

```text
run candidate
-> compare to explicit baseline
-> reject incomparable metrics
-> evaluate thresholds
-> produce machine-readable PASS / FAIL / NOT_COMPARABLE
```

CI integration must not make same-hardware claims on uncontrolled heterogeneous runners.

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

Exit gate:

- every important CLI/engine concept has a clear visual representation;
- identity differences and unavailable metrics remain visible;
- UI never recalculates benchmark semantics independently from core read models.

## M8 — External benchmark ecosystem

Goal: reuse mature benchmark task ecosystems while keeping Performance Lab focused on orchestration, local-device evidence and regression.

Required outcomes:

- external-runner plugin contract;
- configuration translation;
- version/provenance capture;
- normalized result import;
- artifact retention;
- explicit distinction between native and external evaluator results.

Potential integrations should be selected based on concrete coverage needs rather than added as mandatory dependencies.

## M9 — Additional AI task families

Future after the text-generation evaluation contracts are stable.

Candidate families:

- ASR: WER/CER, real-time factor, latency, memory;
- embeddings: retrieval quality, throughput, dimensionality/storage cost;
- rerankers: ranking quality and latency;
- vision/multimodal: task-specific accuracy plus image/token runtime cost.

The core extension should add task-family contracts, not provider-specific special cases.

## Product maturity boundaries

### Engine MVP

M0 complete + essential M1/M2/M3 outcomes + executable CLI run path.

### Practical local evaluation product

Engine MVP + M4 custom workloads + M5 resource evidence + baseline comparison.

### Engineering regression platform

Practical product + M6 automation/CI.

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
