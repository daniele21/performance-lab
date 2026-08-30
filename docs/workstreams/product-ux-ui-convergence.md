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
| UXUI-02 | App shell + canonical IA/adaptive desktop navigation | `AppShell`, navigation/routing, shell CSS/tests | UXUI-01 | no | DONE |
| UXUI-03 | Manual journey convergence: connect/discover -> scenario -> configure -> frozen review -> Live Run -> Run Detail | test-model/live-run/run-detail pages and direct API consumers | UXUI-01, UXUI-02 | yes, separate from Library contracts | DONE |
| UXUI-04A | Library/read-model contracts for Models, Benchmarks, Datasets, Evaluators, Evidence | Python application read models/queries/API + contract tests | UXUI-00 | yes, with UXUI-01 | DONE |
| UXUI-04B | Library + Settings UI convergence | library/settings pages and API client types | UXUI-01, UXUI-02, UXUI-04A | yes, separate from manual journey | DONE |
| UXUI-05 | Benchmark/sample evidence drill-down | benchmark detail, run samples, sample evidence projections/pages | UXUI-04A | yes, after shared routing/page ownership is clear | DONE |
| UXUI-06 | Find best setup planning: use case -> candidates -> config search -> benchmark plan -> estimate | campaign planning domain/application/API + page flow | UXUI-04A, UXUI-05 contracts as needed | no | READY |
| UXUI-07 | Campaign lifecycle + results/recommendation | campaign persistence/orchestration/read models; live/results UI | UXUI-06 | no | BLOCKED |
| UXUI-08 | Same-case cross-candidate comparison | comparison application read models + case comparison UI | UXUI-05, UXUI-07 | yes, after stable integration contracts | BLOCKED |
| UXUI-09 | Product hardening | complete states, accessibility, compact/standard/wide, visual review | UXUI-03..08 | yes by surface with one integration owner | BLOCKED |
| UXUI-10 | Built-product acceptance and browser goldens | J0-J9, packaged-product evidence, accepted browser screenshots | UXUI-09 | no | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

Parallel work must keep explicit write ownership. Shared API/read-model changes integrate before dependent frontend slices; shared design primitives have one owner at a time.

## Current executable slice

### UXUI-06 — Find best setup planning

Owning boundary:

- make use case the first decision and keep model + quantization as candidate identity;
- introduce backend-owned use-case/benchmark relevance and campaign-plan read models before adding browser ranking logic;
- expose candidate selection, configuration-search strategy, benchmark plan and campaign review/estimate as progressive-disclosure steps;
- permit request-level parameter search only when support/ranges are declared by the runtime contract;
- keep runtime/model-load parameters observational unless an explicit mutable runtime lifecycle exists;
- do not start campaign execution or recommendation work in this slice.

Acceptance direction:

- J0 advances from a truthfully blocked shell to an executable planning flow while remaining blocked at campaign execution until UXUI-07;
- browser UI consumes server-owned planning data and does not guess benchmark relevance, parameter ranges or candidate comparability;
- the final review freezes the intended candidate/configuration/benchmark plan before execution ownership passes to UXUI-07.

## Integrated evidence

### UXUI-01 — DONE

Integrated through PR #69. The built product uses the canonical Performance Lab mark/lockup, `Measure. Compare. Decide.` tagline, product-density typography and compact/standard/wide desktop shell breakpoints. Repository Health, Repository Validation, Browser Acceptance and Built Product passed on the integration head.

### UXUI-02 — DONE

Integrated through PR #71. The product exposes the canonical primary task hierarchy plus visually secondary Library/Settings taxonomy, preserves staged Pending destinations and legacy deep links, and has a 1536x960 browser regression for the IA. Repository Health, Repository Validation, Browser Acceptance and Built Product passed on the final merge-ref.

### UXUI-04A — DONE

Integrated through PR #70. Python owns evaluator descriptors and inspectable Benchmark Detail projections, exact authored case content is exposed only from an explicitly registered materialized dataset whose immutable snapshot matches, and `/api/v1/benchmarks` plus `/api/v1/evaluators` are available without introducing a global evaluator weight. The starter suite regression covers its 23 exact benchmark cases. Repository Health, Repository Validation, Browser Acceptance and Built Product passed on the final merge-ref.

### UXUI-04B — DONE

Integrated through PR #73. Library now uses canonical Benchmarks, Datasets, Evaluators, Baselines and Regression policies owners backed by typed API clients; Models and Evidence remain explicitly Pending rather than routing to unrelated data. Settings uses Model connections, Devices / targets and Advanced while retaining external runtime ownership and legacy deep-link compatibility. Registry loading is isolated per active Library surface. Repository Health, Repository Validation, Browser Acceptance and Built Product passed on the final merge-ref.

### UXUI-05 backend slice — integrated

Integrated through PR #72. Python exposes Run Samples and Sample Evidence read models/APIs, preserves retry attempt identity, reports retained measurements and evaluator rule metadata, and truthfully represents prompt/response/explanation absence under the current retention contract. Repository Health, Repository Validation, Browser Acceptance and Built Product passed on the final merge-ref.

### UXUI-03 — DONE

Integrated through PR #75. The existing frozen manual evaluation flow is preserved; Live Run now offers explicit reconnect recovery after transient initial read failure without launching a duplicate job, and Run Detail makes immutable evidence inspection the primary action while Compare remains secondary. The final merge-ref is validated against the already-integrated UXUI-04B baseline.

### UXUI-05 — DONE

Integrated through PR #76. Benchmark Library now drills into a dedicated definition surface with authored cases, expected output and evaluator rules without mixing execution results. Run Detail exposes contributing samples and drills into one immutable `task_id + sample_id + attempt` Sample Evidence surface with model + quantization + fingerprint identity, evaluator-owned score/rule evidence, measurement provenance and explicit `Content not retained` / `Evaluation explanation unavailable` states. J7 passes in the built-browser mocked-API environment; J8 passes both built-browser mocked-API and packaged-product `representative_virtual` evidence with the real loopback API and SQLite persistence. Campaign and cross-candidate comparison ownership remain outside this slice.

## Integration strategy

1. UXUI-01/02/03, UXUI-04A/04B and UXUI-05 are integrated shared/product-page foundations.
2. UXUI-06 is the next owner and introduces backend-owned Find best setup planning before campaign execution exists.
3. UXUI-07 follows sequentially because campaign lifecycle and recommendation share the campaign planning contract.
4. UXUI-08 follows stable sample/campaign contracts; UXUI-09/10 harden and prove the complete experience.

Avoid stacked branches that silently depend on an unmerged red base. Ordinary UX/UI branches start from current green `dev` and target `dev`; if `dev` moves, readiness is re-established on the regenerated merge-ref.

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
