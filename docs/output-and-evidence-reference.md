# Output and evidence reference

Status: active
Document type: operational-reference
Owner: evidence model
Canonical scope: operations.output-evidence
Read when: interpreting a completed run, consuming `.plab.zip`, or deciding which evidence is safe to compare or retain
Last reviewed: 2026-09-01

Performance Lab produces evidence at multiple layers. Terminal output is only a pointer/presentation layer; the durable comparison contract is the immutable `Run` plus its `ExecutionFingerprint` and versioned regression artifacts.

## Evidence hierarchy

```text
CLI run result
   |
   +--> SQLite store
   |       |
   |       +--> canonical Run evidence
   |       +--> optional local-only sample content sidecar (evidence-rich mode)
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

Comparison and regression consume immutable completed Run evidence; they do not infer results from console text or require prompt/output transcripts.

## `performance-lab run --json`

The CLI emits a compact locator object. With the default store and current `general-diagnostic-starter` v1 suite, a representative result is:

```json
{
  "run_id": "run-...",
  "status": "succeeded",
  "fingerprint_id": "...",
  "store_path": ".performance-lab/runs.sqlite3",
  "bundle_path": ".performance-lab/artifacts/run-....plab.zip",
  "sample_count": 23
}
```

The current suite contains 20 unique authored records but produces 23 `SampleExecution` records because the structured dataset is evaluated by two separate tasks. Future suite versions may change that count.

This locator object tells automation where the durable evidence lives. It is not the full benchmark result.

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

Each canonical `SampleExecution` contains:

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

The canonical Run schema deliberately does **not** contain raw prompt or generated model text. This keeps comparison/export evidence aggregate-safe and prevents a portable bundle from silently becoming a transcript/data dump.

### Evidence-rich local sample content

`evidence_mode=evidence_rich` adds a separate local-only `SampleContentEvidence` record keyed by `run_id + task_id + sample_id + attempt`. It contains:

```text
prompt     exact rendered chat content sent through the adapter
response   exact generated text when a response was produced
```

The capture path writes the prompt before inference and the response after generation. Therefore a failed inference can truthfully retain a prompt while the response remains unavailable. The browser never reconstructs either value from benchmark source data.

The local SQLite store keeps rich content outside canonical Run JSON:

```text
working_sample_content
completed_sample_content
```

Working content is promoted in the same SQLite transaction that publishes the completed Run. If the process hard-restarts before publication, working raw content is deleted because current recovery is `NEW_RUN_ONLY`, while bounded interrupted-run metadata remains available for recovery UX. Completed raw content can be deleted independently without changing the immutable canonical Run.

The browser **Test a model** flow defaults to this evidence-rich mode so Sample Evidence can show, in distinct panels:

1. the prompt actually sent to the model;
2. the model output;
3. the benchmark expected output;
4. the evaluator-owned correctness/score summary.

Campaign, CLI and CI/regression defaults remain aggregate-safe unless a caller explicitly opts into richer retention where supported.

## Scores

A score records:

```text
metric
value
evaluator { evaluator_id, version }
higher_is_better
numerator / denominator when applicable
```

Quality aggregation remains metric-specific. Performance Lab does not collapse capability, speed and resources into one universal opaque score. Sample-detail correctness labels are derived in the Python evidence owner only for metrics whose per-case values have explicit 0..1 correctness semantics; other metrics remain generically `scored` rather than receiving an invented pass/fail label.

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

The starter runner writes bundles beside the SQLite store under an `artifacts/` directory. With the default store path:

```text
.performance-lab/runs.sqlite3
.performance-lab/artifacts/<run-id>.plab.zip
```

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

`run.json` contains the canonical serialized immutable Run. **Evidence-rich prompt/model-output sidecars are never included in version-1 bundles.**

Import validation rejects:

- extra/missing files in the ZIP;
- invalid JSON/ZIP encoding;
- unsupported bundle version;
- digest mismatch;
- manifest `run_id` mismatch;
- invalid Run schema.

The ZIP format is intentionally independent from SQLite internals.

## SQLite evidence store

The local store separates mutable working state from immutable completed evidence and, when explicitly enabled, sensitive local content:

```text
working_runs
completed_runs
working_sample_content       # evidence-rich only
completed_sample_content     # evidence-rich only
```

A completed `run_id` cannot be replaced by a different canonical payload. Publishing the exact same canonical completed payload is idempotent; publishing different content under the same completed ID is rejected.

SQLite table layout is an implementation detail. External tooling should prefer the canonical Run/bundle or supported query/API boundaries rather than coupling to table columns. In particular, do not treat the sidecar tables as a portable evidence format.

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

The default canonical Run evidence is designed to keep enough information for reproducibility without persisting sensitive prompt/output text. `aggregate_safe` retains that behavior end to end.

`evidence_rich` is a deliberate local diagnostic opt-in/default for the browser Test a model workflow. Prompt/model output may contain secrets, personal data, proprietary text or other sensitive content, so the UI must label retained rich content explicitly. Rich content is not added to fingerprints, canonical Run JSON, portable bundles or aggregate comparison inputs.

Do not add plaintext credentials, raw private endpoint configuration or prompt/output content to fingerprint fields merely because they would make debugging easier. Deleting rich local content must not mutate or fabricate canonical completed evidence; older aggregate-safe runs remain `content_not_retained` permanently.

## How to inspect a bundle manually

```bash
unzip -l .performance-lab/artifacts/<run-id>.plab.zip
unzip -p .performance-lab/artifacts/<run-id>.plab.zip manifest.json | python -m json.tool
unzip -p .performance-lab/artifacts/<run-id>.plab.zip run.json > /tmp/run.json
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

Raw prompt/output sidecars are **not required** for comparison or regression and should be retained only when their diagnostic value justifies the privacy cost.

A green unit-test run is not a substitute for this real evidence set.
