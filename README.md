# AI Performance Lab

AI Performance Lab is a model- and runtime-agnostic evaluation system for answering one practical deployment question:

> **For my use case, which of the models available to me is the best fit for this device, and with which configuration?**

Rather than ranking models in the abstract, Performance Lab evaluates **model × configuration × device** combinations against the requirements of a specific use case.

The use case determines what matters. Performance Lab maps it to relevant capabilities, benchmarks and evaluation datasets, runs candidate combinations through an external inference service, measures quality, runtime and resource behavior, and stores reproducible evidence that supports a deployment decision.

The lab does not own model loading or inference runtimes. It connects to inference endpoints, executes reproducible evaluation suites, captures measurements, optionally correlates them with host/device/runtime telemetry, and compares resulting evidence across compatible runs.

## Product question

> **Given my target use case, target device and available models/configurations, which combination gives me the best evidence-backed trade-off for what I actually need?**

The goal is not another generic LLM leaderboard. The goal is to turn use-case-relevant benchmark and runtime evidence into a practical deployment decision, with the trade-offs visible rather than hidden in a universal score.

## How it works

**Use case → required capabilities → relevant benchmarks/datasets → candidate model/configuration runs → quality + runtime + resource comparison → evidence-backed decision**

For example, document summarization may emphasize factual consistency, instruction following and long-context behavior, while structured extraction may emphasize field accuracy, schema adherence and hallucination resistance. User-provided datasets can represent the real workload when generic benchmarks are insufficient.

## Core principles

- **Use case first.** Benchmarks and datasets are selected because they are relevant to the workload objective, not because they are popular in isolation.
- **Inference is external.** The lab evaluates endpoints; it does not embed a model runtime in its core.
- **A model name is not a benchmark identity.** Results belong to a complete execution fingerprint: model, quantization, runtime, effective serving configuration, generation configuration, endpoint, hardware, dataset snapshot and evaluator version.
- **Quality, runtime and resources are separate evidence dimensions.** A single opaque score must never hide trade-offs.
- **Black-box first, instrumentation optional.** Any compatible inference endpoint can be evaluated; richer host/runtime measurements and first-party identity are optional integrations.
- **Reproducibility before leaderboard aesthetics.** Runs are versioned, immutable and comparable only when their relevant identities are compatible.
- **Use-case-aligned evaluation matters more than generic ranking.** General-purpose suites, workload packs and user-provided datasets share the same execution model.
- **Recommendations stay evidence-backed.** A preferred model/configuration must expose the evidence and constraints behind the decision rather than becoming an unexplained winner.
- **Regression testing is a first-class secondary use case.** The same evidence supports replacement validation, regression analysis and deterministic CI gates.

## What can be evaluated

The current executable slice targets text-generation endpoints through the reference OpenAI-compatible adapter. The architecture remains extensible to other transports and later task families such as ASR, embeddings, reranking and vision.

A black-box endpoint only needs the inference contract used by the adapter. Runtime-specific telemetry and first-party identity discovery are optional.

### Minimum inference contract

For the standard executable path, expose:

```text
GET  /v1/models
POST /v1/chat/completions
```

`POST /v1/chat/completions` must accept an OpenAI-style `messages` request and return the selected model's completion. Streaming/token usage/capability details are discovered when available rather than assumed.

The minimum model-list response consumed by Performance Lab is:

```json
{
  "data": [
    {"id": "my-model"}
  ]
}
```

For a non-streaming chat completion, the only response field required to score the model output is `choices[0].message.content` as text:

```json
{
  "model": "my-model",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "The model answer"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 42,
    "completion_tokens": 17
  }
}
```

Current consumption rules are deliberately narrow:

| Response field | Status | Performance Lab use |
| --- | --- | --- |
| `choices[0].message.content` | **required** | model output passed to evaluators |
| `model` | optional | normalized response model identifier |
| `choices[0].finish_reason` | optional | normalized completion metadata |
| `usage.prompt_tokens` | optional | observed input-token count |
| `usage.completion_tokens` | optional | observed output-token count / token-based performance evidence |
| provider-specific extra fields | ignored unless explicitly adapted | never guessed into the fingerprint |

For streaming, the adapter requests `stream_options.include_usage=true` and consumes Server-Sent Events with OpenAI-style `data:` frames. Text arrives through `choices[0].delta.content`; `finish_reason` and `usage` may arrive in later frames, followed by `data: [DONE]`.

A compact example is:

```text
data: {"choices":[{"delta":{"content":"hel"},"finish_reason":null}]}

data: {"choices":[{"delta":{"content":"lo"},"finish_reason":"stop"}]}

data: {"choices":[],"usage":{"prompt_tokens":3,"completion_tokens":2}}

data: [DONE]
```

These are **wire-response fields**, not the complete experiment identity. Quantization, artifact revision/digest, runtime name/version/configuration and hardware are not inferred from arbitrary response metadata. If they are not supplied through an explicit identity/configuration contract, they remain `unknown` in the execution fingerprint.

### `local-llm-server` integration

`daniele21/local-llm-server` provides the OpenAI-compatible inference surface above and two optional first-party evidence surfaces with deliberately different responsibilities:

```text
GET /v1/runtime/identity   # stable execution identity, frozen before the run
GET /status                # dynamic runtime telemetry sampled during the run
```

Neither endpoint is required for generic black-box evaluation.

#### Execution identity

The shared versioned producer/consumer contract is `local-llm-identity-v1`. Performance Lab strictly validates the identity document and can map:

- model ID, revision, artifact digest and quantization;
- backend/runtime name and version;
- effective serving-configuration digest;
- non-sensitive machine/CPU/accelerator/memory/OS identity.

These fields are frozen into `ExecutionFingerprint` before evaluation begins. Performance Lab does not infer quantization from filenames or reinterpret arbitrary Local LLM Server response fields.

Identity can be requested explicitly and made mandatory for evidence-grade campaigns:

```json
{
  "local_llm_server_identity": {
    "base_url": "http://127.0.0.1:1235",
    "model_id": "my-model",
    "timeout_seconds": 2.0,
    "required": true
  }
}
```

When `local_llm_server_telemetry` is configured and the explicit identity block is omitted, the runner also attempts identity discovery from the same server root on a best-effort basis. This keeps older Local LLM Server versions usable: failure to discover optional identity falls back to the normal honest unknown-field behavior.

If explicit run-config hardware and first-party server hardware both provide the same field but disagree, the run is rejected before the fingerprint is frozen.

See [`docs/local-llm-identity-contract.md`](docs/local-llm-identity-contract.md) for the exact mapping, selection rules, compatibility behavior and acceptance contract.

#### Runtime telemetry

Performance Lab can collect runtime-native evidence by polling:

```text
GET /status
```

The useful selected-model status fields currently consumed are:

```json
{
  "active_requests": 1,
  "max_concurrent_requests": 1,
  "phase": "generating",
  "output_chunks": 12,
  "output_characters": 640,
  "chunks_per_second": 18.4
}
```

`/status` may expose that object directly or under `models[model_id]` together with `default_model`. `chunks_per_second` is observational runtime evidence and is deliberately **not** relabeled as token throughput.

See [`docs/local-llm-server-integration.md`](docs/local-llm-server-integration.md) for the complete inference/telemetry setup and limitations.

## Quick start

Requires Python 3.12+.

```bash
python -m pip install -e ".[dev]"
python scripts/validate.py
```

Create a run config, for example for `local-llm-server` running on port `1235`:

```json
{
  "schema_version": 1,
  "target_id": "local-llm-server-local-model",
  "endpoint_identity": "127.0.0.1:1235",
  "endpoint": {
    "profile_id": "local-llm-server",
    "base_url": "http://127.0.0.1:1235/v1/",
    "model_selector": "my-model"
  },
  "model_id": "my-model",
  "store_path": ".performance-lab/runs.sqlite3",
  "use_host_telemetry": true,
  "local_llm_server_identity": {
    "base_url": "http://127.0.0.1:1235",
    "model_id": "my-model",
    "timeout_seconds": 2.0,
    "required": true
  },
  "local_llm_server_telemetry": {
    "base_url": "http://127.0.0.1:1235",
    "model_id": "my-model",
    "sample_interval_seconds": 0.05,
    "timeout_seconds": 2.0
  }
}
```

Then execute one controlled run:

```bash
performance-lab run --config local-llm-server-run.json
```

The run is persisted in SQLite and exported as a portable `.plab.zip` evidence bundle. The execution fingerprint records the endpoint/model/runtime-config/generation/dataset/evaluator/hardware/telemetry identity actually known at run start. Unobserved fields remain unknown rather than being guessed.

### Run the local browser product

From a repository checkout, build the frontend and serve it together with the loopback API:

```bash
npm --prefix frontend ci
npm --prefix frontend run build
performance-lab-ui --config local-llm-server-run.json --assets frontend/dist
```

Then open the loopback address printed by `performance-lab-ui`. The primary **Find best setup** journey is executable: choose a versioned use case, select candidate models on one target/device, review the backend-owned benchmark plan and frozen digest, start the campaign, follow reconnectable progress, and inspect results backed by immutable Runs.

Campaign execution revalidates the exact frozen plan on the server before launch. Candidate identity remains explicit, including `unknown` quantization/runtime fields when the connected runtime cannot report them. Parameter sweeps stay unavailable unless the runtime contract supplies bounded ranges.

Results show compatibility and the explicit versioned decision policy before any recommendation. The current `strict-quality-dominance@1.0.0` policy only recommends a unique candidate when comparable quality evidence shows it is no worse on every reported quality metric and strictly better on at least one metric against every alternative; it does not create a universal weighted score. Campaign Results also expose retained benchmark case identities: opening a case compares that exact `(task_id, sample_id)` across candidate Runs, preserves each model/quantization/configuration/Run/sample-attempt identity, and keeps unavailable or non-comparable evidence explicit rather than inferring a case-level winner.

## Current implemented baseline

The repository now includes:

- OpenAI-compatible probe, generation and streaming adapter boundaries;
- versioned execution fingerprints and compatibility rules, including optional effective runtime-config identity;
- deterministic local datasets, reusable custom mappings, a general diagnostic suite and a structured-extraction workload pack;
- deterministic evaluators plus optional provenance-rich rubric/LLM judging;
- single-request, repeatability and concurrent-load performance protocols;
- host, generic instrumented and `local-llm-server` runtime telemetry boundaries;
- strict `local-llm-identity-v1` consumption for first-party model/runtime/hardware identity;
- immutable SQLite evidence, retention policy and portable bundles;
- compatible run comparison, explicit immutable baselines and versioned regression policies;
- executable `run`, `regress` and `regress-ci` flows with machine-readable results and deterministic exit codes;
- a reusable GitHub Actions regression integration;
- a local browser product with Overview, executable Find best setup planning/campaign/results, Case Comparison Across Candidates, Test a model, Live Run, Runs/Run Detail, Compare, Library and Settings;
- server-owned Campaign lifecycle with frozen-plan revalidation, bounded execution, cancellation/recovery, immutable Run grouping and compatibility-aware policy-backed results;
- benchmark, sample and same-case cross-candidate evidence drill-down with explicit content-retention, evaluator-explanation and non-comparability states;
- browser acceptance for J0-J9 where the corresponding journey is executable, with packaged-product evidence for J0, J1, J8 and J9;
- unique build/source identity, immutable packaged artifacts, manifest/checksums, build delta, bounded retention and built-product smoke/cleanup;
- constrained CI dependency snapshots validated on Python 3.12 and 3.13.

The next product UX/UI capability is **UXUI-09 product hardening** across the now-complete J0-J9 journey surface. Representative real-model/runtime/device evidence remains a separate required track before making hardware-specific deployment claims.

See [`docs/current-state.md`](docs/current-state.md) for the operational ledger and [`docs/features/same-case-candidate-comparison.md`](docs/features/same-case-candidate-comparison.md) for the same-case comparison contract.

## Documentation

Documentation uses progressive disclosure: one canonical source owns each kind of truth.

| Question | Canonical source |
| --- | --- |
| What is integrated, blocked or next? | [`docs/current-state.md`](docs/current-state.md) |
| Which active coordinated workstreams and gates remain? | [`docs/workstreams/README.md`](docs/workstreams/README.md) |
| Which capability milestones come next? | [`docs/roadmap.md`](docs/roadmap.md) |
| What architecture and ownership boundaries should implementation preserve? | [`docs/architecture.md`](docs/architecture.md) |
| How should benchmarks, datasets and metrics behave? | [`docs/evaluation-and-benchmarking.md`](docs/evaluation-and-benchmarking.md) |
| What telemetry is required and optional? | [`docs/telemetry.md`](docs/telemetry.md) |
| How does `local-llm-server` connect to Performance Lab? | [`docs/local-llm-server-integration.md`](docs/local-llm-server-integration.md) |
| How is Local LLM Server identity mapped into `ExecutionFingerprint`? | [`docs/local-llm-identity-contract.md`](docs/local-llm-identity-contract.md) |
| What is required before a task, milestone or release is considered done? | [`docs/definition-of-done.md`](docs/definition-of-done.md) |
| Where is all active documentation indexed? | [`docs/README.md`](docs/README.md) |

## Validation

The shared local/CI repository gate runs:

```text
ruff format --check
ruff check
mypy --strict
pytest
```

CI validates the supported Python matrix using a committed dependency-constraint snapshot to reduce resolver drift. Passing repository tests is implementation evidence; it is not a substitute for representative model/device benchmark evidence.

## License

MIT. See [`LICENSE`](LICENSE).
