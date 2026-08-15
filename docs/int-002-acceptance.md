# INT-002 — Local LLM Server execution identity

Status: implementation validation

## Dependencies

- FND-002 canonical `ExecutionFingerprint`
- INT-001 `local-llm-server` runtime telemetry integration
- Local LLM Server `local-llm-identity-v1` producer contract

## Acceptance criteria

- validate `local-llm-identity-v1` without provider-specific inference guessing;
- map model revision/digest/quantization into `ModelIdentity`;
- map backend name/version/config digest into `RuntimeIdentity`;
- map non-sensitive hardware fields into `HardwareIdentity`;
- freeze the resolved identity before evaluation starts;
- keep identity optional for generic OpenAI-compatible endpoints;
- allow identity to be required for evidence-grade campaigns;
- reject explicit hardware metadata that conflicts with first-party server identity;
- preserve existing `/status` telemetry semantics independently;
- deterministic fake-server tests cover the wire contract and end-to-end runner mapping;
- documentation in both repositories names the same protocol version and endpoint.
