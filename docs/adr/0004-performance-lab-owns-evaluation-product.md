# ADR 0004 — Performance Lab owns the evaluation product

Status: Accepted
Date: 2026-08-17

## Context

`local-llm-server` and Performance Lab currently overlap at the user-facing evaluation boundary. Local LLM Server has a Benchmark & Evaluation surface used for runtime diagnostics, while Performance Lab already owns the stronger benchmark engine: suites/datasets, evaluators, performance protocols, telemetry normalization, immutable run evidence, compatibility, comparison, baselines and regression policy.

Keeping two long-term benchmark/evaluation products would create duplicate UI, persistence, policy and metric semantics. It would also violate the one-owner principle: a user should not need to decide which product is authoritative for a benchmark result.

## Decision

**Performance Lab is the long-term owner of benchmark and evaluation as a product capability.**

Performance Lab owns:

- benchmark/evaluation configuration and execution orchestration;
- suites, datasets, workload packs and sampling policy;
- quality/runtime/resource result presentation;
- run history and experiment identity;
- comparison, baseline and regression UX;
- benchmark/evaluation persistence and portable evidence;
- the product UI for creating, monitoring, inspecting and comparing evaluation runs.

`local-llm-server` remains the inference/control-plane owner. It owns:

- model/runtime load, unload and residency;
- scheduling, admission and runtime resource policy;
- inference task execution;
- public runtime identity;
- dynamic runtime/status telemetry;
- serving diagnostics and operational controls.

The integration direction stays one-way at the product boundary:

```text
Performance Lab
    |
    +--> inference API
    +--> /v1/runtime/identity
    +--> /status
    |
    v
Local LLM Server
```

Local LLM Server must not depend on Performance Lab to serve models.

## Transition

Local LLM Server's existing evaluation API/UI is a **transitional compatibility surface**, not the target product owner. It is removed only after Performance Lab has proven replacement parity for the workflows that remain valuable.

Migration follows explicit gates:

1. Performance Lab can discover/select the intended Local LLM Server target and model.
2. Performance Lab can configure and execute the required evaluation workflow.
3. Live progress, cancellation and failure recovery are product-tested.
4. Existing useful result/history semantics have a documented preservation or intentional-drop policy.
5. Cross-product E2E proves the replacement path on deterministic fixtures and real-runtime smoke proves the public integration boundary.
6. Local LLM Server docs/UI direct users to Performance Lab for benchmark/evaluation.
7. Only then are redundant Local LLM Server evaluation routes/UI removed through a separate deprecation/removal change.

No compatibility layer is kept indefinitely without an identified consumer and removal criterion.

## Consequences

Positive:

- one authoritative benchmark/evaluation product and result model;
- Local LLM Server stays focused on reliable local inference operations;
- Performance Lab can evaluate Local LLM Server and unrelated OpenAI-compatible endpoints uniformly;
- comparison/history/regression become coherent across models, runtimes and devices.

Costs:

- Performance Lab needs a real local product surface, not only CLI/CI;
- a versioned local application API/read model is required between the UI and existing Python core;
- Local LLM Server evaluation functionality requires staged migration rather than immediate deletion;
- cross-repository E2E and deprecation evidence are required before ownership convergence is complete.

## Invariants

- No metric is invented to satisfy a mockup.
- Quality, runtime and resources remain separate dimensions.
- Compatibility is evaluated before deltas and rankings.
- Unknown/unavailable evidence stays explicit.
- The frontend never becomes an independent owner of benchmark semantics.
- Local LLM Server remains independently useful as an inference server.
