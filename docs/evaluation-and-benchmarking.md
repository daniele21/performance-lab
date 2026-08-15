# Evaluation and benchmarking

Status: active
Document type: feature-specification
Owner: evaluation
Canonical scope: evaluation.benchmarking
Read when: adding datasets, evaluators, benchmark protocols, sampling policies or result aggregation
Last reviewed: 2026-08-15

## 1. Evaluation model

AI Performance Lab treats model evaluation as three related but distinct products:

1. **Capability evaluation** — correctness or task quality.
2. **Runtime benchmarking** — latency, throughput, reliability and load behavior.
3. **Workload evaluation** — capability + runtime metrics for a real application scenario.

These dimensions share one run/fingerprint/evidence model but must not be collapsed into one authoritative score.

## 2. Suite taxonomy

### General-purpose suite

A compact diagnostic suite intended to answer: "What obvious capability trade-offs does this configuration have?"

It should be fast enough to run on local devices and broad enough to expose differences across:

- instruction following;
- closed-form factual QA;
- reasoning;
- elementary mathematics;
- classification;
- structured output / JSON adherence;
- lightweight coding where deterministic execution is safe.

It is not a universal leaderboard and must not be described as one.

### Capability suite

A focused benchmark family such as reasoning, extraction, classification, code, long context or schema adherence.

### Workload suite

A domain-specific suite that reflects an application contract, for example:

- meeting summarization and action-item extraction;
- PII detection/redaction classification;
- financial document extraction;
- support ticket classification;
- code assistant tasks.

Workload suites should contain acceptance metrics that map to product risk, not only generic benchmark scores.

## 3. Dataset snapshot contract

A run never evaluates a mutable logical dataset directly. It evaluates an immutable `DatasetSnapshot`.

Required identity fields:

- dataset ID/name;
- source type;
- upstream version/revision when available;
- split;
- filters;
- sample-selection algorithm version;
- sample count;
- sampling seed;
- stable digest of selected sample identities/content where feasible;
- local mapping/configuration version for custom files.

Two runs using different snapshot identities must not be reported as same-test-set accuracy regressions.

## 4. Sample selection

Sampling should be deterministic by default.

Inputs:

- requested sample count;
- seed;
- split;
- optional stratification keys;
- optional filters.

The UI may offer convenient counts such as 10, 20, 50, 100, 200 or full set, but the core engine should support any valid positive count. Artificially constraining the engine to multiples of ten makes automation and external benchmark integration less flexible.

### Stratification

When categories/classes are known, optional stratified sampling should prevent small quick tests from accidentally excluding an important category.

The snapshot records whether sampling was:

- sequential;
- uniform random;
- stratified;
- externally predefined.

## 5. Task contract

A task definition separates raw data from execution behavior.

Conceptually:

```text
TaskSpec
  id + version
  dataset reference
  input renderer
  generation policy
  response parser
  evaluators[]
  aggregation policy
  tags/category
```

The task version changes when prompt rendering, parsing, evaluator assignment or material execution semantics change.

## 6. Generation policy

Benchmark runs require explicit generation settings.

Default quality-evaluation policy should favor reproducibility:

- temperature 0 or backend-equivalent deterministic mode when valid for the model/API;
- fixed seed when supported;
- bounded maximum output tokens;
- explicit stop behavior;
- explicit response format for structured tasks.

The run records the **effective** configuration, not only requested values.

Some benchmarks intentionally evaluate stochastic behavior or pass@k. Those must declare repetition count, seed strategy and aggregation semantics.

## 7. Native evaluator primitives

### Exact match

Use for canonical short answers where formatting can be normalized without changing meaning.

Normalization itself is versioned and may include documented operations such as whitespace trimming or case normalization.

### Numeric tolerance

Use for numeric outputs with explicit absolute or relative tolerance. Do not parse arbitrary prose into a number through broad heuristics unless the task specification defines that parser.

### Classification accuracy

Store correct/incorrect plus the normalized predicted class. Unknown/unparseable labels are explicit failures, not automatically coerced to the closest label.

### Precision / recall / F1

Use for entity/field/set extraction where false positives and false negatives matter separately.

Macro/micro/weighted aggregation must be named explicitly.

### Structured output validity

At least three independent signals can be useful:

1. parseable JSON;
2. JSON Schema adherence;
3. field-level semantic correctness.

A response may be valid JSON but semantically wrong. Do not combine these into a single hidden score.

### Code evaluation

Only execute model-generated code inside an explicit sandbox designed for untrusted code. Until such a sandbox exists, code tasks should use static/deterministic non-execution metrics or remain disabled.

## 8. Judge/rubric evaluation

LLM-as-a-judge is useful for tasks without an objective exact ground truth, but it introduces a second model and its own variance.

Every judge score must persist:

- judge provider/adapter;
- judge model/revision when known;
- judge prompt/rubric ID and version;
- generation settings;
- number of judge repetitions if applicable;
- parser/evaluator version.

Judge scoring is never allowed to overwrite deterministic metrics.

For sensitive/local-first workloads, an external judge may violate privacy expectations; the suite must be able to run without it or explicitly require an approved local judge target.

## 9. Capability aggregates

Store raw metric components before aggregates.

Recommended hierarchy:

```text
sample score
 -> task aggregate
 -> category aggregate
 -> suite aggregate
```

An overall suite score is allowed only when its weighting rule is explicit and versioned.

Do not average unrelated units such as accuracy, F1 and JSON validity into a number unless the suite defines a justified normalization and weighting scheme. Default reporting should show the dimensions separately.

## 10. Runtime benchmark protocol

### Single-request profile

For each measured attempt capture, when available:

- lab request start;
- first streamed content event;
- completion;
- input tokens;
- output tokens;
- status/error;
- retry count;
- endpoint-reported metrics separately.

Derived metrics:

- TTFT;
- total latency;
- generation/output tokens per second when token count is reliable;
- end-to-end tokens per second if explicitly defined;
- success/error/timeout rate.

### Warmup

Warmup requests are excluded from measured aggregates but retained as protocol metadata.

Default protocol should support a configurable number of warmups. The exact default is chosen after implementation experiments; it must not be hidden.

### Repetitions

A single timing is anecdotal. Default benchmark presets should run repeated measurements while allowing a quick mode with fewer samples.

Report sample count alongside every aggregate.

## 11. Cold-start policy

The lab cannot assume that the first request is a true cold model load.

Use explicit classifications:

- `CONTROLLED_COLD` — a cooperating adapter/runtime confirms model unloaded/reset precondition;
- `UNCONTROLLED_INITIAL` — first request observed without a guaranteed cold precondition;
- `WARMUP`;
- `WARM_MEASURED`.

Only `CONTROLLED_COLD` may support claims about model cold-load latency.

## 12. TTFT

TTFT is measurable only when the endpoint streams an observable first output event or returns a trustworthy provider timing field with clear provenance.

For non-streaming black-box APIs:

- lab TTFT = unavailable;
- total response latency remains available.

Never substitute total latency for TTFT.

## 13. Token throughput

Preferred token count provenance:

1. endpoint-reported input/output token counts with known semantics;
2. lab tokenizer explicitly matched to the evaluated model/tokenizer revision;
3. unavailable.

Do not tokenize with an arbitrary approximate tokenizer and label the result as model tokens/second.

If useful, a separate characters/second diagnostic may be reported with its own unit and name.

## 14. Concurrency/load evaluation

Supported profile concepts:

### Fixed concurrency

Run N workers until a fixed request/sample count completes.

### Fixed duration

Generate load for a bounded period with a documented arrival policy.

### Arrival-rate profile

Future/advanced: target requests per second and observe saturation/backpressure.

Metrics:

- completed requests/second;
- success/error/timeout counts;
- latency median and tail percentiles;
- queue/backpressure indicators when exposed;
- throughput degradation versus single-request profile.

## 15. Percentiles and statistics

Always display `n`.

For very small samples, emphasize raw values/median/range rather than implying statistical stability through p99 or similar metrics.

The statistics layer should support:

- mean where useful;
- median;
- min/max;
- standard deviation or robust dispersion;
- p90/p95 only above a configured minimum sample threshold;
- confidence intervals when the method and assumptions are explicit.

Regression decisions should not infer significance from a small percentage delta alone.

## 16. Reliability metrics

Runtime quality includes failure behavior.

Track separately:

- successful responses;
- HTTP/transport errors;
- normalized provider errors;
- timeouts;
- cancellations;
- malformed streaming responses;
- evaluator errors.

Evaluator errors are excluded from endpoint reliability denominators unless the evaluator failed because the endpoint response violated an explicit response contract.

## 17. Resource efficiency

Resource metrics are correlated evidence, not a requirement for a basic run.

Potential metrics when supported:

- peak and average RAM/RSS/PSS;
- peak VRAM/unified memory;
- CPU utilization;
- GPU utilization;
- thermal state/throttling;
- power/energy;
- model residency/load duration;
- KV/cache memory where the runtime exposes it.

Each metric must carry provenance and scope. A system-wide CPU percentage is not the same as inference-process CPU utilization.

## 18. Performance/quality comparison

The comparison report should be a trade-off matrix, not a winner declaration.

Example dimensions:

```text
Quality
  reasoning accuracy
  extraction F1
  schema adherence

Runtime
  TTFT
  total latency
  output tok/s
  throughput at concurrency N
  error rate

Resources
  peak memory
  average memory
  thermal throttling
```

A user may define a workload-specific decision policy later, but raw dimension deltas remain visible.

## 19. Regression semantics

Regression is stricter than general comparison.

Before applying thresholds, verify the metrics are comparable under the relevant fingerprint dimensions.

Examples:

- quality regression: same dataset snapshot, task/evaluator versions and compatible generation policy;
- latency regression: same or intentionally controlled hardware, benchmark protocol and load profile;
- memory regression: same telemetry collector semantics and attributable process/runtime scope.

If these conditions are not met, the engine returns `NOT_COMPARABLE` with reasons rather than pass/fail.

## 20. Benchmark presets

Initial product presets can provide progressive depth without changing core semantics.

### Quick

- small deterministic sample;
- minimal repetitions;
- capability + basic single-request performance;
- intended for rapid local iteration.

### Standard

- larger representative sample;
- warmup + repeated timing;
- category metrics;
- baseline comparison when selected.

### Comprehensive

- broader/full selected suite;
- more runtime repetitions;
- optional concurrency profile;
- telemetry when available;
- stronger evidence/report bundle.

### Custom

All policies explicit and editable.

Preset definitions are versioned. Changing a preset changes its version and appears in the fingerprint.

## 21. Starter general-purpose dataset design

The starter suite should prioritize diagnostic signal per inference cost.

Design rules:

- use redistributable datasets or metadata/loaders that comply with upstream licenses;
- avoid enormous downloads for the default quick path;
- keep categories balanced enough for small-sample testing;
- prefer deterministic ground truth;
- include difficulty/category metadata where possible;
- preserve upstream IDs/provenance;
- never silently modify ground truth to fit a particular model family.

A future benchmark-framework adapter may expose larger established suites without bundling their content in the repository.

## 22. Custom workload dataset lifecycle

User workflow:

```text
select file/source
 -> inspect columns/schema
 -> map input + expected output fields
 -> choose task/evaluator template
 -> validate sample preview
 -> freeze DatasetSnapshot
 -> execute
```

The import layer should generate a reusable versioned mapping configuration so repeated evaluations do not require manual remapping.

## 23. Benchmark evidence requirements

Every completed run report should expose:

- execution fingerprint hash plus readable key fields;
- suite and dataset snapshot identity;
- sample count/selection policy;
- effective generation settings;
- adapter/endpoint capabilities relevant to measurement;
- evaluator versions;
- runtime benchmark protocol;
- telemetry provenance/availability;
- failed/skipped sample counts;
- aggregate metrics;
- limitations/warnings.

A result without enough identity to reproduce or interpret it must be marked incomplete evidence.
