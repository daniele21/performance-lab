# local-llm-server identity contract

Status: active
Document type: focused-specification
Owner: runtime integration
Canonical scope: integration.local-llm-server.identity
Read when: connecting Performance Lab to Local LLM Server identity, preparing evidence-grade comparisons, or diagnosing missing model/runtime/hardware identity
Last reviewed: 2026-08-15

Protocol: `local-llm-identity-v1`  
Producer endpoint: `GET /v1/runtime/identity`  
Consumer task: `INT-002`

AI Performance Lab treats the identity endpoint as optional first-party identity evidence from `daniele21/local-llm-server`. It is independent from the OpenAI-compatible inference contract and from `/status` runtime telemetry.

## Responsibility split

The two repositories share the wire protocol but keep different ownership:

- Local LLM Server is the source of truth for the resident model artifact, effective backend, safe serving configuration and local hardware profile.
- Performance Lab validates that document, maps stable fields into its canonical domain and freezes them into `ExecutionFingerprint` before evaluation starts.
- Inference remains owned by `/v1/models` + `/v1/chat/completions`.
- Dynamic runtime telemetry remains owned by `/status`.
- An incompatible producer schema change requires a new protocol version; Performance Lab must never reinterpret it as `local-llm-identity-v1`.

## Why this exists

An inference response can tell Performance Lab what the model answered, but it cannot safely establish the complete configuration that produced the answer. Local LLM Server therefore exposes stable, path-free identity for the actual resident runtime. Performance Lab never infers quantization from model filenames or promotes arbitrary provider fields into canonical identity.

## Mapping

| `local-llm-identity-v1` | Performance Lab |
| --- | --- |
| `model.id` | `ModelIdentity.model_id` |
| `model.revision` | `ModelIdentity.revision` |
| `model.artifact_digest` | `ModelIdentity.artifact_digest` |
| `model.quantization` | `ModelIdentity.quantization` |
| `runtime.name` | `RuntimeIdentity.name` |
| `runtime.version` | `RuntimeIdentity.version` |
| `runtime.config_digest` | `RuntimeIdentity.config_digest` |
| `hardware.machine` | `HardwareIdentity.device_class` |
| `hardware.processor` | `HardwareIdentity.cpu` |
| `hardware.accelerator` | `HardwareIdentity.accelerator` |
| `hardware.total_memory_bytes` | `HardwareIdentity.memory_bytes` |
| `hardware.system` | `HardwareIdentity.os` |

Provider-only metadata such as the Local LLM Server package version, runtime implementation class, artifact key, runtime fingerprint and evidence grade are validated by the integration client but are not silently repurposed into unrelated fingerprint fields.

`RuntimeIdentity.config_digest` is part of the immutable execution identity so two runs using the same backend name/version but different effective serving configuration do not collapse into the same runtime identity.

## Selection rules

The configured identity `model_id` is resolved in this order:

1. exact key in the producer `models` map;
2. exactly one entry whose `model.id` equals the configured value;
3. when no model is configured, the producer `default_model`;
4. when no default is usable, the only resident model if exactly one exists.

Ambiguous or missing selections are typed identity errors.

## Run configuration

Identity can be enabled independently:

```json
{
  "local_llm_server_identity": {
    "base_url": "http://127.0.0.1:1235",
    "model_id": "nemotron-nano-4b",
    "timeout_seconds": 2.0,
    "required": true
  }
}
```

When `local_llm_server_telemetry` is already configured and no explicit identity block is present, the runner also attempts identity discovery from the same server root. That implicit attempt is best-effort so older Local LLM Server versions without `/v1/runtime/identity` remain valid black-box/instrumented targets.

`required: true` is appropriate for evidence campaigns where an unknown runtime identity would invalidate the intended comparison. If required discovery fails, the run fails before the fingerprint is frozen.

## Hardware conflict rule

Local LLM Server is authoritative for hardware fields it actually reports. Explicit run-config hardware may fill fields the server leaves unknown. If both sources provide a value for the same field and the values disagree, Performance Lab rejects the run rather than silently choosing one source.

## Compatibility and absence

The identity endpoint is not required for general OpenAI-compatible evaluation. Without it, Performance Lab preserves the existing honest fallback:

- configured model ID is known;
- runtime identity remains unknown;
- configured hardware remains available;
- missing revision/digest/quantization are not guessed.

This keeps Local LLM Server integration richer without making the core depend on that serving project.

## Acceptance contract

`INT-002` is complete only when:

- `local-llm-identity-v1` is strictly validated without provider-response guessing;
- model revision/digest/quantization map into `ModelIdentity`;
- backend name/version/config digest map into `RuntimeIdentity`;
- non-sensitive hardware maps into `HardwareIdentity`;
- resolved identity is frozen before evaluation starts;
- identity remains optional for generic OpenAI-compatible endpoints and can be required for evidence-grade campaigns;
- conflicting explicit hardware metadata is rejected;
- `/status` telemetry semantics remain independent;
- deterministic fake-server tests cover direct mapping and the end-to-end runner path;
- producer and consumer documentation name the same endpoint and protocol version.

Passing these deterministic integration tests is implementation evidence. Representative model/device runs are still required before treating identity quality and comparison usefulness as product evidence.
