# local-llm-server integration

Status: active
Document type: focused-specification
Owner: runtime integration
Last reviewed: 2026-08-15

Performance Lab can collect runtime-native evidence from `daniele21/local-llm-server` without requiring a custom server plugin. The integration polls the server's existing public `/status` endpoint during a normal evaluation run.

## Why polling instead of server modification

The serving project already exposes the runtime state required for useful first-party evidence: active request count, configured concurrency, phase, output chunks/characters and observed chunks per second. Polling that existing contract keeps the serving runtime independent from Performance Lab while still preserving `RUNTIME` provenance.

The collector deliberately does **not** rename chunks per second to tokens per second. Token throughput remains a separate metric with a different measurement boundary.

## Run configuration

Add `local_llm_server_telemetry` to the normal version-1 run config:

```json
{
  "schema_version": 1,
  "target_id": "local-llm-server-qwen",
  "endpoint_identity": "localhost:8000",
  "endpoint": {
    "profile_id": "local-llm-server",
    "base_url": "http://127.0.0.1:8000/v1/",
    "model_selector": "qwen-model"
  },
  "model_id": "qwen-model",
  "store_path": ".performance-lab/runs.sqlite3",
  "use_host_telemetry": true,
  "local_llm_server_telemetry": {
    "base_url": "http://127.0.0.1:8000",
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

The OpenAI-compatible adapter uses `/v1/`; the runtime collector uses the server root because `/status` is outside the OpenAI API namespace.

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

All measurements use `MeasurementProvenance.RUNTIME`. If `/status` is unavailable or malformed, `TelemetrySession` isolates the collector failure and the black-box evaluation remains valid.

## Combined host + runtime evidence

`use_host_telemetry: true` may be combined with `local_llm_server_telemetry`. The resulting execution fingerprint records both collector identities under telemetry level `instrumented` and uses the stable combined protocol identifier `telemetry-session-v1`.

This keeps host/process evidence distinct from serving-runtime evidence while allowing the same run to carry both.

## Evidence limitations

Polling is observational. Short phases can occur between samples, so phase ratios and peaks are sampling-dependent. They should be compared only under the same collector protocol and sampling configuration.

The first real evidence campaign should therefore preserve the run config, execution fingerprint and bundle together with model/runtime/hardware identity. Stronger server-side counters can be added later only if polling proves insufficient for a concrete decision.
