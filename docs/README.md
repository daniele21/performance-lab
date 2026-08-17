# Documentation map

Status: active
Document type: documentation-governance
Owner: repository
Canonical scope: documentation.routing
Read when: locating the canonical source for a project question
Last reviewed: 2026-08-17

Performance Lab documentation uses progressive disclosure: start with the one source that owns the question, then follow focused links. Do not duplicate behavioral truth across planning, architecture and operational docs.

## Start here

If you want to **use the current CLI product**:

1. [`getting-started.md`](getting-started.md)
2. [`run-config-reference.md`](run-config-reference.md)
3. [`cli-reference.md`](cli-reference.md)
4. [`output-and-evidence-reference.md`](output-and-evidence-reference.md)
5. [`troubleshooting.md`](troubleshooting.md)

If you want to **work on the local visual product**:

1. [`current-state.md`](current-state.md) — what is active now.
2. [`workstreams/ui-productization.md`](workstreams/ui-productization.md) — active dependency DAG and acceptance gates.
3. [`adr/0004-performance-lab-owns-evaluation-product.md`](adr/0004-performance-lab-owns-evaluation-product.md) — Performance Lab vs Local LLM Server ownership decision.
4. [`assets/design/README.md`](assets/design/README.md) — visual direction and behavioral boundaries of the mockups.
5. [`architecture.md`](architecture.md) — current durable dependency/ownership model.

## Canonical owners

| Question | Source |
| --- | --- |
| What is integrated and what happens next? | [`current-state.md`](current-state.md) |
| What is the active UI implementation DAG? | [`workstreams/ui-productization.md`](workstreams/ui-productization.md) |
| Who owns benchmark/evaluation long term? | [`adr/0004-performance-lab-owns-evaluation-product.md`](adr/0004-performance-lab-owns-evaluation-product.md) |
| What visual direction is approved? | [`assets/design/README.md`](assets/design/README.md) + [`assets/design/ui-reference-board.webp`](assets/design/ui-reference-board.webp) |
| What are the durable architecture boundaries? | [`architecture.md`](architecture.md) |
| How should benchmark/dataset/evaluator semantics work? | [`evaluation-and-benchmarking.md`](evaluation-and-benchmarking.md) |
| How should telemetry/provenance work? | [`telemetry.md`](telemetry.md) |
| How does Local LLM Server integrate? | [`local-llm-server-integration.md`](local-llm-server-integration.md) |
| How is Local LLM identity mapped? | [`local-llm-identity-contract.md`](local-llm-identity-contract.md) |
| What is persisted/exported? | [`output-and-evidence-reference.md`](output-and-evidence-reference.md) |
| How does regression CI behave? | [`ci-regression.md`](ci-regression.md) |
| What does deterministic product E2E prove? | [`e2e-product-acceptance.md`](e2e-product-acceptance.md) |
| What is required before DONE? | [`definition-of-done.md`](definition-of-done.md) |
| Where are durable architecture decisions? | [`adr/README.md`](adr/README.md) |

## Documentation lifecycle

- `current-state.md` stays short and volatile.
- `docs/workstreams/` contains only active bounded plans; completed plans are deleted after durable knowledge is transferred.
- `architecture.md`, focused feature docs and ADRs own durable truth.
- operational references describe what the executable product does now, not aspirational UI.
- visual mockups are references, never evidence that a feature is shipped.

When sources conflict, prefer: executable contracts/tests -> accepted ADRs -> architecture/focused specs -> operational references -> active workstream/current state -> roadmap/root README.
