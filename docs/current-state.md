# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-18

This is the short operational ledger for Performance Lab. Durable behavior belongs in architecture/feature/ADR/design contracts; active implementation detail belongs in bounded workstreams.

## Current phase

The benchmark/evidence engine and the first end-to-end local product path are integrated on `dev`.

Performance Lab can now execute reproducible endpoint evaluations, capture quality/runtime/optional resource evidence, freeze execution identity, persist immutable runs, export `.plab.zip`, compare compatible evidence, enforce regression policies through CLI/CI, and expose the same ownership model through a loopback browser product.

The integrated primary path is:

```text
Overview
  -> Test a model
      -> Model
      -> Scenario
      -> Test
      -> frozen Review
      -> Run test
      -> Live Run
      -> immutable Run Detail

Runs -> Run Detail
Compare -> next product slice
```

The canonical UX/brand source of truth remains `design/`, with project-specific `ux-contract.json`, `brand-kit.json` and reference views.

Passing deterministic CI is implementation evidence, not representative model/device benchmark evidence.

## Ownership direction

ADR 0004 is accepted:

- **Performance Lab** is the long-term owner of benchmark/evaluation, run history, comparison, baselines/regression and their UX.
- **Local LLM Server** remains the serving/runtime control plane: inference, residency, scheduling/resources, identity and dynamic status.
- Local LLM Server's current evaluation surface is transitional and is removed only after Performance Lab replacement parity, migration policy and cross-product evidence are complete.

## Integrated benchmark/evidence baseline

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

## Integrated local product surface

The browser product now includes:

- React + TypeScript + Vite foundation under `frontend/`;
- executable semantic design tokens and reusable product primitives;
- task-model-first primary navigation: Overview / Test a model / Runs / Compare;
- tested-model-first Overview backed only by immutable stored run evidence;
- Runs list and immutable Run Detail with separate quality/performance/resource evidence;
- Model -> Scenario -> Test -> Review wizard;
- server-side preflight with frozen `StarterRunConfig` digest;
- server-owned bounded run lifecycle with one active job per local process and no implicit queue;
- launch-time revalidation of the exact frozen digest;
- reconnectable Live Run using job identity separate from immutable run identity;
- explicit cancellation, shutdown and restart/interrupted semantics;
- bounded revision-based progress and SSE transport;
- successful terminal navigation into immutable Run Detail;
- explicit loading/empty/error/cancelled/interrupted/reconnecting states;
- loopback-only local API composition root exposed as `performance-lab-ui`;
- Vite development proxy from `/api` to the fixed local API listener;
- frontend check/Vitest/build plus Python 3.12/3.13 and Product E2E gates.

The local process graph is now explicit:

```text
Browser UI
   |
   | /api/v1 + SSE
   v
FastAPI loopback adapter
   |
   +--> UIQueryService
   +--> RunJobManager
   +--> SQLiteRunStore
   +--> canonical starter registries
   |
   v
endpoint adapter / Local LLM Server
```

The composition root is development/product execution evidence. Final static-asset packaging, browser/process ownership, release smoke and cleanup remain separate release work.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [UI productization](workstreams/ui-productization.md) | ACTIVE | compatibility-first Compare, then secondary Library/Settings |
| Browser acceptance | PLANNED | Playwright J1-J6, cancellation/recovery and zero-residue evidence |
| Representative model/device evidence | READY | first real Local LLM Server smoke + retained run bundle |
| Built-product lifecycle | PLANNED | packaged UI process, smoke/start/stop/clean evidence |

Completed deterministic product E2E is documented in [`e2e-product-acceptance.md`](e2e-product-acceptance.md); it does not replace real-runtime, browser or human acceptance.

## Immediate next block

1. Build **Compare** compatibility-first: identity differences and compatibility reasons precede any metric deltas; invalid deltas stay absent.
2. Complete **Library / Settings** as secondary expert surfaces backed by canonical suite/dataset/baseline/policy/endpoint/target owners.
3. Add **Playwright browser acceptance** for the critical product journeys, including refresh/reconnect, explicit cancellation and recovery.
4. Execute the first **real Local LLM Server model/device run** through the integrated local product and retain the resulting fingerprint/bundle.
5. Add representative repeated/load and baseline/candidate regression evidence on controlled hardware.
6. Finish **built-product lifecycle** only after browser behavior is stable: static assets, local process/browser ownership, bounded artifacts and clean shutdown.
7. Start Local LLM Server evaluation deprecation only after replacement parity and migration evidence are complete.

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
- browser-level J1-J6 acceptance plus cancellation/recovery/zero-residue evidence;
- automated/manual accessibility evidence appropriate to WCAG 2.2 AA;
- adaptive-layout evidence for compact/standard/wide desktop contexts;
- built-product start/stop/clean and no-orphan listener/browser/temp-state evidence;
- human/manual acceptance of the shipped local product surface and progressive-disclosure hierarchy.
