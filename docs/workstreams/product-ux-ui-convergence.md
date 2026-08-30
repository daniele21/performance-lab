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
| UXUI-07 | Campaign lifecycle + results/recommendation | UXUI-06 | READY |
| UXUI-08 | Same-case cross-candidate comparison | UXUI-05/07 | BLOCKED |
| UXUI-09 | Product hardening | UXUI-03..08 | BLOCKED |
| UXUI-10 | Built-product acceptance and browser goldens | UXUI-09 | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`. Shared API/read-model changes integrate before dependent frontend slices; shared design primitives have one owner at a time.

## Current executable slice

### UXUI-07 — Campaign lifecycle + results/recommendation

Owning boundary:

- consume the deterministic frozen plan from UXUI-06 rather than rebuilding use-case, candidate or benchmark semantics;
- persist and orchestrate a bounded Campaign that groups immutable Runs without replacing Run identity;
- expose queued/running/completed/failed/cancelled lifecycle, cancellation, recovery and resource ownership;
- produce results only from compatible retained evidence and an explicit versioned decision policy;
- keep quality, runtime performance and resources separate; never introduce a universal opaque score;
- preserve external model/runtime lifecycle ownership and do not invent mutable runtime configuration.

Acceptance direction:

- `Start evaluation campaign` executes only the exact server-revalidated frozen plan/digest;
- progress/recovery are server-owned and reconnectable without duplicate ownership;
- each campaign matrix entry resolves to one model candidate + frozen configuration + immutable Run;
- compatibility and decision-policy identity appear before any recommendation or alternative ranking;
- J9 remains blocked until UXUI-08 adds same-case cross-candidate comparison.

## Integrated foundation

UXUI-01 through UXUI-06 are integrated through PRs #69, #71, #75, #70/#73, #72/#76 and #77 respectively. The current built product therefore has the canonical shell/design system, manual evaluation recovery, converged Library/Settings, inspectable benchmark/sample evidence and executable Find best setup planning.

UXUI-06 specifically adds backend-owned versioned use cases, target-scoped candidate inventory, runtime-reported parameter capabilities, starter/workload benchmark mapping, bounded planning and a deterministic frozen campaign-plan digest. Sweep strategies remain unavailable when no bounded ranges are reported. J0 is exercised in both `browser-built-mocked-api` and `packaged-product-fixture`; campaign execution/recommendation intentionally remains UXUI-07.

## Integration strategy

1. UXUI-07 makes the frozen campaign plan executable and produces policy-backed results.
2. UXUI-08 adds same-case comparison after stable campaign contracts.
3. UXUI-09/10 harden and prove the complete experience.

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
