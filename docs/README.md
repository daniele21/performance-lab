# Documentation map

Status: active
Document type: documentation-governance
Owner: repository
Canonical scope: documentation.routing
Last reviewed: 2026-08-30

Performance Lab uses progressive disclosure: start from the single canonical owner of the question, then follow focused references. Do not duplicate behavioral truth across status, workstreams, architecture, design and operational docs.

## README ownership

Treat the root README as two semantic owners:

- **Identity** — what Performance Lab is, why it exists, primary audience/outcome and stable positioning. Update only when those claims materially change; do not rewrite them merely because implementation, commands, configuration or a feature changes.
- **Usage** — prerequisites, setup/run, public configuration, CLI/API/UI workflow and copy-paste examples. Update in the same change whenever existing instructions would otherwise become incomplete, wrong, removed, newly mandatory or misleading.

A change may therefore correctly report `README_IDENTITY: N/A` and `README_USAGE: UPDATED`.

## Start here

To **use the current product**:

1. [`getting-started.md`](getting-started.md)
2. [`run-config-reference.md`](run-config-reference.md)
3. [`cli-reference.md`](cli-reference.md)
4. [`output-and-evidence-reference.md`](output-and-evidence-reference.md)
5. [`troubleshooting.md`](troubleshooting.md)

To **work on the repository**:

1. [`../AGENTS.md`](../AGENTS.md) — task routing and durable invariants.
2. [`current-state.md`](current-state.md) — integrated / blocked / next state.
3. [`architecture.md`](architecture.md) — ownership and dependency boundaries.
4. [`workstreams/README.md`](workstreams/README.md) — active coordinated work only.
5. [`../.engineering/commands.json`](../.engineering/commands.json) — canonical operating commands.

For **product UI / UX** also read:

- [`../design/ux-contract.json`](../design/ux-contract.json) — user jobs, task model, hierarchy, states, accessibility, motion/graphics and J1-J6;
- [`../design/brand-kit.json`](../design/brand-kit.json) — semantic brand and motion tokens;
- [`../frontend/AGENTS.md`](../frontend/AGENTS.md) — browser-specific ownership and validation.

## Canonical owners

| Question | Source |
| --- | --- |
| What is the project/why/for whom? | README identity sections |
| How should a person set up, configure, run or use it? | README usage summary plus `getting-started.md`, `run-config-reference.md`, `cli-reference.md` |
| What is integrated and what happens next? | [`current-state.md`](current-state.md) |
| Which active implementation plan coordinates remaining work? | [`workstreams/README.md`](workstreams/README.md) |
| What are the durable architecture boundaries? | [`architecture.md`](architecture.md) |
| Who owns benchmark/evaluation long term? | [`adr/0004-performance-lab-owns-evaluation-product.md`](adr/0004-performance-lab-owns-evaluation-product.md) |
| What product experience/design rules apply? | [`../design/`](../design/) |
| How should benchmark/dataset/evaluator semantics work? | [`evaluation-and-benchmarking.md`](evaluation-and-benchmarking.md) |
| How should telemetry/provenance work? | [`telemetry.md`](telemetry.md) |
| How does Local LLM Server integrate? | [`local-llm-server-integration.md`](local-llm-server-integration.md) |
| How is Local LLM identity mapped? | [`local-llm-identity-contract.md`](local-llm-identity-contract.md) |
| What is persisted/exported? | [`output-and-evidence-reference.md`](output-and-evidence-reference.md) |
| How does regression CI behave? | [`ci-regression.md`](ci-regression.md) |
| What does deterministic product E2E prove? | [`e2e-product-acceptance.md`](e2e-product-acceptance.md) |
| What is required before DONE? | [`definition-of-done.md`](definition-of-done.md) |
| Where are durable architecture decisions? | [`adr/README.md`](adr/README.md) |
| Where should durable feature behavior live when extra docs are needed? | [`features/README.md`](features/README.md) |

## Documentation impact contract

Code and durable documentation ship together. Assess impact from the observable result, not filenames. Before publication classify `README_IDENTITY`, `README_USAGE`, `FEATURE_DOCS`, `ARCHITECTURE`, `ADR`, `SECURITY_DATA`, `OPERATIONS`, `PRODUCT_EXPERIENCE` and `CURRENT_STATE` as `UPDATED` or `N/A`; give a short reason when impact was plausible but `N/A`.

Readiness requires `DOCS_CURRENT_WITH_IMPLEMENTATION: PASS`. Existing feature docs update in the same change when the shipped behavior they describe changes. Create a new feature doc only when durable non-obvious behavior is not sufficiently discoverable from code, public contracts, tests, architecture or the focused operational references.

Preserve stronger local owners: CLI/config/evidence semantics belong in their focused references; README usage should expose a reliable shortest-success path and link rather than duplicate exhaustive contracts.

## Documentation lifecycle

- `current-state.md` is the only short repository-level operational ledger.
- `workstreams/` contains only active bounded plans; completed plans are deleted after durable knowledge is transferred.
- `architecture.md`, `features/`, focused operational references and ADRs own durable truth.
- `design/` owns product-experience and brand/design-system contracts; generated screenshots/traces are evidence, not default durable design truth.
- Git history owns implementation/completed-plan history; do not create new plan changelogs or per-branch progress docs.
- Documentation and agent-context budgets are enforced by `.engineering/documentation-policy.json` as adoption checks are wired in.

When sources conflict, prefer executable contracts/tests -> accepted ADRs -> architecture/design/feature owners -> operational references -> active workstream/current state -> roadmap/root README.
