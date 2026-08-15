# AI Performance Lab

AI Performance Lab is a model- and runtime-agnostic evaluation system for measuring whether an AI model exposed through an inference service is **good enough, fast enough and resource-efficient enough for a specific device and workload**.

The lab does not own model loading or inference runtimes. It connects to an inference endpoint, executes reproducible evaluation suites, captures quality and runtime measurements, optionally correlates them with host/device/runtime telemetry, and stores immutable comparable run evidence.

## Product question

> Can this model/runtime/configuration replace another model for this workload on this device, without unacceptable quality, latency or resource regressions?

## Core principles

- **Inference is external.** The lab evaluates endpoints; it does not embed a model runtime in its core.
- **A model name is not a benchmark identity.** Results belong to a complete execution fingerprint: model, quantization, runtime, generation configuration, endpoint, hardware, dataset snapshot and evaluator version.
- **Quality and runtime performance are separate dimensions.** A single opaque performance score must never hide trade-offs.
- **Black-box first, instrumentation optional.** Any compatible inference endpoint can be evaluated; richer host/runtime measurements are enabled through optional telemetry collectors.
- **Reproducibility before leaderboard aesthetics.** Runs are versioned, immutable and comparable only when their relevant identities are compatible.
- **Workload evaluation matters as much as public benchmarks.** General-purpose suites, workload packs and user-provided datasets share the same execution model.
- **Regression testing is a first-class use case.** The same evidence can be inspected interactively or consumed by deterministic CI gates.

## What can be evaluated

The current executable slice targets text-generation endpoints through the reference OpenAI-compatible adapter. The architecture remains extensible to other transports and later task families such as ASR, embeddings, reranking and vision.

A black-box endpoint only needs the inference contract used by the adapter. Runtime-specific telemetry is optional.

### Minimum inference contract

For the standard executable path, expose:

```text
GET  /v1/models
POST /v1/chat/completions
```

`POST /v1/chat/completions` must accept an OpenAI-style `messages` request and return the selected model's completion. Streaming/token usage/capability details are discovered when available rather than assumed.

### `local-llm-server` integration

`daniele21/local-llm-server` already provides the OpenAI-compatible inference surface above. Performance Lab can additionally collect runtime-native evidence by polling its public root-level endpoint:

```text
GET /status
```

This additional endpoint is **not required for evaluation**. If runtime telemetry is disabled or unavailable, the black-box run remains valid.

The useful selected-model status fields are:

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

`/status` may expose that object directly or, as current `local-llm-server` does, under `models[model_id]` together with `default_model`. `chunks_per_second` is observational runtime evidence and is deliberately **not** relabeled as token throughput.

See [`docs/local-llm-server-integration.md`](docs/local-llm-server-integration.md) for the exact run configuration, selection rules, metrics and limitations.

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
  "local_llm_server_telemetry": {
    "base_url": "http://127.0.0.1:1235",
    "model_id": "my-model",
    "sample_interval_seconds": 0.05,
    "timeout_seconds": 2.0
  }
}
```

Then execute:

```bash
performance-lab run --config local-llm-server-run.json
```

The run is persisted in SQLite and exported as a portable `.plab.zip` evidence bundle. The execution fingerprint records the endpoint/model/generation/dataset/evaluator/hardware/telemetry identity needed for later comparison.

## Current implemented baseline

The repository now includes:

- OpenAI-compatible probe, generation and streaming adapter boundaries;
- versioned execution fingerprints and compatibility rules;
- deterministic local datasets, reusable custom mappings, a general diagnostic suite and a structured-extraction workload pack;
- deterministic evaluators plus optional provenance-rich rubric/LLM judging;
- single-request, repeatability and concurrent-load performance protocols;
- host, generic instrumented and `local-llm-server` runtime telemetry boundaries;
- immutable SQLite evidence, retention policy and portable bundles;
- compatible run comparison, explicit immutable baselines and versioned regression policies;
- executable `run`, `regress` and `regress-ci` flows with machine-readable results and deterministic exit codes;
- a reusable GitHub Actions regression integration;
- constrained CI dependency snapshots validated on Python 3.12 and 3.13.

The core implementation path is no longer the main blocker. The next high-value work is a **representative evidence campaign on real models, runtimes and devices**: preserve real run bundles, repeatability/load evidence, runtime telemetry and CI regression outcomes.

See [`docs/current-state.md`](docs/current-state.md) for the operational ledger.

## Documentation

Documentation uses progressive disclosure: one canonical source owns each kind of truth.

| Question | Canonical source |
| --- | --- |
| What is integrated, blocked or next? | [`docs/current-state.md`](docs/current-state.md) |
| What exactly are we building and what are the acceptance criteria? | [`docs/implementation-plan.md`](docs/implementation-plan.md) |
| Which capability milestones come next? | [`docs/roadmap.md`](docs/roadmap.md) |
| Why did the plan change? | [`docs/plan-changelog.md`](docs/plan-changelog.md) |
| What architecture and boundaries should implementation preserve? | [`docs/architecture.md`](docs/architecture.md) |
| How should benchmarks, datasets and metrics behave? | [`docs/evaluation-and-benchmarking.md`](docs/evaluation-and-benchmarking.md) |
| What telemetry is required and optional? | [`docs/telemetry.md`](docs/telemetry.md) |
| How does `local-llm-server` connect to Performance Lab? | [`docs/local-llm-server-integration.md`](docs/local-llm-server-integration.md) |
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
