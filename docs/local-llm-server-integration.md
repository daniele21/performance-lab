# local-llm-server integration

Status: active
Document type: focused-specification
Owner: runtime integration
Canonical scope: integration.local-llm-server
Read when: connecting Performance Lab to `daniele21/local-llm-server`, preparing a real evidence run, or diagnosing inference/identity/runtime metadata
Last reviewed: 2026-08-15

Performance Lab treats `daniele21/local-llm-server` as an external inference provider. The core does not import or own its runtime. Three independent contracts are available:

```text
/v1/models + /v1/chat/completions   required inference
/v1/runtime/identity                optional frozen execution identity
/status                             optional dynamic runtime telemetry
```

A key rule is that **provider-specific fields are not silently promoted into experiment identity**. Inference, identity and runtime telemetry have separate parsers and measurement boundaries.

## 1. Inference contract — required

Performance Lab's reference adapter expects an OpenAI-compatible API root such as:

```text
http://127.0.0.1:1235/v1/
```

The executable run path uses:

```text
GET  /v1/models
POST /v1/chat/completions
```

The configured `model_id`/`model_selector` must identify a resident model exposed by the serving endpoint.

### `GET /v1/models`

Minimum response:

```json
{
  "data": [
    {"id": "qwen-model"}
  ]
}
```

The OpenAI-compatible parser reads only `data[].id`. Local LLM Server may expose extra fields such as `key`, `created`, `owned_by`, `path`, `backend` and `default`; they do not become canonical identity through this inference adapter.

### Non-streaming chat response

Canonical successful response:

```json
{
  "model": "qwen-model",
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

| Field | Required? | Current use |
| --- | --- | --- |
| top-level JSON object | yes | protocol validation |
| `choices` non-empty array | yes | locate first completion |
| `choices[0].message` object | yes | locate answer |
| `choices[0].message.content` string | **yes** | canonical model output passed to evaluators |
| `model` string | no | normalized response model identifier |
| `choices[0].finish_reason` string | no | completion metadata |
| `usage.prompt_tokens` integer | no | normalized input-token count |
| `usage.completion_tokens` integer | no | normalized output-token count |

If the required `choices/message/content` structure is absent, the adapter raises a typed protocol error rather than guessing another provider-specific response shape.

Local LLM Server may also return `backend`, convenience output aliases, thinking fields and `stats.*`. These are not fallback inference fields and are not substituted for canonical Performance Lab measurements or identity.

### Streaming response

When `stream=true`, Performance Lab sends:

```json
{
  "stream": true,
  "stream_options": {"include_usage": true}
}
```

and expects OpenAI-style SSE `data:` frames:

```text
data: {"model":"qwen-model","choices":[{"delta":{"content":"hel"},"finish_reason":null}]}

data: {"model":"qwen-model","choices":[{"delta":{"content":"lo"},"finish_reason":"stop"}]}

data: {"model":"qwen-model","choices":[],"usage":{"prompt_tokens":3,"completion_tokens":2}}

data: [DONE]
```

The parser consumes text from `choices[0].delta.content`, optional `finish_reason` and optional OpenAI `usage`. Client-side timestamps define the current TTFT boundary.

## 2. Execution identity contract — optional

Local LLM Server is the source of truth for stable identity it can observe about the actual resident runtime. The shared contract is:

```text
GET /v1/runtime/identity
protocol: local-llm-identity-v1
```

Performance Lab validates the document before evaluation and maps known fields into `ExecutionFingerprint`:

```text
model.id                -> model.model_id
model.revision          -> model.revision
model.artifact_digest   -> model.artifact_digest
model.quantization      -> model.quantization
runtime.name            -> runtime.name
runtime.version         -> runtime.version
runtime.config_digest   -> runtime.config_digest
hardware.machine        -> hardware.device_class
hardware.processor      -> hardware.cpu
hardware.accelerator    -> hardware.accelerator
hardware.total_memory_bytes -> hardware.memory_bytes
hardware.system         -> hardware.os
```

Identity is deliberately separate from `/status`: it represents the configuration to freeze at run start, not mutable request counters.

The producer is path-free and may preserve unknown values. Performance Lab does not infer missing revision/hash/quantization/runtime version from filenames, paths or arbitrary provider fields.

See [`local-llm-identity-contract.md`](local-llm-identity-contract.md) for the exact selection, conflict and compatibility semantics.

## 3. Runtime telemetry contract — optional

During a run, Performance Lab can poll the Local LLM Server root:

```text
GET /status
```

Current Local LLM Server returns a top-level `default_model` plus a `models` map. Performance Lab selects the configured telemetry `model_id`, otherwise `default_model`, otherwise the only model if exactly one is present.

Representative status:

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

The `local-llm-server-status-v1` collector consumes:

| Field | Measurement use |
| --- | --- |
| `active_requests` | peak active requests, active ratio |
| `max_concurrent_requests` | reported runtime concurrency |
| `phase` | active/generating/prompt-eval sample ratios |
| `output_chunks` | peak observed output chunks |
| `output_characters` | peak observed output characters |
| `chunks_per_second` | peak observed chunks/s |

`chunks_per_second` is deliberately **not** renamed to `tokens_per_second`; their boundaries differ. Token throughput remains owned by inference/performance protocols when token usage is observable.

## Run configuration

A fully instrumented Local LLM Server run can enable identity, host telemetry and runtime telemetry together:

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
  "local_llm_server_identity": {
    "base_url": "http://127.0.0.1:1235",
    "model_id": "qwen-model",
    "timeout_seconds": 2.0,
    "required": true
  },
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

The base URLs are intentionally different:

```text
endpoint.base_url                   -> http://127.0.0.1:1235/v1/
identity/telemetry server base_url  -> http://127.0.0.1:1235
```

If `local_llm_server_identity` is omitted but `local_llm_server_telemetry` is configured, the runner makes a best-effort identity request to the same server root before the fingerprint is frozen. Failure remains non-fatal for backward compatibility. Use explicit `local_llm_server_identity.required: true` when an evidence campaign must not proceed with incomplete first-party identity.

## Hardware conflict rule

Configured hardware may fill fields Local LLM Server does not know. When both sources know a field and values conflict, Performance Lab fails before evaluation rather than silently choosing one source.

This matters because hardware participates in comparability and resource regression semantics.

## What Performance Lab owns

Local LLM Server does not need to know about datasets, benchmark tasks, evaluators, baselines or regression policies. Performance Lab owns:

- evaluation suite and dataset snapshot;
- prompts/messages derived from each sample;
- generation configuration;
- request count/concurrency/load profile;
- telemetry sampling interval;
- model selection;
- fingerprint assembly/comparability semantics;
- evidence persistence and regression policy.

Local LLM Server only serves inference and optionally exposes its own stable identity and dynamic runtime state.

## Telemetry measurements

Protocol: `local-llm-server-status-v1`

Current measurements include:

- status sample count and sampling errors;
- observed sampling window duration;
- peak active requests;
- active/generating/prompt-eval sample ratios;
- peak observed chunks per second;
- peak per-request output chunks and characters visible in sampled status;
- maximum concurrent requests reported by the runtime.

All use `MeasurementProvenance.RUNTIME`.

`use_host_telemetry: true` may be combined with runtime polling. The resulting fingerprint records the collector identities under telemetry level `instrumented`.

## Evidence limitations

`/v1/runtime/identity` reports what the server explicitly knows. Partial identity remains partial: a missing artifact digest or backend version is not fabricated.

`/status` polling is observational. Short phases can occur between samples, so phase ratios and peaks are sampling-dependent. Compare them only under the same collector protocol and sampling configuration.

A representative evidence campaign should preserve together:

1. the run config;
2. execution fingerprint;
3. `.plab.zip` bundle;
4. the identity document or equivalent captured identity evidence;
5. relevant runtime telemetry;
6. Local LLM Server version/configuration.

Passing deterministic fake-server integration tests proves the contract implementation. A real resident-model/device run is still required for representative product evidence.
