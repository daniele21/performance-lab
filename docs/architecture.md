# Architecture

Status: active
Document type: architecture
Owner: repository
Canonical scope: architecture.repository
Read when: implementing a component, changing dependency boundaries, adding an adapter, or deciding where new behavior belongs
Last reviewed: 2026-08-15

## 1. Architectural objective

AI Performance Lab is an evaluation control plane around externally served AI models.

The lab owns **evaluation orchestration, measurement, scoring, evidence and comparison**. It does not own model runtime lifecycle in the core product.

This boundary is deliberate: the same evaluation engine should be usable against a local llama.cpp server, LM Studio, Ollama, an Android-exposed endpoint, a custom local inference service or a remote API, provided an adapter can express the required request/response behavior.

## 2. System context

```text
                     +-----------------------------+
                     |      AI Performance Lab     |
                     |                             |
                     | suites / runs / comparison |
                     +--------------+--------------+
                                    |
                          normalized inference API
                                    |
              +---------------------+--------------------+
              |                     |                    |
        local server           device server         remote API
              |                     |                    |
        llama.cpp / MLX        Android runtime        provider
              |                     |                    |
              +---------------------+--------------------+
                                    |
                         model + runtime + device
```

Optional instrumentation is a separate channel:

```text
Inference endpoint  <------ requests ------  Performance Lab
       |
       +------ optional telemetry ------->  Telemetry collector
```

A black-box run remains valid when the telemetry channel does not exist.

## 3. Dependency direction

Preferred logical dependency direction:

```text
presentation / CLI / API
          |
          v
application orchestration
          |
          v
core domain contracts
       /   |    \
      v    v     v
 adapters evaluators stores
      |           |
 external IO    persistence
```

Rules:

- domain types do not depend on HTTP clients, databases, UI frameworks or benchmark libraries;
- orchestration depends on interfaces, not concrete endpoint/runtime implementations;
- endpoint adapters do not own scoring policy;
- evaluators do not call the endpoint directly;
- telemetry collectors do not decide benchmark pass/fail;
- persistence does not redefine compatibility rules;
- UI does not reconstruct domain calculations from raw database rows.

## 4. Proposed package/module ownership

Exact language/runtime choice is a foundation task, but the ownership model should resemble:

```text
performance_lab/
  core/
    models
    fingerprints
    compatibility
    errors
  orchestration/
    run_engine
    progress
    cancellation
  adapters/
    inference/
      openai_compatible
    telemetry/
  datasets/
    registry
    loaders
    sampling
  evaluation/
    deterministic
    rubric
  benchmarking/
    latency
    throughput
    statistics
  storage/
    runs
    artifacts
    migrations
  comparison/
    baselines
    regressions
  cli/
  api/
  ui/                # when introduced
```

Create real boundaries only when behavior exists. Do not create empty modules merely to mirror this diagram.

## 5. Inference adapter contract

The adapter isolates provider/transport differences from evaluation logic.

Conceptual interface:

```text
probe(target) -> EndpointCapabilities
invoke(request, cancellation) -> InferenceResult
stream(request, cancellation) -> stream<InferenceEvent>
```

Normalized request contains:

- messages or task input;
- requested generation configuration;
- optional response-format/schema intent;
- timeout/deadline;
- request correlation ID.

Normalized result/event should expose only facts actually known:

- output text/content;
- finish reason when available;
- model identifier when available;
- input/output token counts when available;
- provider request ID when safe/useful;
- normalized error;
- timestamps measured at the lab boundary;
- provider-reported timings in a separate provenance namespace.

### Effective configuration

A major source of invalid benchmark comparisons is assuming requested parameters were honored.

For every run, the adapter must represent one of:

1. parameter supported and effective value known;
2. parameter unsupported and request rejected;
3. parameter unsupported but explicitly ignored under a user-approved compatibility policy;
4. effective value unknown.

Silent parameter loss is not acceptable for benchmark evidence.

## 6. Execution fingerprint

The execution fingerprint is the core reproducibility contract.

Conceptually:

```text
ExecutionFingerprint
  target
    adapter_type
    endpoint_safe_id
  model
    model_id
    revision?
    artifact_digest?
    quantization?
  runtime
    name?
    version?
  generation
    temperature
    top_p
    top_k?
    seed?
    max_output_tokens
    response_format?
    ...
  prompt
    template_id
    template_version
  dataset
    dataset_id
    snapshot_digest
    split
    sample_policy
  evaluator
    evaluator_versions
  benchmark_protocol
    protocol_version
    warmup_policy
    repetition_policy
    concurrency
  environment
    device_id?
    os?
    cpu?
    gpu?
    memory?
  telemetry
    collectors + versions
```

Fingerprint serialization must be canonical before hashing.

Two runs can be partially comparable. Compatibility is therefore dimension-specific rather than a single boolean.

Example:

- same dataset/evaluator/generation but different hardware: capability scores may be comparable; latency is not a hardware-neutral regression;
- same model/hardware but different dataset snapshot: runtime performance may be comparable under the same token/load profile, benchmark accuracy is not;
- same model name but different quantization: comparison is allowed as an explicit configuration comparison, but it must never be described as a same-configuration regression.

## 7. Run lifecycle and state machine

Suggested lifecycle:

```text
DRAFT
  -> VALIDATING
  -> READY
  -> RUNNING
       -> CANCELLING -> CANCELLED
       -> FAILED
       -> AGGREGATING
  -> COMPLETED
```

Completed runs are immutable.

A partial working area may persist checkpoints, but publication into the completed run store must be atomic enough that consumers do not mistake partial evidence for complete results.

### Sample lifecycle

Each sample records independently:

```text
PENDING -> RUNNING -> SUCCESS
                   -> MODEL_ERROR
                   -> ADAPTER_ERROR
                   -> TIMEOUT
                   -> CANCELLED
                   -> EVALUATOR_ERROR
```

Evaluator failure is not model failure. Transport timeout is not an incorrect answer. Aggregations must preserve this distinction.

## 8. Reproducibility rules

### Dataset freeze

At run start, resolve dataset source + split + filter + deterministic sample selection into a `DatasetSnapshot` identity. The run must not observe a dataset changing underneath it.

### Configuration freeze

Freeze endpoint profile references, generation settings, suite version, evaluator versions and benchmark protocol before the first measured sample.

### Randomness

Use deterministic seeds where supported and meaningful. Record when the serving backend does not support deterministic seeding.

For stochastic quality evaluation, repeated sampling is a benchmark-policy decision and must be explicit.

### Clock

Use monotonic clocks for elapsed duration. Wall clock timestamps are for audit/order only.

## 9. Runtime measurement architecture

The lab measures what it owns at the client boundary:

```text
request start
  -> connection/request processing
  -> first streamed output event      = lab TTFT
  -> final output event
  -> response completion              = total latency
```

Endpoint-reported prefill/decode/load timings may be stored, but are tagged as `endpoint_reported` and must not be conflated with lab-observed metrics.

For tokens/second:

- prefer output token count returned by the endpoint when reliable;
- otherwise use a configured tokenizer only when tokenizer/model compatibility is known;
- if token count cannot be established reliably, report character/byte timing only or mark throughput unavailable rather than fabricate token throughput.

## 10. Cold, warm and load protocols

Cold/warm classification must be explicit.

The lab cannot universally force a third-party model runtime to unload. Therefore a `cold` benchmark is only valid when the adapter or external orchestration can establish a documented cold precondition.

Protocol labels:

- `UNCONTROLLED_INITIAL` — first observed request, but cold state not guaranteed;
- `CONTROLLED_COLD` — external/adapter hook proves cold precondition;
- `WARMUP` — excluded from measured aggregates;
- `WARM_MEASURED` — post-warmup measured samples;
- `LOAD_TEST` — concurrent/throughput profile.

Do not label `UNCONTROLLED_INITIAL` as cold in reports.

## 11. Telemetry architecture

Three telemetry levels:

### Level 0 — endpoint-only

Always available:

- client-observed latency;
- TTFT when streamable;
- success/error/timeout;
- token usage when endpoint reports it.

### Level 1 — lab-host telemetry

Collected from the machine running Performance Lab. Useful only when the inference runtime is co-located or when system-level metrics are intentionally being measured.

Possible metrics:

- system CPU;
- system/process memory;
- load average;
- network transfer.

The collector must record attribution limitations.

### Level 2 — instrumented inference host/device

A cooperating server/agent exposes:

- model/runtime identity;
- model load/residency state;
- process memory/RSS/PSS;
- GPU/VRAM/unified memory;
- CPU/GPU utilization;
- thermal state;
- energy/power where available;
- runtime-native prefill/decode/load metrics.

This is the preferred path for meaningful local-device resource benchmarking.

## 12. Telemetry correlation

Every telemetry sample requires:

- monotonic timestamp or synchronized time basis;
- collector identity/version;
- metric name/unit;
- scope (system/process/device/runtime/request/run);
- provenance;
- optional request/run correlation ID.

Clock synchronization between a remote instrumented device and lab host must be addressed before claiming precise request-level correlation. Until then, remote telemetry may be correlated to a run window rather than individual token events.

## 13. Dataset and evaluator architecture

A task is separated into:

```text
Dataset sample
  -> input renderer
  -> inference request
  -> response parser
  -> evaluator(s)
  -> typed score(s)
```

This allows the same dataset sample to support different prompt templates or response formats without duplicating the raw dataset.

Evaluator implementations are versioned independently from datasets because changing normalization or scoring semantics changes results even when dataset content is unchanged.

## 14. External benchmark frameworks

Frameworks such as lm-evaluation-harness or other evaluation packages should be integrated through a bridge that translates:

```text
Performance Lab run config
  -> external framework config
  -> execution
  -> normalized imported evidence
```

The lab must preserve external framework name/version/task/configuration. It must not pretend externally computed scores were produced by native evaluators.

The native engine remains necessary for workload-specific/custom datasets, runtime metrics, telemetry correlation and regression orchestration.

## 15. Persistence model

Recommended storage split:

### Metadata/index store

Queryable:

- targets;
- suites;
- run headers;
- fingerprints;
- aggregate scores;
- aggregate runtime metrics;
- baseline relationships;
- compatibility/comparison results.

### Artifact store

Potentially larger:

- per-sample records;
- raw/sanitized outputs when persistence is enabled;
- telemetry time series;
- imported external benchmark artifacts;
- reports.

A local relational database plus filesystem/content-addressed artifacts is sufficient initially. Database choice is an implementation detail as long as migration and atomicity contracts are maintained.

## 16. Privacy modes

At least two modes should exist conceptually:

### Aggregate-safe

Default for general use/CI:

- persist metrics, hashes, task/sample IDs and typed failures;
- do not persist prompt/output text unless required by the evaluator evidence policy.

### Evidence-rich

Explicit opt-in:

- persist sample inputs/outputs required for debugging;
- clearly mark artifacts as potentially sensitive;
- provide retention/delete controls.

Credentials, authorization headers and signed secrets are never part of either mode.

## 17. Comparison engine

Comparison proceeds in this order:

1. load both immutable run fingerprints;
2. compute identity diff;
3. determine comparable metric dimensions;
4. align tasks/samples where relevant;
5. calculate deltas/statistics;
6. evaluate configured thresholds;
7. emit typed comparison result with limitations.

A comparison report should make configuration differences more visible, not less visible.

## 18. Failure philosophy

Prefer explicit unavailable/unknown/incompatible states over invented defaults.

Examples:

- no streaming -> TTFT unavailable, not zero;
- no token usage -> token throughput unavailable unless a compatible tokenizer is configured;
- telemetry collector permission denied -> run continues with telemetry status `UNAVAILABLE_PERMISSION`;
- model revision unknown -> fingerprint says unknown;
- judge evaluator unavailable -> deterministic metrics may complete while judge score is separately failed/unavailable.

## 19. Extension rules

Add a new module/interface only when it owns one of:

- an autonomous domain responsibility;
- a third-party/platform boundary;
- a reusable behavior used by multiple consumers;
- a distinct testing/release boundary.

Do not add provider-specific branches inside the orchestrator when an adapter can own the difference.

Do not add benchmark-specific conditionals inside persistence or UI; normalize through task/evaluator contracts.

## 20. Architectural decisions still open

Tracked for FND-001/FND-002:

- implementation language/runtime and package strategy;
- local persistence technology;
- configuration file format and schema tooling;
- plugin discovery mechanism;
- whether the local UI is served by the same API process or a separate frontend;
- exact safe endpoint identity hashing/redaction policy;
- initial instrumented telemetry protocol transport.

Durable choices should be recorded as ADRs under `docs/adr/` once decided.
