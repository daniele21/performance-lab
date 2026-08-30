# Product UX/UI convergence

Status: active
Owner: product experience / browser UI
Read when: implementing or coordinating the UX/UI convergence from the canonical product contract to the built Performance Lab product

## Goal

Deliver the approved Performance Lab desktop experience end to end so the product can answer, with inspectable evidence: for this use case on this device, which available model + quantization + configuration is the best fit, and why?

The implementation must converge on `design/ux-contract.json`, `design/brand-kit.json` and the approved targets under `design/reference/visual-targets/desktop-standard/` without turning those images into pixel-regression truth.

## Non-goals

- Moving model loading, unloading or serving-runtime lifecycle into Performance Lab.
- Inventing benchmark semantics, parameter ranges, evaluator explanations or recommendation scores in TypeScript.
- Treating generated design targets as browser golden screenshots.
- Expanding to mobile layouts before the desktop compact/standard/wide contract is complete.

## Invariants

- Primary task hierarchy remains `Overview -> Find best setup -> Test a model -> Runs -> Compare`; Library and Settings stay visually secondary.
- Quantizations are distinct model candidates, not configuration-sweep values.
- A Run is one immutable evidence unit for one model candidate and one frozen configuration; Campaign groups Runs.
- Compatibility precedes deltas, ranking and recommendations.
- Quality, performance and resources remain separate; unknown/unavailable/not-comparable are never encoded as zero.
- Aggregate results drill down to retained sample/evaluator evidence when the retention contract permits it.
- Browser UI consumes backend-owned read models and does not read SQLite or recreate domain truth.
- WCAG 2.2 AA semantics, keyboard/focus behavior and reduced-motion behavior are part of acceptance, not polish.

## Work graph

| ID | Work | Owns/writes | Depends on | Parallel | State |
| --- | --- | --- | --- | --- | --- |
| UXUI-00 | Stabilize and merge the UX/discovery baseline | baseline UX contracts/targets; model discovery; shared form semantics | — | no | DONE |
| UXUI-01 | Design-system + brand convergence | `frontend/src/design/`, shared visual primitives/assets | UXUI-00 | yes, with UXUI-04A | ACTIVE |
| UXUI-02 | App shell + canonical IA/adaptive desktop navigation | `AppShell`, navigation/routing, shell CSS/tests | UXUI-01 | no | BLOCKED |
| UXUI-03 | Manual journey convergence: connect/discover -> scenario -> configure -> frozen review -> Live Run -> Run Detail | test-model/live-run/run-detail pages and direct API consumers | UXUI-01, UXUI-02 | yes, separate from Library contracts | BLOCKED |
| UXUI-04A | Library/read-model contracts for Models, Benchmarks, Datasets, Evaluators, Evidence | Python application read models/queries/API + contract tests | UXUI-00 | yes, with UXUI-01 | ACTIVE |
| UXUI-04B | Library + Settings UI convergence | library/settings pages and API client types | UXUI-01, UXUI-02, UXUI-04A | yes, separate from manual journey | BLOCKED |
| UXUI-05 | Benchmark/sample evidence drill-down | benchmark detail, run samples, sample evidence projections/pages | UXUI-04A | yes, with UXUI-03/04B where write boundaries do not overlap | BLOCKED |
| UXUI-06 | Find best setup planning: use case -> candidates -> config search -> benchmark plan -> estimate | campaign planning domain/application/API + page flow | UXUI-04A, UXUI-05 contracts as needed | no | BLOCKED |
| UXUI-07 | Campaign lifecycle + results/recommendation | campaign persistence/orchestration/read models; live/results UI | UXUI-06 | no | BLOCKED |
| UXUI-08 | Same-case cross-candidate comparison | comparison application read models + case comparison UI | UXUI-05, UXUI-07 | yes, after stable integration contracts | BLOCKED |
| UXUI-09 | Product hardening | complete states, accessibility, compact/standard/wide, visual review | UXUI-03..08 | yes by surface with one integration owner | BLOCKED |
| UXUI-10 | Built-product acceptance and browser goldens | J0-J9, packaged-product evidence, accepted browser screenshots | UXUI-09 | no | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

Parallel work must keep explicit write ownership. Shared API/read-model changes integrate before dependent frontend slices; shared design primitives have one owner at a time.

## Current executable slices

### UXUI-01 — design-system + brand convergence

Acceptance:

- canonical product name is `Performance Lab`; brand assets contain no stale `AI Performance Lab` lockup;
- canonical tagline is `Measure. Compare. Decide.`;
- the built sidebar uses the real compact mark rather than a placeholder glyph;
- desktop compact `1024-1279`, standard `1280-1599` and wide `>=1600` breakpoints match the product contract;
- page typography/density behaves like an application, not a landing page;
- semantic colors, metric dimensions, status colors and reduced-motion behavior stay token-owned.

Validation:

- `npm --prefix frontend run check`
- `npm --prefix frontend run test`
- `npm --prefix frontend run build`
- browser acceptance if shell behavior changes materially

### UXUI-04A — Library/read-model contracts

Acceptance for the first slice:

- Benchmark Detail is projected by Python from canonical `EvaluationSuite`, materialized dataset and evaluator ownership;
- benchmark definition stays separate from run/result evidence;
- cases expose exact retained authored input/expected values where the dataset contract permits it;
- evaluator identity/version, metrics and evaluation rule metadata come from Python-owned evaluation semantics, not TypeScript guesses;
- missing benchmark/case IDs are typed as not found at the API boundary;
- no global evaluator weight is introduced.

Validation:

- focused application/API contract tests;
- repository `check` / `test` profile selected from blast radius;
- J7 remains residual until the frontend Benchmark Detail journey is integrated.

## Integration strategy

1. UXUI-01 and UXUI-04A run independently from the same integrated `dev` baseline.
2. UXUI-01 integrates before UXUI-02 because shell/navigation consumes the canonical shared visual system.
3. UXUI-04A integrates before Library/Settings consumers and sample-evidence pages.
4. Once UXUI-01/02 establish the shell/components, UXUI-03 and UXUI-04B may progress in parallel because they own different page trees.
5. UXUI-05 may progress alongside page convergence once its backend contracts have a single canonical owner.
6. UXUI-06/07 remain sequential because campaign planning, lifecycle and recommendation share one new bounded product contract.

Avoid stacked branches that silently depend on an unmerged red base. Ordinary UX/UI branches start from current green `dev` and target `dev`.

## Visual-target coverage

Approved standard desktop targets currently cover:

- Overview
- Find best setup / Results
- Test a model / Review frozen configuration
- Benchmark Detail
- Sample Evidence Detail
- Models
- Datasets
- Evaluators
- Evidence
- Settings / Model connections

Still required before final visual acceptance:

- Find best setup setup/planning steps
- Campaign Live
- Runs history
- Run Detail / Samples
- Case Comparison Across Candidates
- Compare compatible and incompatible states
- Failure/recovery states

## Durable documentation destinations

- `design/ux-contract.json`: durable task model, IA, surface semantics, states and journeys.
- `design/brand-kit.json`: durable brand/design-system tokens and visual rules.
- `docs/architecture.md`: only if ownership/boundaries change, especially campaign/evidence application ownership.
- `docs/features/`: only for durable shipped feature behavior needing explanation.
- `.engineering/e2e.json`: executable journey/environment-fidelity truth.
- tests/contracts: backend semantics, accessibility and browser behavior.

## Completion

This workstream is complete only when the implemented desktop product, backend read models, evidence semantics, failure/recovery behavior, accessibility, J0-J9 acceptance and built-product evidence agree with the canonical UX contract. Accepted implementation screenshots, not generated targets, become visual-regression goldens. Then update `docs/current-state.md` and delete this file by default.
