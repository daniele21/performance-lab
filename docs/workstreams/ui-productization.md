# Performance Lab UI productization

Status: active
Owner: Performance Lab product UI
Canonical scope: product.ui-productization
Last reviewed: 2026-08-17

## Goal

Turn the existing benchmark/evidence engine into the primary local benchmark/evaluation product: users can discover tested models, create and monitor runs, inspect evidence, compare compatible runs and make workload/device decisions without falling back to CLI-only workflows.

This workstream implements ADR 0004: Performance Lab becomes the benchmark/evaluation product owner; Local LLM Server remains the serving/runtime control plane.

## Non-goals

- moving model loading/runtime lifecycle into Performance Lab;
- making Local LLM Server a dependency of generic endpoint evaluation;
- inventing a universal opaque model score;
- duplicating benchmark semantics in TypeScript;
- removing Local LLM Server evaluation before replacement parity is proven;
- turning the local UI into a cloud service.

## Invariants

1. Python domain/application code owns benchmark semantics, comparability, regression and persistence.
2. The frontend consumes versioned application contracts; it does not read SQLite directly.
3. Unknown/unavailable/partial evidence remains visible and typed.
4. Quality, runtime and resources remain separate dimensions.
5. Any "best" or ranking UI is scoped to an explicit compatible cohort, metric, workload and device context.
6. Local UI binds to loopback by default; no implicit remote processing.
7. Run jobs, browser sessions, ports, temp files and failure evidence are bounded and cleaned on success/failure/cancel/interrupt.
8. Mockups are visual references, not behavioral truth.

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

The UI adapter is an infrastructure boundary. Core domain packages remain framework-independent. The initial implementation should use the smallest ASGI/OpenAPI stack that preserves lifecycle and typed-contract requirements; FastAPI is the preferred candidate because the project already uses Pydantic contracts, but its addition must be isolated to the UI extra/composition root rather than becoming a domain dependency.

Frontend baseline: React + TypeScript + Vite, pinned Node/package-manager versions and committed lockfile. Add component/chart/state libraries only after an explicit dependency review demonstrates they reduce more complexity than they introduce.

## Product surfaces

- **Overview** — tested-model inventory, recent runs and cohort-scoped leaders.
- **New Evaluation** — endpoint/model/suite/sample/generation/performance/telemetry configuration and frozen execution preview.
- **Live Run** — progress, content-safe activity, telemetry, cancellation and recovery.
- **Results / Run Detail** — immutable fingerprint, aggregate metrics, sample/evidence views and bundle integrity.
- **Compare** — baseline/candidate identity diff, dimension-specific comparability, deltas and regression verdicts.
- **Suites** — current bundled/custom suite identities and mappings.
- **Baselines / Policies** — explicit immutable baselines and versioned threshold policies.
- **Targets / Devices** — endpoint capability/identity context, never runtime ownership.

## Work DAG

| Task | State | Depends on | Acceptance |
| --- | --- | --- | --- |
| UIF-001 engineering/UI foundation | READY | — | pinned frontend toolchain + lockfile; repo-template command mapping extended; frontend build/check/test commands deterministic |
| UIA-001 versioned local application API | PLANNED | UIF-001 | read/write contracts for targets, runs, suites, comparisons and policies; no direct UI-to-SQLite access |
| UIA-002 run lifecycle + progress | PLANNED | UIA-001 | bounded job ownership, SSE progress, cancellation, terminal recovery and restart semantics |
| UIK-001 design tokens + primitives | PLANNED | UIF-001 | semantic tokens from visual reference, responsive shell, WCAG 2.2 AA focus/keyboard/contrast baseline |
| UI-001 Overview / tested models | PLANNED | UIA-001, UIK-001 | real stored runs only; cohort filters; no fabricated ranking |
| UI-002 Run history + Run Detail | PLANNED | UIA-001, UIK-001 | fingerprint/evidence/bundle integrity and typed unavailable states visible |
| UI-003 New Evaluation | PLANNED | UIA-001, UIK-001 | every control maps to supported backend config; execution preview matches frozen input |
| UI-004 Live Run | PLANNED | UIA-002, UI-003 | progress + telemetry + cancel; failure/retry leaves system usable and owned resources released |
| UI-005 Compare / regression | PLANNED | UI-002 | dimension-specific comparability, identity diff, PASS/FAIL/NOT_COMPARABLE/NOT_EVALUATED preserved |
| UI-006 Suites / Baselines / Targets | PLANNED | UIA-001, UIK-001 | management/inspection surfaces use existing canonical owners rather than frontend state |
| E2E-UI-001 browser acceptance | PLANNED | UI-001..006 | small Playwright gate for critical user journeys with bounded failure artifacts + zero residue |
| MIG-001 Local LLM evaluation parity map | PLANNED | UI-003, UI-004, UI-005 | inventory each LLS evaluation workflow as migrate / retain-operational / intentionally drop |
| MIG-002 replacement + deprecation | PLANNED | MIG-001, E2E-UI-001 | LLS points evaluation users to Performance Lab; useful history/data policy resolved |
| MIG-003 remove redundant LLS evaluation | PLANNED | MIG-002 | no required consumer remains; cross-repo E2E + real-runtime smoke green before removal |
| REL-UI-001 built-product lifecycle | PLANNED | E2E-UI-001 | build identity, smoke, stop/clean, bounded artifacts and no orphan listener/browser/temp state |

Parallel intent after UIF-001:

```text
                 UIF-001
                /       \
          UIA-001       UIK-001
          /  |  \        / | \
    UIA-002 UI-001 UI-002  UI-003
       |        \    |     /
     UI-004       UI-005
          \       /
          E2E-UI-001
               |
           MIG-001
               |
           MIG-002
               |
           MIG-003

UI-006 can proceed alongside UI-001..005 once UIA-001 + UIK-001 are stable.
```

## Contract/read-model requirements

The first API slice must support stable UI-shaped **read models** without changing domain ownership. At minimum:

- target summary + capability/identity availability;
- run list with explicit filters and pagination;
- run detail with fingerprint, scores, measurements and evidence metadata;
- tested-model projection derived from run evidence with its grouping/cohort identity exposed;
- comparison projection with compatibility reasons before metric deltas;
- suite/policy/baseline summaries;
- content-safe live run state/events.

Aggregation must never merge results whose dataset/evaluator/protocol/hardware requirements make the displayed metric incomparable.

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
- bounded SSE/client buffers and bounded UI failure traces.

## Critical browser journeys

Playwright remains intentionally small:

1. create deterministic evaluation -> live progress -> completed Run Detail;
2. compare two compatible runs -> expected deltas/regression verdict;
3. compare incompatible runs -> `NOT_COMPARABLE` is foregrounded and invalid deltas are absent;
4. cancel an active run -> resources released -> next run succeeds;
5. endpoint/model failure -> actionable typed error -> retry/recovery works.

Component/integration tests own lower-level UI behavior; E2E is not a replacement for them.

## Validation / Definition of Done

A UI slice may reach DONE only when its applicable path is complete:

`CODE -> INTEGRATION -> FAILURE -> RESOURCE -> OPERATIONS -> OBSERVABILITY -> EVIDENCE -> PRODUCT`

Final productization acceptance requires:

- frontend/backend static checks and unit/component tests;
- Python 3.12/3.13 core validation remains green;
- Playwright critical journeys green on the built local surface;
- cancellation/restart/cleanup evidence green;
- exact run fingerprints and comparison semantics match CLI/CI for the same stored evidence;
- no unbounded UI/process artifact growth;
- representative Local LLM Server smoke confirms the public integration path;
- Local LLM evaluation is not removed until MIG-003 gates are satisfied.

## Durable destinations after completion

Transfer stable knowledge to:

- `docs/architecture.md` — final UI/API ownership and runtime topology;
- `docs/features/` — shipped user workflows only where explanation is needed;
- `docs/adr/0004-performance-lab-owns-evaluation-product.md` — ownership decision;
- `.engineering/commands.json` — canonical executable operations;
- scoped `AGENTS.md` only if the frontend subtree gains non-obvious local invariants.

Delete this workstream after all active work is complete and durable knowledge has moved to its canonical owners, per repo-template-sw lifecycle rules.
