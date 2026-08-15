# Run configuration reference

Status: active
Document type: operational-reference
Owner: executable run path
Canonical scope: operations.run-config
Read when: creating or reviewing a `performance-lab run --config` JSON file
Last reviewed: 2026-08-15

The executable starter run uses a strict versioned JSON configuration. Unknown fields are rejected rather than silently ignored.

## Top-level schema

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

## Top-level fields

| Field | Type | Required | Default | Meaning |
| --- | --- | --- | --- | --- |
| `schema_version` | integer literal | yes | — | currently must be `1` |
| `target_id` | non-empty string | yes | — | logical target identity for the evaluation |
| `endpoint_identity` | non-empty string | yes | — | persistence-safe endpoint identity; do not put secrets here |
| `endpoint` | object | yes | — | transport/connection profile |
| `model_id` | non-empty string | yes | — | canonical configured model identity used by the starter run |
| `store_path` | path | no | `.performance-lab/runs.sqlite3` | local SQLite evidence store |
| `run_id` | non-empty string or null | no | generated | explicit run ID when deterministic naming is desired |
| `use_host_telemetry` | boolean | no | `false` | enable portable host/process telemetry collector |
| `local_llm_server_telemetry` | object or null | no | `null` | poll Local LLM Server `/status` during the run |
| `local_llm_server_identity` | object or null | no | `null` | discover/freeze `local-llm-identity-v1` before execution |
| `hardware` | object | no | all fields unknown | caller-supplied hardware identity when explicitly known |
| `suite_id` | literal string | no | `general-diagnostic-starter` | bundled executable suite; current starter path accepts only this value |

## `endpoint`

The endpoint object uses the versioned `EndpointProfile` contract.

| Field | Type | Required | Default | Meaning |
| --- | --- | --- | --- | --- |
| `schema_version` | integer literal | no | `1` | endpoint profile schema |
| `profile_id` | non-empty string | yes | — | human/persistence-safe profile ID |
| `base_url` | HTTP URL | yes | — | adapter base URL, normally ending in `/v1/` for OpenAI-compatible servers |
| `auth` | object | no | no auth | credential indirection; raw credentials are not representable |
| `model_selector` | non-empty string or null | no | `null` | model used by adapter discovery/generation when appropriate |
| `timeout_seconds` | float | no | `120` | endpoint operation timeout; must be >0 and <=3600 |

### Authentication

Credentials are referenced only by environment-variable name.

No authentication:

```json
{
  "strategy": "none"
}
```

Bearer token from an environment variable:

```json
{
  "strategy": "bearer_env",
  "credential_env": "MY_ENDPOINT_TOKEN"
}
```

API key from an environment variable:

```json
{
  "strategy": "api_key_env",
  "credential_env": "MY_ENDPOINT_API_KEY"
}
```

A custom header strategy also requires `header_name`. Raw secret values must not be embedded in the run config or exported evidence.

## `local_llm_server_identity`

```json
{
  "base_url": "http://127.0.0.1:1235",
  "model_id": "my-model",
  "timeout_seconds": 2.0,
  "required": true
}
```

| Field | Type | Required | Default | Meaning |
| --- | --- | --- | --- | --- |
| `base_url` | HTTP URL | yes | — | Local LLM Server root, not `/v1/` |
| `model_id` | non-empty string or null | no | `null` | runtime/model selection hint |
| `timeout_seconds` | float | no | `2.0` | identity request timeout; >0 and <=120 |
| `required` | boolean | no | `false` | if true, discovery/validation failure aborts before fingerprint freeze |

Selection follows the versioned identity-contract rules. Local LLM Server identity can populate model revision/digest/quantization, runtime name/version/config digest and bounded hardware fields.

When the identity block is absent but Local LLM Server telemetry is configured, the runner attempts best-effort identity discovery from the same server root. Failure remains non-fatal in that implicit compatibility mode.

## `local_llm_server_telemetry`

```json
{
  "base_url": "http://127.0.0.1:1235",
  "model_id": "my-model",
  "sample_interval_seconds": 0.05,
  "timeout_seconds": 2.0
}
```

| Field | Type | Required | Default | Meaning |
| --- | --- | --- | --- | --- |
| `base_url` | HTTP URL | yes | — | Local LLM Server root containing `/status` |
| `model_id` | non-empty string or null | no | `null` | selected runtime for status sampling |
| `sample_interval_seconds` | float | no | `0.05` | client polling interval; >0 and <=60 |
| `timeout_seconds` | float | no | `2.0` | per-poll timeout; >0 and <=120 |

Telemetry is observational. Short phases may occur between polls; compare sampled metrics only under compatible collector protocols/configuration.

## `hardware`

```json
{
  "device_id": null,
  "device_class": "MacBookPro18,3",
  "cpu": "Apple M1 Pro",
  "accelerator": "Apple GPU",
  "memory_bytes": 17179869184,
  "os": "macOS"
}
```

All fields are optional. `memory_bytes`, when supplied, must be >0.

Do not guess hardware from endpoint names. When Local LLM Server first-party identity supplies a field and explicit run config supplies the same field, conflicting values fail the run rather than silently choosing one source.

## Complete Local LLM Server example

```json
{
  "schema_version": 1,
  "target_id": "local-llm-server-qwen",
  "endpoint_identity": "127.0.0.1:1235",
  "endpoint": {
    "profile_id": "local-llm-server",
    "base_url": "http://127.0.0.1:1235/v1/",
    "model_selector": "qwen-model",
    "timeout_seconds": 120
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
  },
  "suite_id": "general-diagnostic-starter"
}
```

## Why there are two base URLs

```text
endpoint.base_url                   -> http://127.0.0.1:1235/v1/
local_llm_server_identity.base_url  -> http://127.0.0.1:1235
local_llm_server_telemetry.base_url -> http://127.0.0.1:1235
```

The first belongs to the OpenAI-compatible transport. The other two are Local LLM Server integration roots used to reach `/v1/runtime/identity` and `/status` respectively.

## Validation behavior

The loader rejects:

- invalid JSON;
- non-object top-level JSON;
- unsupported/missing `schema_version`;
- empty required strings;
- unknown fields because models use `extra="forbid"`;
- invalid URLs;
- out-of-range timeout/sampling values;
- invalid hardware memory values.

A validation error exits `performance-lab run` with execution/configuration error semantics rather than running with a partially guessed configuration.

## Reproducibility rules

Treat the config as one input to the fingerprint, not the whole fingerprint. Dataset snapshot, evaluator versions, benchmark protocol, generated model/runtime identity, telemetry descriptor and effective generation/load settings are frozen into `ExecutionFingerprint` at run start.

If an identity field is not explicitly supplied or observed, it remains unknown.