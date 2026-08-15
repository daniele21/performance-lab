# local-llm-server integration

Status: active
Document type: focused-specification
Owner: runtime integration
Canonical scope: integration.local-llm-server
Read when: connecting Performance Lab to `daniele21/local-llm-server`, preparing a real evidence run, or diagnosing missing runtime telemetry
Last reviewed: 2026-08-15

Performance Lab treats `daniele21/local-llm-server` as an external inference provider. The core does not import or own its runtime. Evaluation uses the normal OpenAI-compatible API; optional runtime-native evidence is collected by polling the server's existing public `/status` endpoint during the same run.

## Required input from `local-llm-server`

There are two independent contracts.

### 1. Inference contract — required to evaluate the model

Performance Lab's reference adapter expects an OpenAI-compatible API root such as:

```text
http://127.0.0.1:1235/v1/
```

The executable run path uses:

```text
GET  /v1/models
POST /v1/chat/completions
```

The configured `model_id`/`model_selector` must identify a resident model exposed by the serving endpoint. `POST /v1/chat/completions` must accept OpenAI-style `messages` input and return a completion for that model. Streaming, token usage and optional generation capabilities are probed/normalized when available rather than treated as mandatory server features.

This is enough for black-box quality and runtime evaluation. No `local-llm-server`-specific telemetry is required.

### 2. Runtime telemetry contract — optional

To attach first-party runtime evidence, Performance Lab additionally polls the server root:

```text
GET /status
```

Current `local-llm-server` returns a top-level `default_model` plus a `models` map. Performance Lab selects the configured telemetry `model_id`, otherwise `default_model`, otherwise the only model if exactly one is present.

A representative payload is:

```json
{
  "default_model": "qwen-model",
  "models": {
    "qwen-model": {
      "active_requests": 1,
      "max_concurrent_requests": 1,
      "phase": "generating",
      "output_chunks": 12,
      "output_characters": 640,
      "chunks_per_second": 18.4
    }
  }
}
```

For useful v1 runtime evidence, the selected model status should expose:

| Field | Meaning | Current measurement use |
| --- | --- | --- |
| `active_requests` | requests currently owned by the runtime | peak active requests, active ratio |
| `max_concurrent_requests` | configured admission/concurrency limit | reported runtime concurrency |
| `phase` | current runtime phase, e.g. `idle`, `prompt_eval`, `generating` | phase sample ratios |
| `output_chunks` | output chunks observed for the active request | peak observed output chunks |
| `output_characters` | output characters observed for the active request | peak observed output characters |
| `chunks_per_second` | sampled chunk emission rate when available | peak observed chunks/s |

`chunks_per_second` is deliberately **not** renamed to `tokens_per_second`. They have different measurement boundaries. Token throughput remains owned by the inference/performance protocol when token usage is actually available.

## Why polling instead of server modification

The serving project already exposes the runtime state needed for useful first-party evidence. Polling keeps the serving runtime independent from Performance Lab and avoids adding an evaluation-specific dependency to `local-llm-server`.

The integration can later move to stronger server-side counters only if representative evidence demonstrates that polling is insufficient for a concrete decision.

## Run configuration

Add `local_llm_server_telemetry` to the normal version-1 run config:

```json
{
  "schema_version": 1,
  "target_id": "local-llm-server-qwen",
  "endpoint_identity": "127.0.0.1:1235",
  "endpoint": {
    "profile_id": "local-llm-server",
    "base_url": "http://127.0.0.1:1235/v1/",
    "model_selector": "qwen-model"
  },
  "model_id": "qwen-model",
  "store_path": ".performance-lab/runs.sqlite3",
  "use_host_telemetry": true,
  "local_llm_server_telemetry": {
    "base_url": "http://127.0.0.1:1235",
    "model_id": "qwen-model",
    "sample_interval_seconds": 0.05,
    "timeout_seconds": 2.0
  }
}
```

Then run:

```bash
performance-lab run --config local-llm-server-run.json
```

The two base URLs are intentionally different:

```text
endpoint.base_url                       -> http://127.0.0.1:1235/v1/
local_llm_server_telemetry.base_url     -> http://127.0.0.1:1235
```

The inference adapter operates inside the OpenAI namespace; the runtime collector needs the server root because `/status` is outside `/v1`.

## What Performance Lab supplies

`local-llm-server` does not need to know about datasets, benchmark tasks, evaluators, baselines or regression policies. Performance Lab owns those inputs and drives inference requests through the exposed model API.

For one run, Performance Lab supplies/controls:

- evaluation suite and dataset snapshot;
- prompts/messages derived from each task sample;
- generation configuration;
- request count/concurrency/load profile;
- telemetry sampling interval;
- explicit model selection;
- execution fingerprint and evidence storage.

`local-llm-server` only needs to serve the requested model and expose the contracts above.

## Runtime measurements

Protocol: `local-llm-server-status-v1`

Current measurements include:

- status sample count and sampling errors;
- observed sampling window duration;
- peak active requests;
- active/generating/prompt-eval sample ratios;
- peak observed chunks per second;
- peak per-request output chunks and characters visible in sampled status;
- maximum concurrent requests reported by the runtime.

All measurements use `MeasurementProvenance.RUNTIME`.

If runtime telemetry is unavailable or fails, `TelemetrySession` isolates that collector from the evaluation path. Black-box model evaluation remains independently valid.

## Combined host + runtime evidence

`use_host_telemetry: true` may be combined with `local_llm_server_telemetry`. The resulting execution fingerprint records both collector identities under telemetry level `instrumented` and uses the stable combined protocol identifier `telemetry-session-v1`.

This keeps host/process evidence distinct from serving-runtime evidence while allowing the same run to carry both.

## Evidence limitations

Polling is observational. Short phases can occur between samples, so phase ratios and peaks are sampling-dependent. Compare them only under the same collector protocol and sampling configuration.

The first real evidence campaign should preserve together:

1. the run config;
2. execution fingerprint;
3. `.plab.zip` bundle;
4. model/runtime/hardware identity;
5. relevant `local-llm-server` version/configuration.

This distinction is important: passing the offline integration fixture proves the contract implementation, while a run against an actual resident local model provides the representative product evidence needed for milestone closure.
