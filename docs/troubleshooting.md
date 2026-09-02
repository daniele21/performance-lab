# Troubleshooting

Status: active
Document type: operational-guide
Owner: developer experience
Canonical scope: operations.troubleshooting
Read when: endpoint probing, run configuration, identity/telemetry discovery, persistence, or regression behavior is unexpected
Last reviewed: 2026-08-15

This guide focuses on preserving evidence semantics while diagnosing failures. Do not make a run “work” by inventing missing identity or silently weakening comparability.

## Start with `probe`

Before debugging a full run:

```bash
performance-lab probe \
  --base-url http://127.0.0.1:1235/v1/ \
  --model my-model \
  --json
```

If the probe is unhealthy, fix connectivity/routing/authentication before debugging datasets or evaluators.

## `run` says the config is invalid

Version-1 configs are strict. Common causes:

- missing or unsupported `schema_version`;
- unknown field names;
- invalid/empty required strings;
- invalid URL;
- invalid timeout/sampling range;
- invalid hardware memory value.

Use [`run-config-reference.md`](run-config-reference.md). Performance Lab intentionally rejects unknown fields rather than silently dropping them.

## Endpoint works manually but `probe`/`run` cannot connect

Check that `endpoint.base_url` points to the OpenAI-compatible namespace, normally:

```text
http://127.0.0.1:1235/v1/
```

not just the server root.

If authentication is required, reference an environment variable using the endpoint auth config or CLI probe auth options. Do not put the secret itself in `endpoint_identity` or persisted config.

## Model discovery succeeds but generation fails

Confirm the selected `model_id`/`model_selector` is actually accepted by the endpoint. A `/v1/models` entry does not guarantee every provider-specific generation option is supported.

Performance Lab probes capabilities conservatively. Unsupported options should fail or remain unknown rather than being silently dropped unless an explicit policy owns that behavior.

## Protocol error: missing `choices[0].message.content`

For non-streaming OpenAI-compatible generation, Performance Lab requires the canonical answer at:

```text
choices[0].message.content
```

Provider-specific fields such as `output`, `response`, `content` or `final_answer` are not fallback answer locations for the reference adapter.

Fix the adapter/provider contract rather than teaching the evaluator to guess among arbitrary response fields.

## Token throughput is unavailable

This can be correct. Token-based performance evidence requires trustworthy token counts/timing boundaries. If the endpoint does not return OpenAI-compatible usage or another explicitly adapted token source, Performance Lab leaves token metrics unavailable.

Do not convert characters, chunks or bytes into tokens without a defined measurement protocol.

## Local LLM Server identity is unavailable but the run still proceeds

This is the expected compatibility mode when identity discovery is optional.

If `local_llm_server_identity` is absent and telemetry is configured, the runner performs best-effort discovery. Older server versions can therefore remain valid black-box/instrumented targets with unknown identity fields.

For an evidence campaign where identity is mandatory, configure:

```json
{
  "local_llm_server_identity": {
    "base_url": "http://127.0.0.1:1235",
    "required": true
  }
}
```

Then discovery/validation failure intentionally aborts before the fingerprint is frozen.

## Identity request returns 404

Confirm the server supports `GET /v1/runtime/identity` and that the configured Local LLM Server identity `base_url` is the server root:

```text
http://127.0.0.1:1235
```

The integration appends the versioned identity path; do not use the inference `/v1/` base in this config field.

## Hardware conflict stops the run

Performance Lab rejects a run when first-party Local LLM Server identity and explicit run config provide conflicting values for the same hardware field.

This is intentional. Determine which source is wrong; do not delete one value merely to bypass the conflict unless it truly was not evidence-grade/authoritative.

Explicit config may safely fill a hardware field that the server leaves unknown.

## `/status` telemetry has sample errors

Runtime telemetry is optional and isolated from black-box evaluation. Check:

- server root/base URL;
- `/status` availability;
- selected `model_id`;
- polling timeout;
- whether the runtime existed for the full sampling window.

Some sample loss may be observable evidence rather than a run failure. Short inference phases can also occur between polls.

## Status telemetry does not match token metrics

They have different boundaries. Local LLM Server `chunks_per_second` is runtime chunk evidence; Performance Lab does not relabel it as tokens/s.

Use client/performance token evidence when token counts are observable.

## Run succeeds but expected raw prompt/output text is not in the bundle

This is intentional. The canonical persisted `Run` does not structurally store raw prompt or generated output text by default. It stores identities, scores, token counts when observed, measurements and typed error evidence.

See [`output-and-evidence-reference.md`](output-and-evidence-reference.md).

## Reusing a `run_id` fails

Completed runs are immutable. If a completed `run_id` already exists with different canonical content, the store rejects replacement.

Use a new run ID for a new execution. Do not overwrite a historical result just because the model/config changed.

## `.plab.zip` import/validation fails

A version-1 bundle must contain exactly:

```text
manifest.json
run.json
```

and the SHA-256 in the manifest must match the exact canonical `run.json`. Common failures are modified payloads, extra files, malformed ZIP/JSON, wrong bundle version or mismatched `run_id`.

Treat the bundle as immutable evidence.

## Regression returns `NOT_COMPARABLE`

Inspect fingerprint differences before thresholds. Examples that can legitimately block a dimension include:

- different dataset snapshot/evaluator/template/protocol for capability;
- incompatible load/hardware/protocol for runtime;
- incompatible hardware/telemetry protocol for resource evidence.

A model/runtime/quantization change may be the intended experimental variable and does not by itself imply non-comparability across every dimension.

Do not convert `NOT_COMPARABLE` into `PASS`.

## Regression returns `NOT_EVALUATED`

This means the policy could not produce a justified threshold decision, for example because the direction/evidence needed by a rule is unknown or unavailable.

Fix the policy/evidence gap; do not invent a default verdict.

## Resource rules become `NOT_COMPARABLE` in CI

`regress-ci` treats runner hardware as uncontrolled by default, even if stored fingerprints look similar. This prevents false resource regressions/improvements caused by runner variation.

Use `--runner-identity-controlled` only when the CI topology genuinely guarantees comparable runner identity. The flag does not bypass normal fingerprint compatibility rules.

## `regress` cannot find a baseline/candidate run

Verify both are immutable completed runs in the `--store` path you supplied. The CLI does not silently select “latest” as a baseline.

Keep baseline choice explicit and retain run IDs with the campaign evidence.

## Exit code is non-zero but the tool produced a JSON artifact

For regression automation this may be expected:

```text
0 PASS
1 FAIL
2 ERROR
3 NOT_COMPARABLE
4 NOT_EVALUATED
```

`regress-ci` writes its JSON artifact before returning the gate exit code when possible. Upload the artifact with `if: always()` in GitHub Actions.

## A metric is missing instead of zero

Missing/unknown/unavailable is a first-class evidence state. Zero means an observed zero. Performance Lab intentionally refuses to fabricate metrics merely to make dashboards complete.

## Need to diagnose without exposing sensitive content

Useful safe evidence includes:

- run ID and fingerprint ID;
- sanitized run config (no credential values);
- endpoint/provider version;
- identity protocol/payload when privacy-safe;
- measurement names/provenance/protocol versions;
- typed sample error code/category;
- regression policy and comparability reasons.

Do not paste secrets, raw prompts or generated private output merely to diagnose an orchestration issue.

## Still unclear

Read in this order:

1. [`getting-started.md`](getting-started.md);
2. [`run-config-reference.md`](run-config-reference.md);
3. [`cli-reference.md`](cli-reference.md);
4. [`output-and-evidence-reference.md`](output-and-evidence-reference.md);
5. Local LLM Server-specific [`local-llm-server-integration.md`](local-llm-server-integration.md) and [`local-llm-identity-contract.md`](local-llm-identity-contract.md).