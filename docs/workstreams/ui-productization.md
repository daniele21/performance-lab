# Performance Lab UI productization

Status: active
Owner: Performance Lab product UI
Canonical scope: product.ui-productization
Last reviewed: 2026-08-17

## Goal

Turn the existing benchmark/evidence engine into the primary local benchmark/evaluation product: users can connect a model, decide what they want to learn, run a bounded evaluation, understand the evidence, compare compatible results and make workload/device decisions without falling back to CLI-only workflows.

This workstream implements ADR 0004: Performance Lab becomes the benchmark/evaluation product owner; Local LLM Server remains the serving/runtime control plane.

The product experience is governed by [`../../design/ux-contract.json`](../../design/ux-contract.json), [`../../design/brand-kit.json`](../../design/brand-kit.json) and the canonical reference views under [`../../design/reference/`](../../design/reference/).

## Product experience contract

The default UI must model **user goals, not internal benchmark architecture**.

Primary user question:

> Which model works best for my workload on this device?

Primary interaction model:

```text
Connect model
    -> choose what you want to learn
    -> configure only what is necessary
    -> run test
    -> understand results
    -> compare compatible evidence
    -> decide
```

Complexity follows progressive disclosure:

```text
essential
  -> contextual
  -> advanced
  -> expert / diagnostics
```

Dataset identities, evaluator versions, raw evidence, telemetry provenance, generation parameters and diagnostics remain available, but they must not dominate the default journey unless they are required for the user's current decision.

## Non-goals

- moving model loading/runtime lifecycle into Performance Lab;
- making Local LLM Server a dependency of generic endpoint evaluation;
- inventing a universal opaque model score;
- duplicating benchmark semantics in TypeScript;
- exposing every benchmark/domain object as a primary navigation destination;
- hiding evidence identity or comparability constraints for visual simplicity;
- removing Local LLM Server evaluation before replacement parity is proven;
- turning the local UI into a cloud service.

## Invariants

1. Python domain/application code owns benchmark semantics, comparability, regression and persistence.
2. The frontend consumes versioned application contracts; it does not read SQLite directly.
3. Unknown/unavailable/partial evidence remains visible and typed.
4. Quality, runtime and resources remain separate dimensions.
5. Any "best" or ranking UI is scoped to an explicit compatible cohort, metric, workload and device context.
6. `NOT_COMPARABLE` is a foreground decision state; invalid metric deltas are never rendered as if meaningful.
7. Local UI binds to loopback by default; no implicit remote processing.
8. Run jobs, browser sessions, ports, temp files and failure evidence are bounded and cleaned on success/failure/cancel/interrupt.
9. Mockups are reference evidence for hierarchy and interaction intent, not behavioral truth.
10. Advanced/debug surfaces never silently become required for the primary path.

## Target architecture

```text
Browser UI (TypeScript + React)
        |
        | versioned /api/v1 + SSE progress
        v
Local UI adapter (Python, loopback)
        |
        +--> application/query services
        |       +--> orchestrator
        |       +--> run store
        |       +--> comparison/regression
        |       +--> dataset/suite registry
        |
        +--> endpoint adapters
                +--> Local LLM Server
                +--> generic OpenAI-compatible endpoints
```

The UI adapter is an infrastructure boundary. Core domain packages remain framework-independent. The initial implementation should use the smallest ASGI/OpenAPI stack that preserves lifecycle and typed-contract requirements; FastAPI remains the preferred candidate because the project already uses Pydantic contracts, but its addition must be isolated to the UI extra/composition root rather than becoming a domain dependency.

Frontend baseline: React + TypeScript + Vite, pinned Node/package-manager versions and committed lockfile. The foundation owns deterministic setup/check/test/build gates; final build identity, packaging, promotion and built-product lifecycle remain deferred to `REL-UI-001`. Add component/chart/state libraries only after an explicit dependency review demonstrates they reduce more complexity than they introduce.

## Canonical information architecture

### Primary navigation

```text
Overview
Test a model
Runs
Compare
```

### Secondary navigation

```text
Library
  Test suites
  Datasets
  Baselines
  Regression policies

Settings
  Endpoints
  Devices / targets
  Advanced
```

Suites, datasets, policies, targets, devices, evaluators and telemetry remain first-class product capabilities, but they are not first-class **default navigation concepts** unless the user explicitly drills into them.

## Canonical product surfaces

### Overview

Purpose: answer "what have I tested and what should I look at next?"

Required content:

- tested-model projection derived only from stored run evidence;
- recent runs;
- explicit device/workload/cohort context;
- scoped recommendation/leader information only where comparability is valid;
- one dominant primary CTA: **Test a model**.

The tested model, not the raw run, is the primary discovery object. Runs remain the immutable evidence unit underneath.

### Test a model

Purpose: create an evaluation through a task-oriented flow rather than a benchmark-configuration form.

Canonical steps:

```text
1. Model
2. Scenario
3. Test
4. Review
```

Step 1 should prefer endpoint/model/device autodetection where trustworthy evidence exists.

Step 2 asks what the user wants to measure:

- **General capability** — balanced quality/runtime evaluation;
- **My workload** — user-owned examples/use-case evidence;
- **Performance** — latency/throughput/resource focus;
- **Regression** — compare against an explicit existing baseline.

Step 3 exposes sensible defaults first. Dataset, suite, evaluator, seed, generation, concurrency and telemetry details belong in advanced disclosure unless needed by the chosen scenario.

Step 4 freezes and previews the exact execution identity before launch.

### Live Run

Purpose: communicate progress and system state without turning the default screen into a diagnostics dashboard.

Required hierarchy:

1. run/model/scenario identity;
2. truthful progress/phase;
3. current aggregate quality/runtime/resource signals where semantically valid;
4. cancellation;
5. secondary tabs/disclosures for Activity, Telemetry and Diagnostics.

Raw logs and low-level diagnostics must not dominate normal progress monitoring.

### Runs / Run Detail

Purpose: let users understand immutable evidence and drill down only as needed.

Default summary keeps separate dimensions for:

- quality;
- speed/throughput;
- time to first token/latency;
- resource usage.

Drill-down may expose Quality, Performance, Samples and Evidence. Fingerprint, evaluator/dataset versions, hardware/runtime identity, generation parameters and bundle integrity remain explicit under Evidence/reproducibility.

### Compare

Purpose: answer "which result is better for this decision?" only after establishing whether the evidence is comparable.

Mandatory ordering:

```text
identity / compatibility
    -> compatibility verdict and reasons
    -> valid dimension-specific deltas
    -> regression verdict where applicable
```

For incompatible evidence, foreground `NOT_COMPARABLE`, explain the identity differences, suppress invalid deltas and offer recovery actions such as viewing differences or choosing another run.

### Library / Settings

Purpose: expose expert capability without competing with the primary evaluation workflow.

Library owns inspection/management of test suites, datasets, baselines and regression policies. Settings owns endpoints, device/target context and advanced product configuration. These surfaces must continue to use canonical backend owners rather than creating frontend-only benchmark semantics.

## Critical experience states

Critical surfaces must intentionally handle, where applicable:

```text
default
loading
empty
disabled
success
warning
error
offline
partial-result
not-evaluated
not-comparable
cancelled
```

Every error/blocked state should answer:

```text
what happened?
why, if known?
what remains trustworthy?
what can the user do next?
```

Color alone must never carry the critical meaning of success/failure/comparability.

## Work DAG

| Task | State | Depends on | Acceptance |
| --- | --- | --- | --- |
| UIX-001 product experience contract | DONE in UX alignment change | — | project-specific `design/ux-contract.json` + `design/brand-kit.json`; design source of truth declared; repo-template-sw `product-ui` requirements specialized |
| UIX-002 information architecture + critical journeys | DONE in UX alignment change | UIX-001 | task-model-first primary/secondary navigation; J1–J6 named; canonical product/reference surfaces defined |
| UIX-003 state model + action/progressive-disclosure hierarchy | DONE in UX alignment change | UIX-001, UIX-002 | critical states, recovery expectations, essential/contextual/advanced/expert hierarchy and canonical reference board defined |
| UIF-001 engineering/UI foundation | DONE in UX alignment change | UIX-001..003 | pinned React/TypeScript/Vite toolchain; exact Node/npm pins; committed npm lockfile; repo-template command mapping; loopback dev/preview; frontend check/test/build CI gate; existing Python 3.12/3.13 + Product E2E remain green |
| UIA-001 versioned local application API + UI read models | READY | UIF-001 | UI-shaped contracts for tested models, targets, runs, suites, comparisons, baselines/policies; no direct UI-to-SQLite access |
| UIA-002 run lifecycle + progress | PLANNED | UIA-001 | bounded job ownership, SSE progress, cancellation, terminal recovery and restart semantics |
| UIK-001 semantic design tokens + canonical primitives | READY | UIF-001, UIX-001..003 | executable tokens from `design/brand-kit.json`; canonical reusable components; responsive shell; WCAG 2.2 AA focus/keyboard/contrast baseline |
| UI-001 Overview / tested models | PLANNED | UIA-001, UIK-001 | tested-model-first overview from real stored evidence; recent runs; scoped cohort context; one dominant Test a model CTA |
| UI-002 Runs + Run Detail | PLANNED | UIA-001, UIK-001 | immutable run evidence, separate quality/runtime/resources, typed unavailable states and progressive Evidence/reproducibility drill-down |
| UI-003 Test a model | PLANNED | UIA-001, UIK-001 | Model -> Scenario -> Test -> Review flow; scenario presets/defaults; advanced disclosure; every visible control maps to supported backend config; frozen preview matches execution input |
| UI-004 Live Run + recovery | PLANNED | UIA-002, UI-003 | truthful phase/progress, summary signals, cancel, Activity/Telemetry/Diagnostics disclosure; failure/retry leaves system usable and resources released |
| UI-005 Compare / regression | PLANNED | UI-002 | compatibility-first UI; identity differences before deltas; PASS/FAIL/NOT_COMPARABLE/NOT_EVALUATED preserved; invalid deltas absent |
| UI-006 Library + Settings | PLANNED | UIA-001, UIK-001 | suites/datasets/baselines/policies/endpoints/targets exposed as secondary surfaces backed by canonical owners |
| E2E-UI-001 browser acceptance | PLANNED | UI-001..006 | Playwright gate covers required critical journeys, actionable recovery, accessibility essentials, bounded failure artifacts and zero residue |
| MIG-001 Local LLM evaluation parity map | PLANNED | UI-003, UI-004, UI-005 | inventory each LLS evaluation workflow as migrate / retain-operational / intentionally drop |
| MIG-002 replacement + deprecation | PLANNED | MIG-001, E2E-UI-001 | LLS points evaluation users to Performance Lab; useful history/data policy resolved |
| MIG-003 remove redundant LLS evaluation | PLANNED | MIG-002 | no required consumer remains; cross-repo E2E + real-runtime smoke green before removal |
| REL-UI-001 built-product lifecycle | PLANNED | E2E-UI-001 | build identity, smoke, stop/clean, bounded artifacts and no orphan listener/browser/temp state |

### UIF-001 completion evidence

The foundation is intentionally thin and leaves product semantics to downstream tasks. It establishes:

- `frontend/` React + TypeScript + Vite composition root;
- exact Node/npm pins and `package-lock.json`-backed `npm ci`;
- strict TypeScript, ESLint, Prettier and Vitest configuration;
- typed canonical primary/secondary navigation contract with a unit test preventing expert concepts from drifting into primary navigation;
- accessible placeholder application shell with visible focus and reduced-motion baseline;
- loopback-only fixed-port Vite dev/preview behavior;
- scoped `frontend/AGENTS.md` and `frontend/README.md` ownership rules;
- `.engineering/commands.json`, `doctor` and bounded clean commands;
- CI frontend lane: frozen install -> check -> test -> production build;
- same-head evidence that the new frontend lane, Python 3.12, Python 3.13 and deterministic Product E2E all pass.

`UIF-001` does **not** claim final product accessibility, visual-regression coverage, API integration, browser E2E, packaging or release-artifact lifecycle. Those remain owned by `UIK-001`, `UIA-*`, `E2E-UI-001` and `REL-UI-001` as appropriate.

### Parallel execution intent

```text
UIX-001 -> UIX-002 -> UIX-003
                    |
              UIF-001 [DONE]
                /       \
        UIA-001 [READY] UIK-001 [READY]
         /  |  \       /  |  \
   UIA-002 UI-001 UI-002  UI-003
      |        \     |      /
    UI-004        UI-005
        \          /
          E2E-UI-001
               |
           MIG-001
               |
           MIG-002
               |
           MIG-003
```

`UI-006` can proceed alongside `UI-001..005` once `UIA-001 + UIK-001` are stable.

The highest-value implementation parallelism now is:

- **backend lane:** `UIA-001 -> UIA-002`;
- **design-system lane:** `UIK-001`;
- after the first stable API + primitives slice, **read-only product lane:** `UI-001` and `UI-002` can run in parallel;
- `UI-003` can proceed in parallel once the write/config contracts needed by Test a model are explicit;
- `UI-004` depends on both lifecycle and Test a model;
- `UI-005` depends primarily on Run Detail/comparison read models.

## Contract/read-model requirements

The first API slice must support stable UI-shaped **read models** without changing domain ownership. At minimum:

- tested-model summary derived from immutable run evidence, with grouping/cohort identity exposed;
- target/endpoint summary + capability/identity availability;
- run list with explicit filters and pagination;
- run detail with fingerprint, scores, measurements and evidence metadata;
- scenario/preflight projection needed by Test a model;
- frozen execution preview matching the eventual run input;
- comparison projection with compatibility verdict/reasons before metric deltas;
- suite/dataset/policy/baseline summaries;
- content-safe live run state/events.

Aggregation must never merge results whose dataset/evaluator/protocol/hardware requirements make the displayed metric incomparable.

Frontend-friendly read models are allowed; duplicating benchmark truth or recomputing canonical comparability in TypeScript is not.

## Design-system implementation contract

`UIK-001` should establish executable ownership for the semantic system already declared in `design/`.

Minimum primitives:

```text
AppShell
Navigation
PageHeader / SectionHeader
Button / IconButton
Field / Select / Toggle / SegmentedControl
Tabs / Disclosure
Status / EvidenceState
Metric / MetricGroup / Delta
DataTable / RunTable
Progress / RunProgress
CompatibilitySummary
IdentityDiff
EmptyState / ErrorState / LoadingState
Dialog / Toast / Tooltip
```

Rules:

- reuse an existing semantic component before creating a one-off visual variant;
- avoid "dashboard = many cards" as a default composition strategy;
- use semantic tokens rather than raw palette values in product components;
- preserve keyboard/focus semantics in every primitive from first implementation, not as polish;
- support the declared desktop compact/standard/wide layout contexts without merely shrinking the same dense layout.

## Resource and failure contract

The local product process owns its listener, UI API clients and active run jobs. Initial local behavior should default to one active benchmark job per local Performance Lab process unless an explicit bounded configuration says otherwise; benchmark-internal concurrency remains a separate load-profile setting.

Define and test:

- queue/reject behavior at capacity;
- API/request timeouts;
- cancellation during warmup/sample/evaluation/publication;
- browser disconnect without cancelling server-owned work accidentally;
- graceful shutdown during active work;
- stale run recovery after process restart;
- no partial run presented as immutable completed evidence;
- bounded SSE/client buffers and bounded UI failure traces;
- recovery CTA after endpoint/model failure;
- preservation of trustworthy partial evidence without implying completion.

## Critical browser journeys

Playwright remains intentionally small and maps directly to `design/ux-contract.json`:

1. **J1** — connect/select model -> choose scenario -> review frozen config -> run -> live progress -> completed Run Detail;
2. **J2** — Overview -> tested model/workload context -> inspect the evidence supporting a scoped recommendation;
3. **J3** — compare two compatible runs -> compatibility confirmation -> expected valid deltas/regression verdict;
4. **J4** — compare incompatible runs -> `NOT_COMPARABLE` foregrounded -> reasons visible -> invalid deltas absent -> recovery choice available;
5. **J5** — endpoint/model failure -> actionable typed error -> retry -> successful recovery;
6. **J6** — cancel an active run -> resources released -> next run succeeds.

Component/integration tests own lower-level UI behavior; E2E is not a replacement for them.

## Validation / Definition of Done

A UI slice may reach DONE only when its applicable path is complete:

`TASK MODEL -> CODE -> INTEGRATION -> STATES/FAILURE -> ACCESSIBILITY -> ADAPTIVE LAYOUT -> RESOURCE -> OBSERVABILITY -> EVIDENCE -> PRODUCT`

Final productization acceptance requires:

- frontend/backend static checks and unit/component tests;
- Python 3.12/3.13 core validation remains green;
- Playwright critical journeys green on the built local surface;
- critical keyboard/focus/contrast behavior validated to WCAG 2.2 AA target;
- compact/standard/wide layouts preserve content/action priority;
- cancellation/restart/cleanup evidence green;
- exact run fingerprints and comparison semantics match CLI/CI for the same stored evidence;
- no unbounded UI/process artifact growth;
- representative Local LLM Server smoke confirms the public integration path;
- human/manual acceptance checks the task model and progressive disclosure against the canonical reference views;
- Local LLM evaluation is not removed until MIG-003 gates are satisfied.

## Immediate next block

1. Start **UIA-001 and UIK-001 in parallel**.
2. `UIA-001` defines versioned UI-shaped read models and application/API boundaries without duplicating domain semantics or reading SQLite from TypeScript.
3. `UIK-001` converts `design/brand-kit.json` and the reference hierarchy into executable semantic tokens, canonical primitives and the production responsive shell.
4. Use Overview and Runs/Run Detail as the first production slices once the first API/read-model and primitive slices are stable because they consume existing immutable evidence without introducing run-lifecycle writes.
5. Build Test a model against an explicit scenario/preflight/frozen-execution contract rather than exposing the raw run configuration object directly.
6. Add Live Run only after the server-owned lifecycle/cancellation contract is proven.
7. Implement Compare as compatibility-first from the first slice; do not retrofit `NOT_COMPARABLE` after metric charts exist.
8. Keep Library/Settings secondary throughout implementation; do not promote internal architecture back into primary navigation.

## Durable destinations after completion

Transfer stable knowledge to:

- `design/ux-contract.json` — durable experience contract and critical journeys;
- `design/brand-kit.json` — durable visual/semantic token contract;
- executable frontend design-system source — canonical component implementation after UIK-001;
- `docs/architecture.md` — final UI/API ownership and runtime topology;
- `docs/features/` — shipped user workflows only where explanation is needed;
- `docs/adr/0004-performance-lab-owns-evaluation-product.md` — ownership decision;
- `.engineering/commands.json` — canonical executable operations;
- scoped `AGENTS.md` only if the frontend subtree gains non-obvious local invariants.

Delete this workstream after all active work is complete and durable knowledge has moved to its canonical owners, per repo-template-sw lifecycle rules.
