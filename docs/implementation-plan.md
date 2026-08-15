# AI Performance Lab — implementation plan

Status: active
Document type: target-specification
Owner: repository
Canonical scope: target.repository
Read when: planning implementation work, checking dependencies, deciding what can run in parallel, or changing acceptance criteria
Last reviewed: 2026-08-15

This document is the canonical implementation plan for AI Performance Lab. It owns product boundaries, task decomposition, dependencies and acceptance criteria. Live task status belongs in [`current-state.md`](current-state.md); capability sequencing belongs in [`roadmap.md`](roadmap.md); material plan changes belong in [`plan-changelog.md`](plan-changelog.md).

## 1. Product target

AI Performance Lab is an independent, hardware-aware evaluation and benchmarking layer for AI inference endpoints.

It must answer four separate questions:

1. **Capability** — how well does a model solve a defined task or benchmark?
2. **Runtime performance** — how fast and reliable is inference under a defined load profile?
3. **Resource efficiency** — what resource cost is observed when trustworthy telemetry is available?
4. **Regression** — did a model/runtime/configuration/code change improve or degrade a compatible baseline?

The evaluated unit is an immutable **execution fingerprint**, not a model name.

## 2. Ownership boundaries

Performance Lab owns:

- datasets, workload packs and sampling policy;
- benchmark/evaluator protocols;
- generation/load configuration;
- execution fingerprint assembly;
- client-boundary performance measurement;
- telemetry normalization/provenance;
- immutable run evidence;
- compatibility/comparison/regression semantics;
- CLI/CI/UI control surfaces.

Performance Lab does **not** own:

- model loading or backend lifecycle;
- GGUF/MLX/safetensors execution;
- backend resource allocation;
- provider-specific runtime truth that has not been exposed through a versioned contract;
- a universal opaque model score;
- inference hosting.

Generic OpenAI-compatible evaluation must remain valid without any Local LLM Server-specific integration.

## 3. Core invariants

### Execution identity

At minimum, the fingerprint can represent:

- target/adapter and safe endpoint identity;
- model ID, revision, artifact digest and quantization when known;
- runtime name, version and effective runtime-config digest when known;
- hardware/device identity when known;
- generation configuration;
- prompt/template version;
- dataset snapshots;
- evaluator versions;
- benchmark protocol;
- load profile;
- telemetry protocol/collectors.

Unknown remains unknown. Values are never inferred from suggestive filenames, arbitrary provider fields or unrelated counters.

### Result dimensions

Quality, runtime and resources remain separate. Compatibility is evaluated before deltas or thresholds.

Changing model/runtime/quantization/configuration is often the independent variable and therefore does not automatically make all result dimensions incomparable. Changes to dataset/evaluator/protocol/hardware that invalidate a dimension produce typed non-comparability.

### Evidence

Completed runs are immutable. Raw sensitive prompt/output retention is policy-controlled and minimized. Portable evidence must be independent from SQLite internals.

### Telemetry and identity

Black-box inference, frozen execution identity and dynamic telemetry are different concerns:

```text
inference response      -> answer / usage
identity provider       -> stable pre-run execution identity
telemetry collector     -> dynamic measurements during run
```

No one channel silently substitutes for another.

## 4. Product layers

```text
User / CI / UI
      |
CLI + local control surface
      |
Evaluation Orchestrator
      |
+---------------------+----------------------+---------------------+
|                     |                      |                     |
Capability Engine     Runtime Benchmarks     Identity Providers    Telemetry
|                     |                      |                     |
Dataset Registry      Inference Adapter      Versioned mapping     Collectors
         \             |                     |                    /
          \------------+---------------------+-------------------/
                                |
                         External endpoint
                                |
                   Run Store / portable evidence
                                |
                  Comparison / Regression Engine
```

## 5. Status vocabulary

Live status uses:

- `PLANNED`
- `READY`
- `IN_PROGRESS`
- `BLOCKED`
- `VALIDATION`
- `DONE`
- `DEFERRED`

This file does not duplicate live statuses. See [`current-state.md`](current-state.md).

## 6. Parallel work lanes

| Lane | Workstream | Parallel intent |
| --- | --- | --- |
| `FND` | repository/contracts/orchestrator | shared critical contracts |
| `ADP` | inference adapters | parallel after request/response domain |
| `DAT` | datasets/suites/workload packs | independent after dataset schema |
| `EVAL` | capability evaluation | parallel with runtime measurement |
| `PERF` | latency/throughput/load/statistics | parallel with evaluation |
| `TEL` | host/runtime telemetry | optional parallel instrumentation |
| `STO` | persistence/comparison/retention | parallel after run/fingerprint schemas |
| `CLI` | developer/automation control plane | converges existing engine pieces |
| `REG` | baseline/regression/CI | depends on comparison semantics |
| `UI` | local visual product | downstream of stable read models |
| `INT` | external runtime/framework integrations | versioned optional integrations |
| `REL` | release/reproducibility | cross-cutting hardening |
| `DOC` | governance/evidence | continuous |

## 7. Task registry and acceptance

### FND — foundation

#### FND-001 — repository foundation
Dependencies: none

Acceptance:

- clean checkout installs and runs the shared validation gate;
- local and CI validation use the same commands;
- no inference runtime is embedded merely to satisfy the package skeleton.

#### FND-002 — canonical domain and compatibility
Dependencies: FND-001

Acceptance:

- immutable/versioned schemas for endpoint, fingerprint, suite, dataset, run, sample, measurement and score;
- explicit unknown semantics;
- secrets cannot be serialized as endpoint credentials;
- dimension-specific compatibility returns typed reasons;
- runtime identity can include effective configuration identity when explicitly observed.

#### FND-003 — plugin/registry boundaries
Dependencies: FND-002

Acceptance:

- narrow adapter/dataset/evaluator/telemetry/export contracts;
- deterministic fakes exercise orchestration without network/model dependencies;
- plugins cannot mutate completed runs.

#### FND-004 — evaluation orchestrator
Dependencies: FND-002, ADP-001 interface

Lifecycle:

```text
validate
-> probe/resolve target
-> resolve optional first-party identity
-> freeze suite + fingerprint
-> optional warmup
-> execute samples
-> capture telemetry
-> evaluate + aggregate
-> publish immutable run
-> optional compare/regress
-> export
```

Acceptance includes typed cancellation/timeout/failure outcomes and content-safe progress events.

### ADP — inference endpoints

#### ADP-001 — OpenAI-compatible reference adapter
Dependencies: FND-002

Acceptance:

- probe, model discovery, non-streaming, streaming, cancellation and normalized errors;
- normalized token usage when returned;
- local fake HTTP coverage;
- unsupported options are explicit rather than silently discarded.

#### ADP-002 — evidence-based capability probe
Dependencies: ADP-001

Acceptance:

- declared, observed and unknown are distinct;
- streaming, usage, seed and structured-output checks preserve uncertainty.

#### ADP-003 — additional transport adapters
Dependencies: stable ADP-001

Add only when real behavior cannot be represented through the reference adapter. Otherwise defer.

### DAT — datasets and suites

#### DAT-001 — dataset/task schema
Dependencies: FND-002

Acceptance:

- local/bundled sources;
- immutable source/split/version/content identity;
- deterministic sample selection;
- explicit expected-output/evaluator mapping.

#### DAT-002 — general diagnostic starter suite
Dependencies: DAT-001, EVAL-001

Must remain a compact diagnostic suite, not a universal ranking. Initial coverage includes instruction following, closed-form QA, reasoning, basic math, classification and structured output.

#### DAT-003 — custom dataset import
Dependencies: DAT-001

JSONL/CSV mapping is explicit and reusable; semantic columns are not guessed.

#### DAT-004 — workload packs
Dependencies: DAT-003, EVAL evaluator primitives

Workload-specific suites compose normal dataset/evaluator contracts and do not branch the generic engine.

### EVAL — capability evaluation

#### EVAL-001 — deterministic evaluator primitives
Dependencies: FND-003, DAT-001

Acceptance:

- exact/normalized match;
- numeric tolerance;
- classification/F1;
- pattern validity where appropriate;
- JSON/JSON Schema;
- deterministic field extraction;
- evaluator failures remain distinct from model failures.

#### EVAL-002 — rubric/LLM judge
Dependencies: stable score model

Judge evaluation is opt-in and records judge model, adapter, rubric/prompt version and sampling configuration. Deterministic metrics remain preferred when objective ground truth exists.

#### EVAL-003 — external benchmark bridge
Dependencies: stable import/export/evaluator contracts

Bridge established frameworks through adapters rather than copying their tasks into core. Framework/task/version provenance must survive import.

### PERF — runtime benchmarking

#### PERF-001 — single-request protocol
Dependencies: ADP-001, FND-002

Capture setup/TTFT/total latency and token throughput only when the necessary evidence exists. Cold/warm/warmup semantics are explicit.

#### PERF-002 — concurrency/load protocol
Dependencies: PERF-001

Support fixed-count and bounded-duration profiles with throughput, reliability, queue/backpressure and latency-distribution evidence.

#### PERF-003 — repeatability/statistics
Dependencies: PERF-001

Report raw sample counts, dispersion and qualified percentiles; tiny samples must not be presented with misleading confidence.

### TEL — optional telemetry

#### TEL-001 — telemetry collector lifecycle
Dependencies: FND-002 measurement schema

Collectors are optional and capability-reported; collector failure does not fabricate zeros.

#### TEL-002 — host collector
Dependencies: TEL-001

Portable CPU/memory/load evidence where attribution is possible. Platform-specific GPU/energy/thermal collectors remain separate.

#### TEL-003 — generic instrumented runtime protocol
Dependencies: TEL-001, ADP-002

Safe versioned runtime-originated measurements and optional explicit identity, without making instrumentation mandatory for third-party endpoints.

### STO — persistence/comparison

#### STO-001 — immutable SQLite run store
Dependencies: FND-002

Acceptance:

- working state separated from completed evidence;
- atomic terminal publication;
- versioned portable ZIP bundle with integrity verification;
- no plaintext credentials.

#### STO-002 — compatible comparison
Dependencies: STO-001, compatibility rules, result models

Identity differences surface before deltas; quality/runtime/resource dimensions are independently comparable.

#### STO-003 — retention policy
Dependencies: STO-001

Retention is explicit for sample evidence, text/logs and aggregates, applied before immutable publication.

### CLI — control plane

#### CLI-001 — probe/inspect
Dependencies: adapter/dataset interfaces

Human-readable target/suite inspection without model-runtime ownership.

#### CLI-002 — end-to-end run
Dependencies: FND-004, evaluation/performance path

Versioned config drives endpoint -> suite -> fingerprint -> orchestration -> SQLite -> `.plab.zip`.

#### CLI-003 — machine-readable regression automation
Dependencies: CLI-002, REG-001

Stable JSON output and deterministic exit codes for PASS/FAIL/ERROR/NOT_COMPARABLE/NOT_EVALUATED.

### REG — regression and CI

#### REG-001 — explicit immutable baseline engine
Dependencies: STO-002

No implicit latest baseline. Compatibility is evaluated before metric deltas.

#### REG-002 — versioned threshold policy
Dependencies: REG-001

Metric direction and absolute/relative tolerance are explicit. Unknown evidence yields `NOT_EVALUATED` rather than an invented verdict.

#### REG-003 — CI integration
Dependencies: CLI-003, REG-002

Machine-readable artifact plus concise CI summary. Resource comparisons are conservative on uncontrolled runners.

### INT — external integrations

#### INT-001 — Local LLM Server runtime telemetry
Dependencies: ADP-001, TEL-001

Use normal OpenAI-compatible inference plus optional public `/status` polling. Preserve `chunks_per_second` as chunk evidence rather than relabeling it token throughput. Local LLM Server does not import Performance Lab.

Canonical spec: [`local-llm-server-integration.md`](local-llm-server-integration.md).

#### INT-002 — Local LLM Server execution identity
Dependencies: FND-002, INT-001 integration boundary; aligned Local LLM Server producer
Parallel: producer and consumer can implement against the same frozen protocol

Contract:

```text
GET /v1/runtime/identity
protocol = local-llm-identity-v1
```

Acceptance:

- strict versioned parsing with no arbitrary provider-field fallback;
- model ID/revision/digest/quantization -> `ModelIdentity`;
- backend name/version/effective config digest -> `RuntimeIdentity`;
- safe hardware characteristics -> `HardwareIdentity`;
- identity resolves before fingerprint freeze;
- explicit `required` mode can fail an evidence campaign when identity is unavailable;
- generic endpoints and older Local LLM Server versions remain valid when identity is optional;
- conflicting configured vs first-party hardware fails rather than silently selecting one source;
- `/status` telemetry remains independent;
- deterministic direct-client and end-to-end runner tests;
- producer and consumer use the same protocol/endpoint documentation.

Canonical spec: [`local-llm-identity-contract.md`](local-llm-identity-contract.md).

Future runtime-specific integrations require their own versioned contracts only when generic inference/telemetry/identity boundaries are insufficient.

### UI — local product surface

#### UI-001 — run setup IA
Dependencies: stable domain/read models

Primary surfaces: Targets, New Evaluation, Live Run, Results, Compare, Datasets/Suites, Baselines/Policies, Settings/Telemetry.

#### UI-002 — comparison visualization
Dependencies: STO-002, REG-001

Quality, speed and resources remain visually separate; incompatible identity is foregrounded.

### REL — reproducibility/release

#### REL-001 — constrained CI dependency snapshot
Dependencies: repository validation stack

Supported CI Python environments install through a committed exact constraint snapshot and validate that direct dependencies/resolved versions match it. This is CI resolver reproducibility, not a claim of universal cross-platform lock reproducibility.

## 8. Execution waves

The historical bootstrap waves are complete in implementation. The active dependency structure is now evidence-oriented:

```text
             integrated engine + regression core
                         |
       +-----------------+------------------+
       |                 |                  |
       v                 v                  v
real endpoint        real runtime       real CI gate
quality/perf         identity+telemetry  baseline/candidate
       |                 |                  |
       +-----------------+------------------+
                         |
                  retained evidence set
```

Parallel non-blocking work can continue on UI-002, additional workload packs and selected platform telemetry. EVAL-003 should start only when representative evidence exposes a real benchmark-coverage gap.

## 9. MVP/evidence exit criteria

The useful engine MVP requires a user to be able to:

1. probe an OpenAI-compatible endpoint;
2. choose a versioned bundled suite or explicit local custom dataset;
3. execute deterministic quality/runtime evaluation without modifying the inference service;
4. persist a complete honest execution fingerprint plus immutable run results;
5. observe unavailable identity/telemetry rather than fabricated values;
6. compare compatible result dimensions and surface identity differences;
7. select an immutable baseline and apply versioned regression policy;
8. run the same workflow from CLI/CI with machine-readable outcomes;
9. preserve a portable evidence bundle;
10. for an instrumented Local LLM Server target, optionally freeze first-party model/runtime/hardware identity and correlate dynamic runtime telemetry.

Implementation completion does not by itself close evidence milestones. Representative model/device/load/CI runs must be retained according to [`roadmap.md`](roadmap.md) and [`definition-of-done.md`](definition-of-done.md).

## 10. Plan maintenance

For each coherent implementation change:

- update [`current-state.md`](current-state.md) when live status or immediate next work changes;
- update this plan only when target/task/dependency/acceptance changes;
- update [`roadmap.md`](roadmap.md) when milestone scope/status changes;
- append [`plan-changelog.md`](plan-changelog.md) for material plan changes;
- create/update a focused specification only for a durable bounded concern;
- do not create temporary task-completion documents when the information belongs in an existing canonical owner.

## 11. Immediate planned implementation boundary

No new core abstraction is the default next step. Close the aligned Local LLM Server identity integration, then prioritize representative evidence:

1. real resident-model starter/workload runs with retained `.plab.zip` and frozen identity;
2. repeated/concurrent performance evidence on controlled hardware;
3. Local LLM Server identity + `/status` telemetry correlation;
4. real baseline/candidate `regress-ci` evidence;
5. UI-002/additional workload packs in parallel where useful.

Only add a new adapter, telemetry source or benchmark bridge when those runs expose a concrete missing capability.
