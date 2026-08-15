# AI Performance Lab — implementation plan

Status: active
Document type: target-specification
Owner: repository
Canonical scope: target.repository
Read when: planning implementation work, checking dependencies, deciding what can run in parallel, or changing acceptance criteria
Last reviewed: 2026-08-15

This document is the canonical implementation plan for AI Performance Lab. It defines the target product boundary, work breakdown, dependencies, parallel execution lanes, acceptance criteria and milestone exit gates.

Operational status belongs in [`current-state.md`](current-state.md). Capability sequencing belongs in [`roadmap.md`](roadmap.md). Changes to this plan must be recorded in [`plan-changelog.md`](plan-changelog.md).

## 1. Product target

AI Performance Lab evaluates AI inference endpoints independently from the model runtime that serves them.

The core product must answer four separate questions:

1. **Capability** — how well does this endpoint solve a defined task or benchmark?
2. **Runtime performance** — how fast and reliable is inference under a defined load profile?
3. **Resource efficiency** — how much memory, compute, energy/thermal budget does the complete serving configuration consume when telemetry is available?
4. **Regression** — did a change in model, quantization, runtime, prompt, configuration, hardware or code improve or degrade a compatible baseline?

The primary unit of comparison is not a model name. It is an immutable **execution fingerprint** representing the complete evaluated configuration.

## 2. Non-goals for the first product slice

The first release does not:

- load GGUF, MLX, safetensors or other model artifacts itself;
- own llama.cpp, Ollama, MLX, vLLM, SGLang or vendor-specific runtime lifecycle;
- provide a public model hosting service;
- infer that two runs are comparable when critical identity fields differ;
- collapse quality, speed and resource consumption into one authoritative score;
- require an LLM-as-a-judge to evaluate deterministic tasks;
- require privileged host telemetry for basic endpoint evaluation;
- target multimodal, ASR, embedding or reranking evaluation before the text-generation core is stable.

## 3. Product layers

```text
User / CI / UI
      |
CLI + local API
      |
Evaluation Orchestrator
      |
+--------------------+--------------------+
|                    |                    |
Capability Engine    Runtime Benchmarks   Resource Correlator
|                    |                    |
Dataset Registry     Inference Adapter    Telemetry Adapter
         \             |                 /
          \------------+----------------/
                       |
                 External endpoint

All run inputs/results -> Run Store -> Comparison/Regression Engine -> Reports
```

The core must preserve these boundaries so that adding a new endpoint adapter, dataset family, evaluator or telemetry source does not require rewriting the orchestrator.

## 4. Canonical domain objects

Implementation may refine names, but these concepts must remain explicit.

### Target

A logical endpoint under test. Contains connection metadata and declared capabilities but no benchmark result state.

### EndpointProfile

Transport-specific configuration such as base URL, authentication strategy, model selector and timeout policy. Secrets must never be persisted in exported run artifacts.

### ExecutionFingerprint

Immutable identity of an evaluation configuration. At minimum:

- target/adapter type;
- endpoint identity safe for persistence;
- model identifier returned/selected;
- model artifact/revision/quantization when known;
- runtime name and version when known;
- hardware/device identity when known;
- generation configuration;
- prompt/template version;
- dataset snapshot/version;
- evaluator version;
- benchmark protocol version;
- concurrency/load profile;
- telemetry availability and measurement protocol.

Unknown fields remain explicitly unknown. They are never fabricated.

### EvaluationSuite

Versioned ordered set of tasks plus sample-selection policy, generation policy and evaluation rules.

### DatasetSnapshot

Immutable logical version of a dataset used by a run, including source, split, filtering/sampling policy and content digest or equivalent stable identity.

### Run

Top-level immutable evaluation execution with lifecycle state, fingerprint, suite, timestamps, environment, aggregate results and links to per-sample evidence.

### SampleExecution

One attempt against one dataset sample, with timing, response metadata, safe error state and evaluator output.

### Measurement

Typed runtime/resource measurement with unit, timestamp/scope and provenance.

### Score

Typed quality metric with evaluator identity, numerator/denominator where applicable and aggregation rules.

### Baseline

Explicit user- or policy-selected run used for compatible regression comparison. "Latest" must not silently become the baseline.

## 5. Status vocabulary

Every implementation item uses one of:

- `PLANNED` — defined but not dependency-ready;
- `READY` — dependencies satisfied and can start;
- `IN_PROGRESS` — implementation active;
- `BLOCKED` — cannot proceed; blocker must be named;
- `VALIDATION` — implementation exists but acceptance evidence is incomplete;
- `DONE` — acceptance criteria and documentation complete;
- `DEFERRED` — intentionally outside the current milestone.

The status shown in this file is the planning baseline only. Live status is maintained in [`current-state.md`](current-state.md).

## 6. Parallelization model

Work is organized into lanes. Tasks in different lanes may execute concurrently once their listed dependencies are satisfied.

| Lane | Workstream | Parallel intent |
| --- | --- | --- |
| `FND` | repository/contracts | establishes shared contracts; early critical path |
| `ADP` | inference adapters | parallel after core request/response contracts exist |
| `DAT` | datasets/suites | parallel after dataset/task schemas exist |
| `EVAL` | capability evaluation | parallel with runtime benchmarking after adapter contract exists |
| `PERF` | latency/throughput/load | parallel with capability evaluation |
| `TEL` | host/device telemetry | independent optional lane after measurement schema |
| `STO` | persistence/comparison | parallel after run/fingerprint schemas |
| `CLI` | command-line/API control plane | can start with fakes after orchestrator interface |
| `UI` | local visual interface | starts after query/read models stabilize; not on MVP critical path |
| `REG` | baselines/regression/CI | depends on stable run store and comparison semantics |
| `INT` | external-framework integrations | starts only after native task/evaluator contracts stabilize |
| `DOC` | docs/governance/evidence | continuous alongside every lane |

### Critical path to first useful MVP

```text
FND-001 repository skeleton
  -> FND-002 core domain contracts
  -> ADP-001 adapter contract + OpenAI-compatible adapter
  -> FND-004 orchestrator lifecycle
  -> +--------------------+
     |                    |
     EVAL-001             PERF-001
     |                    |
     +---------+----------+
               |
             STO-002 comparable run queries
               |
             REG-001 regression comparison
               |
             CLI-003 machine-readable run command
```

`DAT`, `TEL`, `STO` foundations and `CLI` scaffolding can progress in parallel with much of this path.

## 7. Work breakdown

### FND — repository and core contracts

#### FND-001 — repository foundation

Status baseline: `READY`
Dependencies: none
Parallel: no; first repository task

Deliverables:

- source/test/package skeleton;
- dependency and environment management;
- lint/format/type-check/test commands;
- CI validation workflow;
- license decision;
- branch/contribution policy;
- architecture-safe package naming.

Acceptance:

- clean checkout can install dependencies and run the repository validation command;
- no runtime/model dependency is embedded merely to make the skeleton compile;
- CI and local validation use the same core commands.

#### FND-002 — domain schemas and compatibility rules

Status baseline: `PLANNED`
Dependencies: FND-001
Parallel: unlocks `ADP`, `DAT`, `TEL`, `STO`

Deliverables:

- typed schemas for Target, EndpointProfile, ExecutionFingerprint, EvaluationSuite, DatasetSnapshot, Run, SampleExecution, Measurement and Score;
- schema/version fields;
- serialization rules;
- secret/privacy classification;
- explicit unknown/null semantics;
- compatibility rules for run comparison.

Acceptance:

- round-trip serialization tests;
- schema migrations/version rejection behavior is explicit;
- incompatible fingerprints produce typed non-comparability reasons rather than best-effort comparison.

#### FND-003 — plugin/registry contracts

Status baseline: `PLANNED`
Dependencies: FND-002
Parallel: yes

Define narrow replaceable interfaces for:

- inference adapters;
- task loaders;
- evaluators;
- telemetry collectors;
- result exporters;
- external benchmark runners.

Acceptance:

- deterministic fakes can exercise orchestrator tests without network/model dependencies;
- a plugin cannot mutate an immutable completed run.

#### FND-004 — evaluation orchestrator lifecycle

Status baseline: `PLANNED`
Dependencies: FND-002, ADP-001 interface portion
Parallel: partially with adapter implementation

Lifecycle:

```text
validate configuration
-> resolve target capabilities
-> freeze dataset snapshot + execution fingerprint
-> optional warmup
-> execute samples
-> capture measurements
-> evaluate responses
-> aggregate
-> persist immutable run
-> compare to optional baseline
-> export/report
```

Acceptance:

- cancellation, timeout, partial sample failure and total endpoint failure have typed outcomes;
- resumability policy is explicit: either resume a partial run under the same frozen identity or create a new run; never silently mix identities;
- progress events are observable without exposing prompt/output content by default.

---

### ADP — inference endpoint adapters

#### ADP-001 — generic adapter contract + OpenAI-compatible reference adapter

Status baseline: `PLANNED`
Dependencies: FND-002
Parallel: yes with DAT-001, TEL-001, STO-001

Required adapter capabilities:

- health/probe;
- model/capability discovery when available;
- non-streaming generation;
- streaming generation for TTFT;
- request cancellation;
- normalized token usage when returned;
- normalized typed errors;
- timeout and retry metadata;
- generation parameter capability map.

Acceptance:

- adapter tests use a local fake HTTP server;
- unsupported generation options fail or are reported explicitly; they are not silently dropped unless policy explicitly permits it and the run records the effective configuration;
- streaming timestamps allow TTFT measurement at the lab boundary.

#### ADP-002 — endpoint capability probe

Status baseline: `PLANNED`
Dependencies: ADP-001
Parallel: yes

Probe should distinguish declared, observed and unknown capabilities, including streaming, seed, response format/schema, token usage and model discovery.

#### ADP-003 — additional transport adapters

Status baseline: `DEFERRED`
Dependencies: ADP-001 stable contract

Candidates: native Ollama semantics, custom local server telemetry handshake, vendor-specific APIs. Add only when a real behavioral difference cannot be represented cleanly through the reference adapter.

---

### DAT — datasets and suite definition

#### DAT-001 — dataset/task schema

Status baseline: `PLANNED`
Dependencies: FND-002
Parallel: yes

Support:

- bundled datasets;
- user local files;
- deterministic sampling by seed;
- split selection;
- sample caps in configurable increments, with UI presets allowed but no core restriction to multiples of ten;
- task metadata and expected output contract;
- content digest/version provenance.

#### DAT-002 — general-purpose starter suite

Status baseline: `PLANNED`
Dependencies: DAT-001, EVAL-001 evaluator primitives
Parallel: partial

The starter suite must be compact enough for local-device testing and broad enough to detect obvious trade-offs. Initial categories:

- instruction following;
- factual/closed-form QA;
- reasoning;
- basic mathematics;
- classification;
- structured JSON extraction/adherence;
- lightweight code generation/evaluation where sandboxing is safe.

The suite must be documented as a diagnostic sample, not a universal model ranking.

#### DAT-003 — custom dataset import

Status baseline: `PLANNED`
Dependencies: DAT-001
Parallel: yes

Initial formats should prioritize JSONL/CSV with an explicit mapping wizard/config rather than heuristic field guessing.

#### DAT-004 — workload packs

Status baseline: `PLANNED`
Dependencies: DAT-003, EVAL-002
Parallel: yes after core evaluators

Versioned workload-specific suites such as meeting intelligence, PII extraction or domain classification. Workload packs must not leak product-specific logic into the generic execution engine.

---

### EVAL — capability evaluation

#### EVAL-001 — deterministic evaluator primitives

Status baseline: `PLANNED`
Dependencies: FND-003, DAT-001
Parallel: yes with PERF-001

Implement typed evaluators for:

- exact match / normalized exact match;
- numeric tolerance;
- classification accuracy;
- precision/recall/F1;
- regex/pattern validity where appropriate;
- JSON parsing and JSON Schema adherence;
- deterministic field-level extraction scoring.

Acceptance:

- metric aggregation is testable from static fixtures;
- normalization behavior is versioned;
- evaluator failures are distinct from model failures.

#### EVAL-002 — rubric and judge-based evaluation

Status baseline: `PLANNED`
Dependencies: EVAL-001 stable score model
Parallel: yes

Judge-based evaluation is optional and must record judge model, prompt/rubric version and sampling configuration. Deterministic metrics remain preferred when the task has an objective ground truth.

#### EVAL-003 — benchmark-framework bridge

Status baseline: `PLANNED`
Dependencies: FND-003, EVAL-001, stable run import/export schema
Parallel: `INT` lane

Integrate established evaluation frameworks through adapters rather than copying their task implementations into core. External results must retain framework/version/task provenance.

---

### PERF — endpoint runtime benchmarking

#### PERF-001 — single-request latency protocol

Status baseline: `PLANNED`
Dependencies: ADP-001, FND-002
Parallel: yes with EVAL-001

Capture separately:

- request setup time;
- TTFT when streaming is available;
- total latency;
- prompt/input token count when known;
- generated token count when known;
- output tokens/second;
- endpoint-reported prefill/decode metrics when available, marked as endpoint-originated rather than lab-measured.

Protocol must distinguish cold, warmup and measured warm runs.

#### PERF-002 — throughput and concurrency profiles

Status baseline: `PLANNED`
Dependencies: PERF-001
Parallel: yes

Support fixed request counts, fixed concurrency and bounded-duration load profiles. Capture latency distribution, throughput, success/error/timeout rate and backpressure behavior.

#### PERF-003 — repeatability/statistics

Status baseline: `PLANNED`
Dependencies: PERF-001

Report median, p90/p95 where sample sizes justify them, dispersion and raw sample counts. The UI/report must not display misleading percentiles for tiny samples without qualification.

---

### TEL — optional host/device telemetry

#### TEL-001 — telemetry collector contract

Status baseline: `PLANNED`
Dependencies: FND-002 measurement schema
Parallel: yes with ADP/DAT/STO

Collectors must be optional and capability-reported. A run remains valid when telemetry is unavailable.

#### TEL-002 — local host collector

Status baseline: `PLANNED`
Dependencies: TEL-001
Parallel: yes

Initial portable metrics:

- process/system memory where attribution is possible;
- CPU utilization;
- host load;
- collector overhead metadata.

Platform-specific GPU/VRAM/energy/thermal collectors must remain separate adapters.

#### TEL-003 — instrumented endpoint telemetry protocol

Status baseline: `PLANNED`
Dependencies: TEL-001, ADP-002
Parallel: yes

Define an optional safe contract for local servers to expose runtime/model/hardware/resource metadata. This enables deeper integration with projects such as Local LLM Server or Android Local LLM Harness without making it mandatory for third-party endpoints.

---

### STO — run persistence, evidence and comparison

#### STO-001 — immutable local run store

Status baseline: `PLANNED`
Dependencies: FND-002
Parallel: yes

Requirements:

- atomic run publication;
- partial/in-progress state separated from completed immutable evidence;
- schema versioning;
- bounded handling of raw response content according to privacy mode;
- export/import of portable run bundles;
- no plaintext credentials.

#### STO-002 — compatible comparison queries

Status baseline: `PLANNED`
Dependencies: STO-001, fingerprint compatibility rules, EVAL-001/PERF-001 result models

Compare quality and runtime dimensions independently. Surface identity differences before deltas.

#### STO-003 — retention and artifact policy

Status baseline: `PLANNED`
Dependencies: STO-001
Parallel: yes

Define retention for per-sample text, logs, telemetry series and aggregate metrics. Default mode should minimize sensitive prompt/output persistence while preserving enough evidence for reproducibility.

---

### CLI — developer control plane

#### CLI-001 — target and suite inspection

Status baseline: `PLANNED`
Dependencies: FND-003, ADP-001/DAT-001 interfaces
Parallel: yes using fakes

Commands should include target probe, dataset/suite list/inspect and configuration validation.

#### CLI-002 — interactive run command

Status baseline: `PLANNED`
Dependencies: FND-004, EVAL-001 or PERF-001

Provide progress, cancellation and clear result location.

#### CLI-003 — machine-readable automation mode

Status baseline: `PLANNED`
Dependencies: CLI-002, REG-001

Required for CI:

- stable exit codes;
- JSON output;
- baseline selection;
- threshold policies;
- no ANSI dependence;
- deterministic configuration file support.

---

### REG — comparison, regression and CI gates

#### REG-001 — baseline and compatibility engine

Status baseline: `PLANNED`
Dependencies: STO-002

A baseline must be explicit and immutable. Comparison result includes:

- compatible dimensions;
- incompatible/unknown dimensions;
- absolute and relative deltas;
- significance/uncertainty where supported;
- threshold result per metric.

#### REG-002 — regression policy file

Status baseline: `PLANNED`
Dependencies: REG-001

Example policy concepts:

```yaml
quality:
  overall_accuracy:
    max_relative_drop_pct: 1.0
runtime:
  ttft_ms:
    max_regression_pct: 10
  output_tokens_per_second:
    max_regression_pct: 5
reliability:
  error_rate:
    max_absolute: 0.01
```

Exact schema will be versioned during implementation.

#### REG-003 — CI integration

Status baseline: `PLANNED`
Dependencies: CLI-003, REG-002

Publish a concise pass/fail summary plus machine-readable artifact. CI must not claim hardware comparability when runner hardware is uncontrolled or identity differs.

---

### UI — local product interface

#### UI-001 — information architecture and run setup

Status baseline: `PLANNED`
Dependencies: domain/read-model stability; can prototype earlier with mocks
Parallel: not on MVP critical path

Primary surfaces:

- Targets;
- New Evaluation;
- Live Run;
- Results;
- Compare;
- Datasets/Suites;
- Baselines/Regression Policies;
- Settings/Telemetry.

#### UI-002 — results and comparison visualization

Status baseline: `PLANNED`
Dependencies: STO-002, REG-001

Quality, speed and resources remain visually separate. Comparison UI must foreground incompatible identities and confidence limitations.

---

## 8. Recommended execution waves

### Wave 0 — bootstrap contracts

Sequential core:

- FND-001
- FND-002

Can begin as soon as FND-002 schemas settle:

- FND-003
- ADP-001
- DAT-001
- TEL-001
- STO-001
- CLI-001 using fakes

### Wave 1 — first executable run

Parallel streams:

**Stream A — quality:** DAT-001 -> EVAL-001 -> DAT-002

**Stream B — runtime:** ADP-001 -> PERF-001 -> PERF-003

**Stream C — evidence:** STO-001 -> STO-003

**Stream D — optional observability:** TEL-001 -> TEL-002

Convergence: FND-004 orchestrates all streams into one immutable run.

### Wave 2 — comparison and practical usage

Parallel:

- PERF-002 concurrency/load;
- DAT-003 custom datasets;
- STO-002 comparison;
- CLI-002;
- TEL-003 instrumented telemetry;
- UI-001 prototype against stable read models.

Convergence: REG-001 compatible baseline comparison.

### Wave 3 — regression product

Parallel:

- REG-002 threshold policies;
- CLI-003 automation mode;
- UI-002 compare/regression views;
- DAT-004 workload packs;
- EVAL-002 judge/rubric evaluation.

Convergence: REG-003 CI gate.

### Wave 4 — ecosystem and expansion

After native contracts are stable:

- EVAL-003 external benchmark bridges;
- additional inference adapters;
- device-specific telemetry collectors;
- remote/distributed runner architecture if justified;
- ASR/embedding/reranking/vision task families through new task contracts rather than special cases in text-generation core.

## 9. MVP exit criteria

The first useful MVP is complete only when a user can:

1. register/probe an OpenAI-compatible local endpoint;
2. choose a versioned bundled suite or local custom dataset;
3. select a deterministic sample count/seed;
4. execute quality and runtime evaluation without modifying the inference service;
5. obtain per-task quality metrics and per-run latency/throughput/reliability metrics;
6. persist the complete execution fingerprint and immutable run results;
7. compare two compatible runs with explicit identity differences;
8. select a baseline and apply at least simple regression thresholds;
9. run the same workflow from CLI with machine-readable output;
10. understand when resource telemetry is unavailable rather than seeing fabricated zero values.

UI completion is desirable but is not required to prove the engine MVP if the CLI covers the workflow cleanly.

## 10. v0.1 target

Suggested v0.1 boundary:

- FND-001 through FND-004;
- ADP-001 and ADP-002;
- DAT-001 through DAT-003;
- EVAL-001;
- PERF-001 through PERF-003;
- TEL-001 and a basic TEL-002 where portable;
- STO-001 through STO-003;
- CLI-001 through CLI-003;
- REG-001 through REG-002;
- basic documentation, examples and deterministic integration tests.

REG-003 CI integration may ship in v0.1 if runner identity semantics are sufficiently clear; otherwise it becomes the first v0.2 item.

## 11. Plan maintenance rules

Every implementation change must update documentation in the same change when it affects status, scope, dependencies or acceptance criteria.

When work completes:

1. update live status in [`current-state.md`](current-state.md);
2. update the relevant milestone in [`roadmap.md`](roadmap.md);
3. change this plan only if the target, task decomposition, dependency or acceptance criteria changed;
4. append a dated entry to [`plan-changelog.md`](plan-changelog.md) whenever this plan changes materially;
5. add or update a focused specification when a workstream becomes too detailed for this repository-level plan;
6. never erase a blocker or deferred gate by marking the parent task done.

### Required plan-changelog entry

A material plan update records:

- date;
- affected task IDs;
- previous assumption;
- new decision;
- reason/evidence;
- dependency impact;
- roadmap/milestone impact.

## 12. Immediate next implementation block

Start with **FND-001 repository foundation** and **FND-002 domain schemas**. As soon as the FND-002 interfaces are stable enough, open parallel work on **ADP-001**, **DAT-001**, **TEL-001** and **STO-001** rather than serializing those independent workstreams.
