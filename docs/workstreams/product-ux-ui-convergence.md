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
| UXUI-00 | Stabilize and merge the UX/discovery baseline, including Browser Acceptance | PR #65; shared form semantics; current UX contracts/targets | — | no | ACTIVE |
| UXUI-01 | Design-system + brand convergence | `frontend/src/design/`, shared visual primitives/assets | UXUI-00 | yes, with UXUI-03A/04A after integration | BLOCKED |
| UXUI-02 | App shell + canonical IA/adaptive desktop navigation | `AppShell`, navigation/routing, shell CSS/tests | UXUI-01 | no | BLOCKED |
| UXUI-03 | Manual journey convergence: connect/discover -> scenario -> configure -> frozen review -> Live Run -> Run Detail | test-model/live-run/run-detail pages and direct API consumers | UXUI-01, UXUI-02 | yes, separate from Library contracts | BLOCKED |
| UXUI-04A | Library/read-model contracts for Models, Benchmarks, Datasets, Evaluators, Evidence | Python application read models/queries/API + contract tests | UXUI-00 | yes | BLOCKED |
| UXUI-04B | Library + Settings UI convergence | library/settings pages and API client types | UXUI-01, UXUI-02, UXUI-04A | yes, separate from manual journey | BLOCKED |
| UXUI-05 | Benchmark/sample evidence drill-down | benchmark detail, run samples, sample evidence projections/pages | UXUI-04A | yes, with UXUI-03/04B where write boundaries do not overlap | BLOCKED |
| UXUI-06 | Find best setup planning: use case -> candidates -> config search -> benchmark plan -> estimate | campaign planning domain/application/API + page flow | UXUI-04A, UXUI-05 contracts as needed | no | BLOCKED |
| UXUI-07 | Campaign lifecycle + results/recommendation | campaign persistence/orchestration/read models; live/results UI | UXUI-06 | no | BLOCKED |
| UXUI-08 | Same-case cross-candidate comparison | comparison application read models + case comparison UI | UXUI-05, UXUI-07 | yes, after stable integration contracts | BLOCKED |
| UXUI-09 | Product hardening | complete states, accessibility, compact/standard/wide, visual review | UXUI-03..08 | yes by surface with one integration owner | BLOCKED |
| UXUI-10 | Built-product acceptance and browser goldens | J0-J9, packaged-product evidence, accepted browser screenshots | UXUI-09 | no | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

Parallel work must keep explicit write ownership. Shared API/read-model changes integrate before dependent frontend slices; shared design primitives have one owner at a time.

## Current executable slice

`UXUI-00`

Acceptance:

- PR #65 exact head passes Repository Health, Repository Validation, Browser Acceptance and Built Product.
- Form labels expose concise accessible names while descriptions are linked through `aria-describedby`.
- Approved desktop visual targets remain organized and mapped by `manifest.json`.
- PR #65 can be merged to `dev` without weakening a legitimate browser assertion.

Validation:

- `npm --prefix frontend run check`
- `npm --prefix frontend run test`
- `npm --prefix frontend run test:e2e`
- repository remote preflight on exact head

## Integration strategy

After UXUI-00 lands on green `dev`, parallelize only slices with independent ownership:

1. UXUI-01 owns shared visual primitives/tokens.
2. UXUI-04A owns new Python application/read-model contracts and tests and may progress in parallel with UXUI-01.
3. Once UXUI-01/02 establish the shell/components, UXUI-03 and UXUI-04B may progress in parallel because they own different page trees.
4. UXUI-05 may progress alongside page convergence once its backend contracts have a single canonical owner.
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