# local-llm-server integration

Status: active
Document type: focused-specification
Owner: runtime integration
Canonical scope: integration.local-llm-server
Read when: connecting Performance Lab to `daniele21/local-llm-server`, preparing a real evidence run, or diagnosing inference/identity/runtime metadata
Last reviewed: 2026-08-15

Performance Lab treats `daniele21/local-llm-server` as an external inference provider. The core does not import or own its runtime. Evaluation uses the normal OpenAI-compatible API; optional runtime-native evidence is collected by polling the server's existing public `/status` endpoint during the same run.

A key rule is that **provider-specific fields are not silently promoted into experiment identity**. The sections below distinguish the exact wire fields Performance Lab consumes today, extra fields that `local-llm-server` already emits, and identity fields that remain unknown until an explicit contract binds them.

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

The configured `model_id`/`model_selector` must identify a resident model exposed by the serving endpoint. `POST /v1/chat/completions` must accept OpenAI-style `messages` input and return a completion for that model.

#### `GET /v1/models` response

The minimum response consumed by the current adapter is:

```json
{
  "data": [
    {"id": "qwen-model"}
  ]
}
```

The current parser reads only `data[].id` to discover model IDs. `local-llm-server` currently also returns fields such as `key`, `created`, `owned_by`, `path`, `backend` and `default`; these are useful provider metadata but are **not currently consumed by the OpenAI-compatible adapter**.

This distinction matters for reproducibility: `backend` or a model path appearing in `/v1/models` does not automatically become part of `ExecutionFingerprint` until Performance Lab explicitly defines that mapping.

#### Non-streaming `POST /v1/chat/completions` response

A canonical successful response is:

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

Current consumption is exact:

| Field | Required? | Current use |
| --- | --- | --- |
| top-level JSON object | yes | protocol validation |
| `choices` non-empty array | yes | locate the first completion |
| `choices[0].message` object | yes | locate the answer |
| `choices[0].message.content` string | **yes** | canonical model output passed to evaluators |
| `model` string | no | normalized response model identifier |
| `choices[0].finish_reason` string | no | completion metadata |
| `usage.prompt_tokens` integer | no | normalized input-token count |
| `usage.completion_tokens` integer | no | normalized output-token count |

If the required `choices/message/content` structure is absent, the adapter raises a typed protocol error rather than guessing another provider-specific response shape.

`local-llm-server` currently enriches the response with additional convenience fields such as:

```text
backend
output
response
content
raw_output
thinking
final_answer
stats.input_tokens
stats.output_tokens
stats.total_tokens
stats.tokens_per_second
stats.time_total_seconds
```

Those fields are **not part of the current Performance Lab inference wire contract**. In particular:

- `backend` is not currently promoted to `ExecutionFingerprint.runtime`;
- `stats.tokens_per_second` is not substituted for Performance Lab's own performance measurement boundary;
- `stats.input_tokens` / `stats.output_tokens` do not replace OpenAI `usage.prompt_tokens` / `usage.completion_tokens` in the current adapter;
- `output`, `response`, `content` and `final_answer` are not fallback answer fields; `choices[0].message.content` remains canonical.

This keeps the adapter deterministic and prevents provider-specific response enrichments from silently changing benchmark semantics.

#### Streaming `POST /v1/chat/completions` response

When `stream=true`, Performance Lab sends:

```json
{
  "stream": true,
  "stream_options": {"include_usage": true}
}
```

and expects Server-Sent Events using `data:` frames. A representative stream is:

```text
data: {"model":"qwen-model","choices":[{"delta":{"content":"hel"},"finish_reason":null}]}

data: {"model":"qwen-model","choices":[{"delta":{"content":"lo"},"finish_reason":"stop"}]}

data: {"model":"qwen-model","choices":[],"usage":{"prompt_tokens":3,"completion_tokens":2}}

data: [DONE]
```

The parser currently consumes:

| Stream field | Required? | Current use |
| --- | --- | --- |
| SSE line beginning with `data:` | yes for parsed events | event framing |
| JSON object after `data:` | yes for non-`[DONE]` frames | protocol validation |
| `choices[0].delta.content` string | optional per frame | text delta |
| `choices[0].finish_reason` string | optional | completion metadata |
| `usage.prompt_tokens` integer | optional | observed input tokens |
| `usage.completion_tokens` integer | optional | observed output tokens |
| `data: [DONE]` | supported terminator | ignored as a content event |

The client timestamps each parsed chunk at the Performance Lab boundary. The server therefore does not need to provide a TTFT timestamp for the current black-box performance protocol.

Streaming, token usage, seed support and structured-output support are capability evidence: absence of a field is not automatically interpreted as unsupported unless an explicit active check proves it.

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
      "model": "qwen-model",
      "backend": "llama_cpp",
      "loaded_at": 1786800000.0,
      "state": "ready",
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

The current `local-llm-server-status-v1` collector consumes only the measurement fields below:

| Field | Current status | Current measurement use |
| --- | --- | --- |
| `active_requests` | consumed | peak active requests, active ratio |
| `max_concurrent_requests` | consumed | reported runtime concurrency |
| `phase` | consumed | active/generating/prompt-eval sample ratios |
| `output_chunks` | consumed | peak observed output chunks |
| `output_characters` | consumed | peak observed output characters |
| `chunks_per_second` | consumed | peak observed chunks/s |
| `model` | exposed by server, not yet bound | candidate model identity evidence |
| `backend` | exposed by server, not yet bound | candidate runtime identity evidence |
| `loaded_at` | exposed by server, not yet bound | candidate runtime-instance evidence |
| `state` | exposed by server, not yet bound | candidate runtime lifecycle evidence |
| `tokens_generated` / `tokens_per_second` | provider compatibility fields, not consumed | deliberately not used as canonical token evidence |

`chunks_per_second` is deliberately **not** renamed to `tokens_per_second`. They have different measurement boundaries. Token throughput remains owned by the inference/performance protocol when token usage is actually observable.

## Identity metadata: what is automatic today

`ExecutionFingerprint` can represent richer identity than the current `local-llm-server` adapter automatically discovers:

```text
model.model_id
model.revision
model.artifact_digest
model.quantization
runtime.name
runtime.version
hardware.device_id
hardware.device_class
hardware.cpu
hardware.accelerator
hardware.memory_bytes
hardware.os
```

For the current executable starter run, provenance is:

| Fingerprint field | Current source for `local-llm-server` runs |
| --- | --- |
| `model.model_id` | explicit run config (`model_id`) |
| `model.revision` | unknown unless a future explicit identity mapping supplies it |
| `model.artifact_digest` | unknown unless a future explicit identity mapping supplies it |
| `model.quantization` | unknown unless a future explicit identity mapping supplies it |
| `runtime.name` | currently unknown in the starter-run wiring |
| `runtime.version` | currently unknown in the starter-run wiring |
| hardware fields | explicit run config `hardware`; never guessed from response text |
| generation config | frozen suite/run configuration |
| datasets/evaluators/protocol/load | Performance Lab-owned frozen configuration |
| telemetry protocol/collectors | Performance Lab collector configuration |

Performance Lab also has a generic `runtime-telemetry-v1` instrumented endpoint contract capable of returning explicit `runtime`, `model` and `hardware` identity. That generic handshake is separate from the current `local-llm-server` `/status` polling integration and is **not silently assumed to exist** on the server.

This is an intentional honesty boundary: until a mapping is explicit, a useful-looking `backend`, model filename or path is not guessed into canonical identity.

## Why polling instead of server modification

The serving project already exposes runtime state useful for first-party operational evidence. Polling keeps the serving runtime independent from Performance Lab and avoids adding an evaluation-specific dependency to `local-llm-server`.

The integration can later promote stable server metadata into a versioned identity contract only when that mapping is defined and tested. A likely future extension would bind model revision/digest/quantization and runtime name/version without changing the black-box OpenAI contract.

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
- explicit hardware identity when the caller knows it;
- execution fingerprint and evidence storage.

`local-llm-server` only needs to serve the requested model and expose the contracts above. Extra fields are safe to return, but they do not become canonical evidence until the adapter explicitly owns their semantics.

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
4. model/runtime/hardware identity that was explicitly observed or supplied;
5. relevant `local-llm-server` version/configuration.

This distinction is important: passing the offline integration fixture proves the wire-contract implementation, while a run against an actual resident local model provides the representative product evidence needed for milestone closure.
