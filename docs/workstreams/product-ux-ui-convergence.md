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
| UXUI-01 | Design-system + brand convergence | `frontend/src/design/`, shared visual primitives/assets | UXUI-00 | yes, with UXUI-04A | DONE |
| UXUI-02 | App shell + canonical IA/adaptive desktop navigation | `AppShell`, navigation/routing, shell CSS/tests | UXUI-01 | no | ACTIVE |
| UXUI-03 | Manual journey convergence: connect/discover -> scenario -> configure -> frozen review -> Live Run -> Run Detail | test-model/live-run/run-detail pages and direct API consumers | UXUI-01, UXUI-02 | yes, separate from Library contracts | BLOCKED |
| UXUI-04A | Library/read-model contracts for Models, Benchmarks, Datasets, Evaluators, Evidence | Python application read models/queries/API + contract tests | UXUI-00 | yes, with UXUI-01 | DONE |
| UXUI-04B | Library + Settings UI convergence | library/settings pages and API client types | UXUI-01, UXUI-02, UXUI-04A | yes, separate from manual journey | BLOCKED |
| UXUI-05 | Benchmark/sample evidence drill-down | benchmark detail, run samples, sample evidence projections/pages | UXUI-04A | yes, with UXUI-03/04B where write boundaries do not overlap | READY |
| UXUI-06 | Find best setup planning: use case -> candidates -> config search -> benchmark plan -> estimate | campaign planning domain/application/API + page flow | UXUI-04A, UXUI-05 contracts as needed | no | BLOCKED |
| UXUI-07 | Campaign lifecycle + results/recommendation | campaign persistence/orchestration/read models; live/results UI | UXUI-06 | no | BLOCKED |
| UXUI-08 | Same-case cross-candidate comparison | comparison application read models + case comparison UI | UXUI-05, UXUI-07 | yes, after stable integration contracts | BLOCKED |
| UXUI-09 | Product hardening | complete states, accessibility, compact/standard/wide, visual review | UXUI-03..08 | yes by surface with one integration owner | BLOCKED |
| UXUI-10 | Built-product acceptance and browser goldens | J0-J9, packaged-product evidence, accepted browser screenshots | UXUI-09 | no | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

Parallel work must keep explicit write ownership. Shared API/read-model changes integrate before dependent frontend slices; shared design primitives have one owner at a time.

## Current executable slices

### UXUI-02 — app shell + canonical IA

Acceptance:

- primary task navigation remains exactly `Overview`, `Find best setup`, `Test a model`, `Runs`, `Compare`;
- Library exposes the canonical secondary taxonomy: `Models`, `Benchmarks`, `Datasets`, `Evaluators`, `Evidence`, `Baselines`, `Regression policies`;
- Settings exposes `Model connections`, `Devices / targets`, `Evidence retention`, `Accessibility`, `Advanced`;
- canonical destinations already backed by a legacy page owner use stable aliases without breaking existing deep links;
- canonical destinations whose owning page is not implemented yet remain visible but explicitly unavailable/non-interactive instead of routing to the wrong owner;
- desktop compact/standard/wide keep secondary navigation visually subordinate to the primary task model;
- keyboard, current-page semantics and reduced-motion behavior remain intact.

Validation:

- `npm --prefix frontend run check`
- `npm --prefix frontend run test`
- `npm --prefix frontend run build`
- browser acceptance at the standard `1536 x 960` target plus existing adaptive/reduced-motion coverage
- merge-ref validation against current `dev` because UXUI-04A integrated after this branch was created

### UXUI-05 — benchmark/sample evidence drill-down

Ready boundary:

- UXUI-04A now owns inspectable Benchmark Detail and evaluator metadata in Python;
- the next backend slice must add run/sample evidence projections without moving benchmark definition into result context;
- prompt/output content remains conditional on explicit retention; absent retained content must project `Content not retained` rather than an empty value;
- evaluator rationale is evaluator-owned; absent explanation must project `Evaluation explanation unavailable`;
- J7 can become executable once Benchmark Detail is consumed by the frontend; J8 remains blocked until sample evidence read models/pages exist.

## Integrated evidence

### UXUI-01 — DONE

Integrated through PR #69. The built product now uses the canonical Performance Lab mark/lockup, `Measure. Compare. Decide.` tagline, product-density typography and the compact/standard/wide desktop shell breakpoints. Repository Health, Repository Validation, Browser Acceptance and Built Product passed on the integration head.

### UXUI-04A — DONE

Integrated through PR #70. Python now owns evaluator descriptors and inspectable Benchmark Detail projections, exact authored case content is exposed only from an explicitly registered materialized dataset whose immutable snapshot matches, and `/api/v1/benchmarks` plus `/api/v1/evaluators` are available without introducing a global evaluator weight. The starter suite regression covers its 23 exact benchmark cases. Repository Health, Repository Validation, Browser Acceptance and Built Product passed on the final merge-ref.

## Integration strategy

1. UXUI-01 and UXUI-04A are integrated.
2. UXUI-02 is the only current shared-shell owner and must integrate before page-level convergence depends on the canonical IA.
3. After UXUI-02 integrates, UXUI-03 and UXUI-04B may progress in parallel because they own different page trees.
4. UXUI-05 may progress independently on backend/sample evidence ownership now that UXUI-04A is integrated; frontend drill-down pieces must coordinate page ownership with UXUI-04B.
5. UXUI-06/07 remain sequential because campaign planning, lifecycle and recommendation share one new bounded product contract.

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
