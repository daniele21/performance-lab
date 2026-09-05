# Performance Lab — coding agent guide

Repository-wide routing and durable invariants. Status belongs in `docs/current-state.md`; detailed behavior belongs in architecture/features/workstreams.

## Read only what the task requires

Always read this guide, then the closest scoped `AGENTS.md`, owning implementation/tests and only relevant contracts: `.engineering/commands.json` for operations/stages/gates, `.engineering/e2e.json` for complete-workflow/fidelity claims, `design/*` for meaningful product UI, and `docs/README.md` for documentation ownership.

## Purpose and invariants

Performance Lab evaluates externally served AI inference endpoints and answers which available model/configuration gives the best evidence-backed trade-off for a use case/device. It owns evaluation, evidence, comparison and regression; serving-runtime lifecycle remains external.

Preserve explicit immutable execution fingerprints; versioned completed evidence/datasets; separate quality/runtime/resource dimensions; compatibility before deltas/rankings/regression; distinct endpoint/lab provenance; no persisted raw authorization; Python as semantic owner with TypeScript projections; bounded local listeners/jobs/temp/artifacts; truthful separation of hosted fixtures from real device/model evidence.

## Ownership routing

Domain/comparability -> `src/performance_lab/domain/`; inference adapters -> `adapters/`; datasets/evaluation -> `datasets/`, `evaluation/`; benchmark/telemetry -> `performance/`, `telemetry/`; persistence/regression -> `storage/`, `regression/`; app/API -> `application/`, `ui_api.py`, `ui_server.py`; browser -> `frontend/AGENTS.md`; product experience -> `design/`.

## Delivery model

Performance Lab follows repo-template-sw **0.9.2**.

- `ITERATION`: focused owner-local Python/frontend checks while implementation changes. No exact-head/full-diff/doc ceremony and no browser/product/built-product gate merely because it exists.
- `INTEGRATION` (`PR -> dev`): prove the affected observable outcome automatically. Exact head, full diff, affected durable docs, selected risk gates and affected critical E2E are required. Required `REAL_ENVIRONMENT` evidence is explicit but non-blocking and deferred to release.
- `RELEASE` (`dev -> main`): FULL validation plus release-critical artifact/E2E and every applicable required residual real-environment confirmation.

The selector maps **risk dimensions -> required gates -> profile shorthand**. `LEAN | SCOPED | STRONG | FULL` summarize the decision; concrete gates are authoritative.

Parallel technical subtasks should converge early around vertical outcomes. Stacked publication is exceptional; avoid sync-only PR chains.

## Validation

`.github/workflows/validate.yml` is the automatic PR owner. It selects Python, frontend, product E2E, browser E2E and built-product gates. When `built-product` is required, it exercises the stronger integrated cone and satisfies overlapping frontend/product/browser gates rather than duplicating them in separate workflows. `browser-acceptance.yml` is manual diagnostic; `built-product.yml` is tag/manual release tooling.

Successful integration evidence is reusable. Before merge it is exact-head evidence. After a content-preserving merge to `dev`, reuse is allowed only when Git tree, prior target/base, required gates and profile are equivalent. Direct pushes without trusted evidence validate normally. Release remains FULL.

E2E UI evidence modes are `ASSERTIONS`, `SCREENSHOTS`, `FULL_MEDIA`. A material UI/UX integration journey uses FULL_MEDIA; screenshots remain sufficient for stable visible inspection/comparison claims. `RUNTIME-1` keeps real model/runtime/device/telemetry/thermal/repeated-load claims in `REAL_ENVIRONMENT`, and those claims gate release rather than entry into `dev`.

`PRE_REAL_E2E` remains useful: it proves that the complete automatable cone is green before any real runtime/device run. It does not make real-runtime evidence an integration gate.

## Documentation and failure discipline

Affected durable documentation must be current at `INTEGRATION`, not after every private edit. README identity and usage are separate owners. `docs/current-state.md` owns integrated/blocked/next truth, not branch diaries; completed workstreams are deleted after durable truth moves.

Classify failures as change regression, baseline, environment, flaky, base drift or assumption before editing. Fix the owning invariant; never suppress a legitimate gate for green CI or promote hosted evidence into a real-device claim.