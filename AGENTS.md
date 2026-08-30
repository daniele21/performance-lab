# Performance Lab — coding agent guide

This file is the repository-wide navigation layer for coding agents. It owns durable invariants, routing and validation selection. It is not a status ledger or a substitute for architecture, feature or workstream documentation.

## Read only what the task requires

Always read this guide, then only:

1. the closest scoped `AGENTS.md` for the target subtree (`frontend/AGENTS.md` for browser work);
2. the canonical architecture/feature/workstream source required by the change;
3. `.engineering/commands.json` when setup, test, E2E, build, runtime or cleanup behavior is relevant;
4. `.engineering/e2e.json` when a complete workflow or browser/runtime/device/environment-dependent claim is relevant;
5. `docs/README.md` when documentation ownership or README impact is unclear;
6. for meaningful user-facing work, `design/ux-contract.json` and `design/brand-kit.json`;
7. the owning implementation, direct consumers and nearby tests.

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
- Executor capability and environment fidelity are separate: `REMOTE_AUTOMATED` does not upgrade a fixture/emulator into target-environment evidence.
- Final real-runtime/device validation should confirm residual hardware/runtime/telemetry gaps, not become the first complete product workflow test when that workflow is automatable earlier.
- Code and durable documentation ship together; an affected stale canonical owner blocks publication readiness.
- README identity and README usage are separate owners: stable purpose/positioning is not rewritten for usage-only changes, while setup/run/configuration/public examples must stay current.

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
| Documentation impact | `docs/README.md` | README identity/usage, feature/architecture/ADR/security/operations/design/current-state owner |

Add another scoped `AGENTS.md` only when a subtree has meaningful local hazards, ownership or validation rules.

## Project operating commands

`.engineering/commands.json` is the canonical intent-to-command map. Use it rather than inventing a second command path.

- `check` — broad cheap validation while iterating.
- `test` — unit/integration/contract behavior.
- `e2e` — deterministic complete product workflow evidence through the Python/CLI/HTTP/persistence boundary.
- `build` — production browser build when shipped code changes.
- `smoke` — minimal built/runtime viability when applicable.
- `package` — publish only after package smoke and, through the canonical command, packaged J1 full-product E2E.
- `stop` / `clean` — release project-owned runtime/generated state.

E2E and smoke are not synonyms. The built-product lifecycle is active: build identity, immutable artifact promotion, manifest/checksum, build delta, retention and smoke/cleanup are enforced through the canonical operating contract.

## Validation and preflight

Use `skills/validate-change/SKILL.md` while iterating and `skills/preflight-change/SKILL.md` immediately before publication.

`python scripts/select_validation_profile.py` is the canonical blast-radius selector:

- `LEAN` — documentation/governance-only;
- `SCOPED` — contained implementation owner/module;
- `STRONG` — cross-boundary, user-facing, persistence, E2E or release-sensitive behavior;
- `FULL` — engineering/CI/dependency/toolchain/selector changes, promotion or unknown executable scope.

Do not silently downgrade below `auto`. A repair that broadens scope must re-run selection.

Before any ready state, `preflight-change` classifies `README_IDENTITY`, `README_USAGE`, `FEATURE_DOCS`, `ARCHITECTURE`, `ADR`, `SECURITY_DATA`, `OPERATIONS`, `PRODUCT_EXPERIENCE` and `CURRENT_STATE`; `DOCS_CURRENT_WITH_IMPLEMENTATION` must be `PASS`.

If the current agent cannot execute an automatable deterministic gate, classify it `REMOTE_AUTOMATED` and use repository-owned GitHub workflows through `remote-preflight`; do not turn the user into the test runner. Physical/runtime/device/telemetry evidence is `REAL_ENVIRONMENT` only when the claim genuinely requires it.

For E2E, also select the environment in `.engineering/e2e.json`:

- `browser-built-mocked-api` — built React + Chromium, Performance Lab API mocked (`host_or_fake`);
- `python-product-fixture` — real CLI/application/HTTP/SQLite/regression + deterministic inference fixture (`representative_virtual`);
- `packaged-product-fixture` — packaged wheel + built frontend + real API/SQLite/Chromium + deterministic inference fixture (`representative_virtual`);
- `real-runtime-device` — real external runtime/model/device (`target_environment`).

Use the cheapest environment that proves the changed claim. `RUNTIME-1` retains real model/runtime identity, physical resource, telemetry and thermal/repeated-load evidence as residual real-environment requirements.

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
3. For coordinated work, use the single owning active bounded workstream instead of creating branch-progress documents.
4. Implement one coherent slice without speculative layers.
5. Validate narrowly while iterating, then expand according to blast radius.
6. For complete workflows/environment claims, select the relevant `.engineering/e2e.json` journey and sufficient fidelity rather than running every E2E layer mechanically.
7. Assess documentation impact from observable behavior and update only affected canonical durable docs/design contracts; README identity and usage are independent owners.
8. Update `docs/current-state.md` only for integrated/blocked/next state changes.
9. Finalize completed workstreams by transferring durable knowledge and deleting the workstream by default.
10. Run preflight, review the complete diff, require current documentation and publish only exact-head evidence.

## Documentation lifecycle

- README identity owns stable purpose/audience/outcome/positioning; update only when those claims materially change.
- README usage owns the shortest current setup/run/configuration/public usage path; update when existing instructions/examples become incomplete, wrong or misleading, while focused operational references remain canonical for detail.
- `docs/architecture.md` owns current architecture and ownership boundaries.
- `docs/features/` owns durable shipped feature behavior when extra explanation is needed; existing feature docs update in the same change as the behavior they describe.
- `docs/adr/` owns accepted durable architectural decisions.
- `docs/current-state.md` is the single short operational ledger.
- `docs/workstreams/` contains only active bounded implementation/evidence plans.
- `design/` owns product-experience and brand/design-system contracts.
- Git history owns implementation and completed-plan history.

Do not create new plan changelogs, per-branch progress docs or duplicate status registries.

## Evidence and stop conditions

Never claim validation, accessibility, real-device performance, cleanup or release evidence that was not executed. Surface the conflict instead of improvising when a change would violate a durable invariant/ADR, expose sensitive state, create a second source of truth, bypass comparability/evidence identity, bypass required lifecycle cleanup, leave affected documentation stale, contradict the adopted product-experience contract, or overstate E2E environment fidelity.
