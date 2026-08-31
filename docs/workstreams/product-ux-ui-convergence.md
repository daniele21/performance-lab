# Product UX/UI convergence

Status: active
Owner: product experience / browser UI
Read when: coordinating the remaining UX/UI convergence to the built Performance Lab product

## Goal

Deliver the approved desktop experience so Performance Lab can answer with inspectable evidence: for this use case on this device, which available model + quantization + configuration is the best fit, and why?

Canonical experience truth lives in `design/ux-contract.json`, `design/brand-kit.json` and the approved targets under `design/reference/visual-targets/desktop-standard/`.

## Non-goals

- Moving model loading, unloading or serving-runtime lifecycle into Performance Lab.
- Inventing benchmark semantics, parameter ranges, evaluator explanations or recommendation scores in TypeScript.
- Treating generated design targets as browser golden screenshots.
- Expanding to mobile before desktop compact/standard/wide is complete.

## Invariants

- Primary hierarchy remains `Overview -> Find best setup -> Test a model -> Runs -> Compare`; Library and Settings are secondary.
- Quantizations are distinct model candidates, not configuration-sweep values.
- One Run is immutable evidence for one model candidate + frozen configuration; Campaign groups Runs.
- Compatibility precedes deltas, ranking and recommendations.
- Quality, performance and resources remain separate; unknown/unavailable/not-comparable are never zero.
- Aggregate results drill into retained sample/evaluator evidence when permitted.
- Browser UI consumes backend-owned read models and does not recreate domain truth.
- WCAG 2.2 AA semantics, keyboard/focus and reduced motion are acceptance requirements.

## Work graph

| ID | Work | Depends on | State |
| --- | --- | --- | --- |
| UXUI-00 | UX/discovery baseline | — | DONE |
| UXUI-01 | Design-system + brand convergence | UXUI-00 | DONE |
| UXUI-02 | App shell + canonical IA/adaptive desktop navigation | UXUI-01 | DONE |
| UXUI-03 | Manual connect/discover -> frozen review -> Live Run -> Run Detail | UXUI-01/02 | DONE |
| UXUI-04A | Library/read-model contracts | UXUI-00 | DONE |
| UXUI-04B | Library + Settings UI convergence | UXUI-01/02/04A | DONE |
| UXUI-05 | Benchmark/sample evidence drill-down | UXUI-04A | DONE |
| UXUI-06 | Find best setup planning | UXUI-04A/05 | DONE |
| UXUI-07 | Campaign lifecycle + results/recommendation | UXUI-06 | DONE |
| UXUI-08 | Same-case cross-candidate comparison | UXUI-05/07 | DONE |
| UXUI-09 | Product hardening | UXUI-03..08 | READY |
| UXUI-10 | Built-product acceptance and browser goldens | UXUI-09 | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`. Shared API/read-model changes integrate before dependent frontend slices; shared design primitives have one owner at a time.

## Current executable slice

### UXUI-09 — Product hardening

Owning boundary:

- harden the complete use-case-first, manual-run, campaign, same-case evidence and Compare journeys without changing their domain owners;
- cover loading/empty/error/reconnect/cancel/partial/not-comparable states consistently;
- verify keyboard/focus, WCAG 2.2 AA semantics, reduced motion and compact/standard/wide desktop behavior;
- verify long model ids, config digests, case content and evidence lists do not break hierarchy or navigation;
- preserve explicit unavailable/not-retained/not-comparable states instead of smoothing them into generic errors.

Acceptance direction:

- J0-J9 remain green while failure/recovery and accessibility coverage expands;
- no frontend fallback recreates Python comparison, campaign or evidence semantics;
- responsive and long-data behavior remains usable at the approved desktop breakpoints;
- remaining visual-target gaps are implementation-ready for UXUI-10 acceptance.

## Integrated foundation

UXUI-01 through UXUI-07 are integrated through the established convergence PR sequence, with Campaign lifecycle/recommendation finalized by PR #81. The built product has the canonical shell/design system, manual evaluation recovery, converged Library/Settings, inspectable benchmark/sample evidence, executable Find best setup planning and a persisted/reconnectable Campaign lifecycle with policy-backed results.

UXUI-08 adds a Python-owned same-case projection over existing Campaign/Run/sample owners. Campaign Results enumerates retained task/sample identities; opening one exact case shows model + quantization + frozen config + immutable Run/sample attempt for every candidate. Capability compatibility reuses the canonical fingerprint rules, incompatible candidates remain explicit, response retention state is never reconstructed and the case surface does not invent a winner or delta. J9 is exercised in both mocked-browser and packaged-product environments.

## Integration strategy

1. UXUI-09 hardens failure, accessibility, responsive and long-data behavior across the complete journey.
2. UXUI-10 captures built-product acceptance and accepted implementation goldens.

Ordinary UX/UI branches start from current green `dev` and target `dev`; if `dev` moves, readiness is re-established on the regenerated merge-ref.

## Visual-target gaps

Existing targets cover Overview, Find best setup / Results, Test a model / Review, Benchmark Detail, Sample Evidence, Models, Datasets, Evaluators, Evidence and Model connections.

Still required before final visual acceptance: Find best setup planning steps, Campaign Live, Runs history, Run Detail / Samples, Case Comparison Across Candidates, compatible/incompatible Compare states and failure/recovery states.

## Durable destinations

- `design/ux-contract.json`: durable task model, IA, states and journeys.
- `design/brand-kit.json`: durable design-system/brand rules.
- `docs/architecture.md` / ADR: ownership or architectural boundary changes.
- `.engineering/e2e.json`: executable journey/environment-fidelity truth.
- tests/contracts: backend semantics, accessibility and browser behavior.

## Completion

Complete only when the desktop product, backend read models, evidence semantics, failure/recovery behavior, accessibility, J0-J9 acceptance and built-product evidence agree with the UX contract. Accepted implementation screenshots, not generated targets, become visual-regression goldens; then update `docs/current-state.md` and delete this active workstream by default.
