# Performance Lab — coding agent guide

This file is the repository-wide navigation layer for coding agents. It owns durable invariants, routing and validation selection. It is not a status ledger or a substitute for architecture, feature or workstream documentation.

## Read only what the task requires

Always read this guide, then only:

1. the closest scoped `AGENTS.md` for the target subtree (`frontend/AGENTS.md` for browser work);
2. the canonical architecture/feature/workstream source required by the change;
3. `.engineering/commands.json` when setup, test, E2E, build, runtime or cleanup behavior is relevant;
4. for meaningful user-facing work, `design/ux-contract.json` and `design/brand-kit.json`;
5. the owning implementation, direct consumers and nearby tests.

Use `docs/current-state.md` only when the task depends on current integrated/blocked/next state. Do not load every plan or all documentation for a local change.

## Repository purpose

Performance Lab evaluates externally served AI inference endpoints. It answers a deployment decision: for a use case and device, which available model/configuration provides the best evidence-backed trade-off? The lab owns evaluation, evidence, comparison and regression; the serving runtime remains external.

## Non-negotiable invariants

- Core does not own model loading or serving-runtime lifecycle.
- A model name alone is never a complete benchmark identity; execution fingerprints remain explicit and immutable.
- Completed run evidence and dataset snapshots are immutable/versioned.
- Quality, runtime performance and resource evidence remain separate dimensions.
- Compatibility is established before deltas, rankings or regression verdicts are shown.
- Unknown/unavailable evidence is never encoded as zero or silently fabricated.
- Endpoint-reported and lab-observed measurements retain distinct provenance.
- Secrets and raw authorization material are never persisted in portable evidence.
- UI/application projections consume canonical Python semantics; TypeScript must not reimplement benchmark/comparability truth or read SQLite directly.
- Local UI/API listeners default to loopback. Run jobs, listeners, temporary state and evidence artifacts are bounded and have explicit cleanup ownership.
- Real device/model claims require real evidence; deterministic fakes or hosted CI must not be promoted into hardware claims.

## Ownership and routing

| Change | Start here | Inspect next |
| --- | --- | --- |
| Domain / fingerprint / comparability | `src/performance_lab/domain/` | `docs/architecture.md`, consumers, tests |
| Inference integration | `src/performance_lab/adapters/` | plugin contracts, performance/orchestrator tests |
| Dataset / evaluator behavior | `src/performance_lab/datasets/`, `src/performance_lab/evaluation/` | evaluation spec, fixtures/tests |
| Runtime benchmark / telemetry | `src/performance_lab/performance/`, `src/performance_lab/telemetry/` | provenance/resource contracts, tests |
| Persistence / comparison / regression | `src/performance_lab/storage/`, `src/performance_lab/regression/` | evidence reference, tests |
| UI application/API lifecycle | `src/performance_lab/application/`, `src/performance_lab/ui_api.py`, `src/performance_lab/ui_server.py` | frontend API client, lifecycle tests |
| Browser UI | `frontend/AGENTS.md` | `design/`, owning page/components/tests |
| Product experience / design system | `design/ux-contract.json` | `design/brand-kit.json`, `frontend/src/design/`, critical journeys |
| Active coordinated work | `docs/current-state.md` | relevant `docs/workstreams/*.md` only |

Add another scoped `AGENTS.md` only when a subtree has meaningful local hazards, ownership or validation rules.

## Project operating commands

`.engineering/commands.json` is the canonical intent-to-command map. Use it rather than inventing a second command path.

- `check` — broad cheap validation while iterating.
- `test` — unit/integration/contract behavior.
- `e2e` — complete critical workflow evidence when lower-level tests are insufficient.
- `build` — production browser build when shipped code changes.
- `smoke` — minimal built/runtime viability when applicable.
- `stop` / `clean` — release project-owned runtime/generated state.

E2E and smoke are not synonyms. The current build-identity/artifact-promotion gap is explicitly owned by `REL-UI-001`; do not mark those deferred guarantees complete before the implementation exists.

## Product experience routing

The repository adopts the `product-ui` profile. Meaningful UX/UI work follows this dependency order at the depth justified by the change:

```text
user outcome
-> task model
-> information architecture / critical journey
-> information + action hierarchy
-> progressive disclosure / defaults
-> interactions / states / feedback / recovery
-> adaptive / platform behavior
-> accessibility
-> design system / components
-> motion
-> visual polish / graphics
-> validation
```

Structural UX changes traverse the full sequence. Interaction changes start at the earliest affected task/state boundary. Visual-only changes preserve the settled task model and use existing semantic components/tokens.

Do not expose internal benchmark architecture merely because the backend has more options. Motion and graphics need an experience purpose; they must not compensate for unresolved hierarchy, flow, feedback or recovery.

## Change workflow

1. Confirm the owning boundary and smallest coherent scope.
2. Inspect owner, direct consumers, fakes and tests before changing shared contracts.
3. For coordinated work, use the single active bounded workstream instead of creating branch-progress documents.
4. Implement one coherent slice without speculative layers.
5. Validate narrowly while iterating, then expand according to blast radius using `.engineering/commands.json`.
6. Update only canonical durable docs/design contracts whose current behavior or decision changed.
7. Update `docs/current-state.md` only for integrated/blocked/next state changes.
8. Finalize completed workstreams by transferring durable knowledge and deleting the workstream by default.
9. Inspect the complete diff before publishing.

## Documentation lifecycle

- `docs/architecture.md` owns current architecture and ownership boundaries.
- `docs/features/` owns durable shipped feature behavior when extra explanation is needed.
- `docs/adr/` owns accepted durable architectural decisions.
- `docs/current-state.md` is the single short operational ledger.
- `docs/workstreams/` contains only active bounded implementation plans.
- `design/` owns product-experience and brand/design-system contracts.
- Git history owns implementation and completed-plan history.

Do not create new plan changelogs, per-branch progress docs or duplicate status registries.

## Evidence and stop conditions

Never claim validation, accessibility, real-device performance, cleanup or release evidence that was not executed. Surface the conflict instead of improvising when a change would violate a durable invariant/ADR, expose sensitive state, create a second source of truth, bypass comparability/evidence identity, bypass required lifecycle cleanup, or contradict the adopted product-experience contract.
