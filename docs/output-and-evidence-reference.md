# Output and evidence reference

Status: active
Document type: operational-reference
Owner: evidence model
Canonical scope: operations.output-evidence
Read when: interpreting a completed run, consuming `.plab.zip`, or deciding which evidence is safe to compare or retain
Last reviewed: 2026-08-15

Performance Lab produces evidence at multiple layers. Terminal output is only a pointer/presentation layer; the durable comparison contract is the immutable `Run` plus its `ExecutionFingerprint` and versioned regression artifacts.

## Evidence hierarchy

```text
CLI run result
   |
   +--> SQLite store
   |
   +--> .plab.zip
           |
           +--> manifest.json
           +--> run.json
                    |
                    +--> ExecutionFingerprint
                    +--> EvaluationSuite
                    +--> aggregate_scores
                    +--> aggregate_measurements
                    +--> samples[]
                           +--> token counts when observed
                           +--> measurements[]
                           +--> scores[]
                           +--> typed error when failed/cancelled
```

Comparison and regression consume immutable completed evidence; they do not infer results from console text.

## `performance-lab run --json`

The CLI emits a compact locator object:

```json
{
  "run_id": "...",
  "status": "succeeded",
  "fingerprint_id": "...",
  "store_path": ".performance-lab/runs.sqlite3",
  "bundle_path": ".performance-lab/<run-id>.plab.zip",
  "sample_count": 20
}
```

This object tells automation where the durable evidence lives. It is not the full benchmark result.

## Canonical `Run`

A persisted Run contains:

```text
schema_version
run_id
status
fingerprint
suite
created_at
completed_at
aggregate_scores[]
aggregate_measurements[]
samples[]
```

Terminal statuses are `succeeded`, `failed` and `cancelled`. Terminal runs require `completed_at`; non-terminal working state does not.

## `ExecutionFingerprint`

The fingerprint answers: **what exact evaluation configuration produced this evidence?**

It includes:

- target and adapter identity;
- persistence-safe endpoint identity;
- model ID plus revision/artifact digest/quantization when known;
- runtime name/version/config digest when known;
- hardware identity when known;
- generation configuration;
- prompt-template version;
- dataset snapshots and content hashes;
- evaluator versions;
- benchmark protocol version;
- load profile;
- telemetry level/protocol/collector identities.

The fingerprint ID is the content digest of the canonical serialized fingerprint. Missing optional identity is part of the fingerprint as explicit unknown state; it is never guessed.

## Model/runtime/hardware identity

Representative shape:

```json
{
  "model": {
    "model_id": "my-model",
    "revision": null,
    "artifact_digest": null,
    "quantization": "Q4_K_M"
  },
  "runtime": {
    "name": "llama_cpp",
    "version": "0.3.x",
    "config_digest": "..."
  },
  "hardware": {
    "device_id": null,
    "device_class": "arm64",
    "cpu": null,
    "accelerator": null,
    "memory_bytes": null,
    "os": "darwin"
  }
}
```

`null` means unknown/not observed. It does not mean zero and does not imply compatibility.

## Sample evidence

Each `SampleExecution` contains:

| Field | Meaning |
| --- | --- |
| `sample_id` | stable sample identity in the frozen dataset/suite |
| `task_id` | owning evaluation task |
| `attempt` | attempt number, starting at 1 |
| `status` | `succeeded`, `failed` or `cancelled` |
| `started_at` / `completed_at` | timezone-aware execution timestamps |
| `input_tokens` | observed input tokens or `null` |
| `output_tokens` | observed output tokens or `null` |
| `measurements[]` | latency/runtime/resource evidence |
| `scores[]` | evaluator results |
| `error` | typed bounded error information for non-successful samples |

The persisted Run schema deliberately does not contain raw prompt or generated model text. This reduces sensitive-content retention and prevents exported evidence from silently becoming a transcript/data dump.

## Scores

A score records:

```text
metric
value
evaluator { evaluator_id, version }
higher_is_better
numerator / denominator when applicable
```

Quality aggregation remains metric-specific. Performance Lab does not collapse capability, speed and resources into one universal opaque score.

## Measurements

Every measurement carries explicit scope and provenance:

```text
name
value
unit
scope       = sample | run
provenance  = client | host | runtime
protocol_version
observed_at (optional)
```

Examples:

- client-provenance latency or TTFT measured at the Performance Lab boundary;
- host-provenance CPU/memory observations;
- runtime-provenance Local LLM Server `/status` samples/aggregates.

A runtime-reported metric is not silently relabelled as a client-measured metric. Different measurement boundaries must remain distinguishable.

## Portable `.plab.zip`

A version-1 bundle contains exactly two files:

```text
manifest.json
run.json
```

`manifest.json` contains:

```json
{
  "bundle_version": 1,
  "run_schema_version": 1,
  "run_id": "...",
  "run_sha256": "<sha256-of-canonical-run-json>"
}
```

`run.json` contains the canonical serialized immutable Run.

Import validation rejects:

- extra/missing files in the ZIP;
- invalid JSON/ZIP encoding;
- unsupported bundle version;
- digest mismatch;
- manifest `run_id` mismatch;
- invalid Run schema.

The ZIP format is intentionally independent from SQLite internals.

## SQLite evidence store

The local store separates mutable working state from immutable completed evidence:

```text
working_runs
completed_runs
```

A completed `run_id` cannot be replaced by a different payload. Publishing the exact same canonical completed payload is idempotent; publishing different content under the same completed ID is rejected.

SQLite table layout is an implementation detail. External tooling should prefer the canonical Run/bundle or supported query/CLI boundaries rather than coupling to table columns.

## Comparison evidence

Before reporting deltas, Performance Lab checks dimension-specific compatibility. Expected experimental variables such as model/runtime/configuration can differ; invariants needed for a meaningful capability/runtime/resource comparison may not.

Typical examples:

- capability: dataset/evaluator/template/protocol must be compatible;
- runtime: load protocol and relevant hardware identity must be compatible;
- resource: hardware and telemetry protocol must be compatible.

A non-comparable result is evidence, not missing error handling.

## Regression artifacts

`regress` can emit a full machine-readable regression report with baseline/candidate identities, policy and per-rule results.

`regress-ci` additionally writes a durable CI JSON artifact and uses deterministic exit codes. The CI report preserves whether resource/hardware comparison was considered trustworthy under the runner-identity policy.

See [`ci-regression.md`](ci-regression.md).

## Privacy and retention boundary

The default canonical Run evidence is designed to keep enough information for reproducibility without automatically persisting sensitive prompt/output text. Retention policy may further reduce per-sample diagnostics/measurements before terminal publication while preserving fingerprint and aggregate evidence required by the configured policy.

Do not add plaintext credentials, raw private endpoint configuration or prompt/output content to fingerprint fields merely because they would make debugging easier.

## How to inspect a bundle manually

```bash
unzip -l result.plab.zip
unzip -p result.plab.zip manifest.json | python -m json.tool
unzip -p result.plab.zip run.json > /tmp/run.json
performance-lab inspect /tmp/run.json
```

The bundle digest is over the exact canonical `run.json` payload. If the payload is modified after export, a conforming import must reject it.

## What should be retained for a representative comparison

Keep together:

- baseline and candidate run IDs;
- both `.plab.zip` bundles;
- run configs;
- relevant endpoint/runtime revision;
- identity/telemetry protocol versions;
- regression policy;
- CI artifact where applicable;
- representative hardware/device context not already captured in the fingerprint.

A green unit-test run is not a substitute for this real evidence set.