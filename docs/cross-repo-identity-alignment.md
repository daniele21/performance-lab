# Cross-repository identity alignment

`daniele21/local-llm-server` is the producer and AI Performance Lab is the consumer of the versioned `local-llm-identity-v1` protocol.

Producer endpoint:

```text
GET /v1/runtime/identity
```

The contract is deliberately independent from:

- OpenAI-compatible inference (`/v1/models`, `/v1/chat/completions`);
- dynamic runtime telemetry (`/status`);
- Performance Lab benchmark/dataset/evaluator configuration.

Local LLM Server owns truth about the resident model artifact, backend, safe effective serving configuration and hardware profile. Performance Lab validates that truth and freezes the mapped identity into `ExecutionFingerprint` before evaluation starts.

An incompatible producer change must introduce a new protocol version. Performance Lab must never reinterpret an incompatible payload as `local-llm-identity-v1`.
