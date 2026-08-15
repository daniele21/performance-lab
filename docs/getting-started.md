# Getting started

Status: active
Document type: operational-guide
Owner: developer experience
Canonical scope: operations.getting-started
Read when: installing Performance Lab, probing an endpoint, or running a first reproducible evaluation
Last reviewed: 2026-08-15

This guide is the shortest supported path from a clean checkout to a persisted evaluation run and a comparable regression workflow.

## 1. Install and validate

Performance Lab requires Python 3.12+.

```bash
python -m pip install -e ".[dev]"
python scripts/validate.py
```

The repository gate runs formatting/linting, strict typing and tests. Passing it proves implementation consistency, not representative model/device performance.

## 2. Verify an inference endpoint

Performance Lab's reference adapter expects an OpenAI-compatible endpoint with at least:

```text
GET  /v1/models
POST /v1/chat/completions
```

Probe it before creating a run:

```bash
performance-lab probe \
  --base-url http://127.0.0.1:1235/v1/ \
  --model my-model
```

For machine-readable automation:

```bash
performance-lab probe \
  --base-url http://127.0.0.1:1235/v1/ \
  --model my-model \
  --json
```

A healthy probe does not imply that every optional capability is supported. Streaming, token usage, seed and structured output remain evidence-based capabilities.

## 3. Create a minimal run config

```json
{
  "schema_version": 1,
  "target_id": "local-model",
  "endpoint_identity": "127.0.0.1:1235",
  "endpoint": {
    "profile_id": "local-endpoint",
    "base_url": "http://127.0.0.1:1235/v1/",
    "model_selector": "my-model"
  },
  "model_id": "my-model"
}
```

Fields omitted here use version-1 defaults, including the local SQLite store and bundled diagnostic suite. Read [`run-config-reference.md`](run-config-reference.md) before relying on defaults for a controlled evidence campaign.

## 4. Run the bundled diagnostic suite

Save the config as `run.json`, then execute:

```bash
performance-lab run --config run.json
```

A successful run prints the status, fingerprint ID, SQLite store path and portable bundle path.

Machine-readable form:

```bash
performance-lab run --config run.json --json
```

returns a compact pointer object such as:

```json
{
  "run_id": "run-...",
  "status": "succeeded",
  "fingerprint_id": "...",
  "store_path": ".performance-lab/runs.sqlite3",
  "bundle_path": ".performance-lab/artifacts/run-....plab.zip",
  "sample_count": 24
}
```

`sample_count` is illustrative: it is the actual number of `SampleExecution` records produced by the frozen suite/tasks and should not be inferred from the number of unique authored source records.

The durable evidence lives in the store/bundle, not in terminal text. See [`output-and-evidence-reference.md`](output-and-evidence-reference.md).

## 5. Use Local LLM Server for richer identity and telemetry

A black-box OpenAI-compatible endpoint is enough for evaluation. Local LLM Server can additionally provide:

```text
GET /v1/runtime/identity   -> frozen execution identity
GET /status                -> sampled dynamic runtime telemetry
```

Example:

```json
{
  "schema_version": 1,
  "target_id": "local-llm-server-my-model",
  "endpoint_identity": "127.0.0.1:1235",
  "endpoint": {
    "profile_id": "local-llm-server",
    "base_url": "http://127.0.0.1:1235/v1/",
    "model_selector": "my-model"
  },
  "model_id": "my-model",
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

The two base URL forms are intentional: OpenAI inference uses `/v1/`; Local LLM Server identity/status configuration uses the server root.

## 6. Inspect a run

`performance-lab inspect` accepts a Run JSON or ExecutionFingerprint JSON. A portable bundle contains `manifest.json` and `run.json`, so one simple workflow is:

```bash
unzip -p .performance-lab/artifacts/<run-id>.plab.zip run.json > /tmp/performance-lab-run.json
performance-lab inspect /tmp/performance-lab-run.json
```

Use `--json` when another tool will consume the output.

## 7. Run a baseline/candidate regression

After two completed runs exist in the same store, create a versioned regression policy and execute:

```bash
performance-lab regress \
  --store .performance-lab/runs.sqlite3 \
  --baseline-run <baseline-run-id> \
  --candidate-run <candidate-run-id> \
  --policy regression-policy.json
```

Performance Lab evaluates fingerprint compatibility before thresholds. A model/runtime change can be the experimental variable; dataset/evaluator/protocol/hardware differences may make particular dimensions non-comparable.

## 8. Gate a change in CI

```bash
performance-lab regress-ci \
  --store .performance-lab/runs.sqlite3 \
  --baseline-run <baseline-run-id> \
  --candidate-run <candidate-run-id> \
  --policy regression-policy.json \
  --artifact performance-lab-regression.json
```

Exit codes distinguish `PASS`, `FAIL`, execution error, `NOT_COMPARABLE` and `NOT_EVALUATED`. See [`cli-reference.md`](cli-reference.md) and [`ci-regression.md`](ci-regression.md).

## 9. Evidence checklist for a real campaign

Retain together:

1. run config;
2. endpoint/server revision and configuration;
3. immutable `ExecutionFingerprint`;
4. `.plab.zip` bundle;
5. relevant identity/telemetry protocol versions;
6. baseline/candidate run IDs;
7. regression policy ID/version;
8. CI JSON artifact when gating a change.

Do not call a model/runtime comparison representative solely because deterministic fixtures and CI are green.

If the workflow fails, use [`troubleshooting.md`](troubleshooting.md).