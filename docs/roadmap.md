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
| M0 — Repository and contracts | In progress | validated foundation + remaining plugin/registry/fake boundary | adapters, datasets, telemetry and storage are now unlocked in parallel |
| M1 — First black-box evaluation | Planned | run a deterministic quality suite against an OpenAI-compatible endpoint | quality and runtime benchmark engines in parallel |
| M2 — Runtime performance evidence | Planned | TTFT/latency/throughput/reliability with repeatable protocols | runs alongside M1 quality engine work |
| M3 — Run store and comparison | Planned | immutable fingerprints, history and compatible run comparison | storage can begin during M1/M2 |
| M4 — Custom workload evaluation | Planned | import local datasets and create reusable workload suites | parallel with comparison/telemetry |
| M5 — Resource-aware local evaluation | Planned | host/device telemetry and instrumented endpoint correlation | telemetry lane is mostly independent |
| M6 — Regression automation | Planned | explicit baselines, threshold policies and machine-readable CLI | UI work may run in parallel |
| M7 — Local product UI | Planned | configure, run, inspect and compare evaluations visually | not on engine MVP critical path |
| M8 — External benchmark ecosystem | Planned | bridge established evaluation frameworks without duplicating them | after native contracts stabilize |
| M9 — Additional AI task families | Future | ASR, embeddings, reranking, vision through generic task extensions | independent task-family workstreams after text core |

## M0 — Repository and contracts

Goal: establish a project that can evolve without coupling the core to a model runtime or UI.

Implemented and validated:

- repository toolchain, lint/type/test/CI foundation;
- branch and contribution policy;
- MIT license;
- immutable domain schemas and schema versioning;
- deterministic execution fingerprint identity;
- dimension-specific compatibility semantics;
- privacy-safe endpoint credential references;
- clean-checkout validation on Python 3.12 and 3.13.

Remaining before M0 closes:

- plugin interfaces for inference, datasets/evaluators, telemetry, stores/exporters;
- deterministic fakes for orchestration tests;
- integration-line bootstrap for parallel work.

Exit gate:

- clean checkout validation works;
- core domain serialization tests pass;
- adapter, dataset, telemetry and storage lanes can implement against stable enough contracts without importing one another;
- FND-003 contracts/fakes are usable by the first downstream implementations.

## M1 — First black-box capability evaluation

Goal: connect to an OpenAI-compatible endpoint and obtain trustworthy quality scores from a versioned suite.

Required outcomes:

- OpenAI-compatible adapter with streaming/non-streaming normalized behavior;
- endpoint capability probe;
- dataset snapshotting and deterministic sampling;
- deterministic evaluators;
- compact general-purpose starter suite;
- orchestrator lifecycle with cancellation/failure semantics;
- per-sample and aggregate results.

Exit gate:

- a local endpoint can be evaluated without Performance Lab knowing how the model is hosted;
- the completed run has a reproducible fingerprint and immutable result bundle;
- unsupported/unknown endpoint features are explicit.

## M2 — Runtime performance evidence

Goal: measure serving behavior independently from quality scoring.

Required outcomes:

- client-observed total latency;
- TTFT for streaming endpoints;
- reliable output token throughput when token counts are valid;
- warmup/repetition policy;
- controlled versus uncontrolled cold-start semantics;
- repeated timing statistics;
- fixed-concurrency load profile;
- typed reliability/error metrics.

Exit gate:

- quality and runtime metrics are reported separately;
- no unavailable metric is represented as zero;
- benchmark protocol identity is persisted in the fingerprint.

## M3 — Run store and compatible comparison

Goal: make results useful across changes rather than disposable single runs.

Required outcomes:

- durable immutable completed-run store;
- partial-run working state separated from completed evidence;
- aggregate and per-sample query model;
- portable run export/import;
- run identity diff;
- dimension-specific compatibility rules;
- quality/runtime/resource delta reporting.

Exit gate:

- a user can select two runs and understand both the metric deltas and the configuration differences that produced them;
- incompatible comparisons return reasons rather than misleading percentages.

## M4 — Custom workload evaluation

Goal: answer "which model is best for my scenario?" rather than only public benchmark questions.

Required outcomes:

- JSONL/CSV import;
- explicit column/schema mapping;
- reusable mapping configuration;
- local dataset snapshot identity;
- task/evaluator templates for classification, extraction, QA and structured output;
- workload-pack versioning.

Candidate first workload packs:

- meeting intelligence;
- PII/entity extraction;
- structured document extraction.

Exit gate:

- a user can run the same workload dataset against multiple endpoints/configurations and compare task-relevant quality plus runtime metrics.

## M5 — Resource-aware local evaluation

Goal: correlate inference quality/performance with device resource cost.

Required outcomes:

- telemetry collector interface and typed availability states;
- portable local host CPU/memory evidence where attributable;
- optional instrumented inference telemetry protocol;
- run-window correlation;
- peak/average resource summaries with provenance;
- first real integration with a local/device serving project.

Later within the milestone:

- GPU/VRAM/unified-memory collectors;
- thermal state;
- power/energy where reliable.

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

M0 through the essential parts of M1, M2 and M3 plus a CLI execution path.

### Practical local evaluation product

Engine MVP + M4 custom datasets + basic M5 telemetry + baseline comparison.

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
