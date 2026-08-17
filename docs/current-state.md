# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-17

This is the short operational ledger for Performance Lab. Durable behavior belongs in architecture/feature/ADR/design contracts; active implementation detail belongs in bounded workstreams.

## Current phase

The benchmark/evidence core is integrated on `dev`; the next product phase is **task-model-first UI productization plus representative real-device evidence**.

Performance Lab can already execute reproducible endpoint evaluations, capture quality/runtime/optional resource evidence, freeze execution identity, persist immutable runs, export `.plab.zip`, compare compatible evidence and enforce regression policies through CLI/CI. Deterministic product E2E is integrated.

The major product gap is no longer the engine: it is the local visual product that makes tested models, run evidence and comparison usable without CLI-only workflows.

The product experience direction is explicitly organized around the user's decision flow rather than internal benchmark modules:

```text
Overview
Test a model
Runs
Compare

Library / Settings -> advanced and expert capability
```

The canonical UX/brand source of truth is `design/`, with project-specific `ux-contract.json`, `brand-kit.json` and reference views.

## Ownership direction

ADR 0004 is accepted:

- **Performance Lab** is the long-term owner of benchmark/evaluation, run history, comparison, baselines/regression and their UX.
- **Local LLM Server** remains the serving/runtime control plane: inference, residency, scheduling/resources, identity and dynamic status.
- Local LLM Server's current evaluation surface is transitional and is removed only after Performance Lab replacement parity, migration policy and cross-product evidence are complete.

## Integrated baseline

The current `dev` line includes:

- versioned immutable domain/fingerprint contracts;
- OpenAI-compatible endpoint adapter and capability probing;
- bundled/custom datasets and workload packs;
- deterministic evaluators plus optional rubric judge;
- latency/TTFT/throughput, repeatability and bounded load protocols;
- host/runtime telemetry with explicit provenance;
- Local LLM Server `/v1/runtime/identity` and `/status` integration;
- immutable SQLite run evidence, portable bundles and retention;
- compatible comparison, explicit baselines and versioned regression policies;
- CLI `probe`, `inspect`, `run`, `regress`, `regress-ci`;
- constrained Python 3.12/3.13 CI dependencies;
- deterministic Product E2E across CLI + HTTP + persistence + regression.

Passing deterministic CI is implementation evidence, not representative model/device benchmark evidence.

## Product UI contract and foundation in the active UX alignment change

The active UI change now contains both the product contract and the executable browser foundation:

- canonical design source of truth under `design/`;
- task-model-first information architecture;
- primary navigation: Overview / Test a model / Runs / Compare;
- secondary Library and Settings surfaces for benchmark internals/expert configuration;
- Test a model journey: Model -> Scenario -> Test -> Review;
- compatibility-first Compare behavior;
- explicit loading/empty/error/offline/partial/not-evaluated/not-comparable/cancelled states;
- WCAG 2.2 AA target and compact/standard/wide desktop adaptive contexts;
- J1-J6 critical journeys mapped to future browser evidence;
- React + TypeScript + Vite browser foundation under `frontend/`;
- exact Node/npm/dependency pins with committed `package-lock.json`;
- loopback-only Vite development/preview listeners with fixed-port failure behavior;
- repository operating commands under `.engineering/commands.json`;
- deterministic frontend `check`, `test` and production `build` gates in CI;
- scoped frontend contributor rules preserving Python ownership of benchmark semantics.

The foundation shell is engineering evidence only. Overview, Runs, Test a model, Compare and their production states are still implemented by the downstream UI tasks.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [UI productization](workstreams/ui-productization.md) | ACTIVE | `UIA-001 + UIK-001` in parallel |
| Representative model/device evidence | READY | first real Local LLM Server smoke + retained run bundle |

Completed E2E hardening is documented in [`e2e-product-acceptance.md`](e2e-product-acceptance.md); it does not replace real-runtime or human acceptance.

## Immediate next block

1. **UIA-001 + UIK-001 in parallel** — implement the versioned UI application/read API and executable semantic design system from the `design/` contracts.
2. Build **Overview/Tested Models** and **Runs/Run Detail** first once the first API/read-model and primitive slices are stable; both expose existing immutable evidence without requiring new run-lifecycle writes.
3. Build **Test a model** as Model -> Scenario -> Test -> Review against explicit preflight/frozen-execution contracts; do not expose the raw benchmark config as the default UX.
4. Add **Live Run/cancellation/recovery** only after `UIA-002` proves server-owned lifecycle and cleanup semantics.
5. Build **Compare/regression** compatibility-first: verdict and identity differences precede valid metric deltas.
6. Keep Library/Settings secondary throughout implementation so suites/datasets/policies/targets do not drift back into the primary task model.
7. In parallel, execute the first real Local LLM Server smoke/evidence run so UI assumptions are checked against real identity/telemetry rather than fixtures only.
8. Start Local LLM Server evaluation deprecation only after Performance Lab UI parity is product-tested.

## Integration lines

- `dev` is the canonical implementation/integration line.
- `main` is stable/release-oriented and is promoted deliberately after evidence.
- Feature branches start from current green `dev`, remain focused and merge through CI-green PRs.

## Evidence still required

Before broad product/release claims:

- real resident-model starter/workload run with retained fingerprint and bundle;
- repeated/load evidence on controlled hardware;
- real Local LLM Server identity + telemetry usefulness check;
- real baseline/candidate regression evidence;
- built UI component/integration tests for the semantic design system and states;
- built UI Playwright J1-J6 journeys plus cancellation/recovery/zero-residue evidence;
- automated/manual accessibility evidence appropriate to WCAG 2.2 AA;
- adaptive-layout evidence for compact/standard/wide desktop contexts;
- human/manual acceptance of the shipped local product surface and progressive-disclosure hierarchy.
