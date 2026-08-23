# Performance Lab UI productization

Status: active
Owner: Performance Lab product UI
Canonical scope: product.ui-productization
Last reviewed: 2026-08-23

## Goal

Complete the local product experience that lets a user answer:

> Which model/configuration works best for my workload on this device, and why?

Performance Lab owns evaluation configuration, execution evidence, run history, comparison and regression UX. Serving/runtime lifecycle remains outside the product core and is owned by the connected inference service.

## Durable contracts

This workstream coordinates implementation only. Durable truth lives in:

- [`../../design/ux-contract.json`](../../design/ux-contract.json) — task model, hierarchy, states, accessibility, motion/graphics and J1-J6;
- [`../../design/brand-kit.json`](../../design/brand-kit.json) — semantic visual/motion tokens;
- [`../architecture.md`](../architecture.md) — ownership and runtime topology;
- [`../output-and-evidence-reference.md`](../output-and-evidence-reference.md) — persisted/exported evidence;
- [`../adr/0004-performance-lab-owns-evaluation-product.md`](../adr/0004-performance-lab-owns-evaluation-product.md) — product ownership boundary;
- [`.engineering/commands.json`](../../.engineering/commands.json) — executable repository operations.

Do not duplicate those contracts here.

## Product invariants

1. Default UX models user decisions, not benchmark internals.
2. Python application/domain code owns benchmark semantics, comparability, regression and persistence.
3. The frontend consumes versioned application contracts and never reads SQLite or recreates canonical comparability.
4. Quality, runtime and resources remain separate dimensions; unknown/unavailable/partial evidence stays typed.
5. Compatibility precedes metric deltas and regression verdicts; `NOT_COMPARABLE` is a foreground decision state.
6. Progressive disclosure is `essential -> contextual -> advanced -> expert/diagnostics`.
7. Local UI/API binds to loopback by default; run jobs/listeners/temp evidence have bounded ownership and cleanup.
8. Mockups/reference views guide hierarchy and interaction intent; shipped behavior comes from executable contracts/tests.
9. Real-device, accessibility, cleanup and release claims require evidence actually executed.

## Integrated baseline on `dev`

Completed and merged:

- `UIX-001..003` — experience contract, IA, critical journeys and state/progressive-disclosure model;
- `UIF-001` — React/TypeScript/Vite foundation, pinned toolchain, frontend CI and operating commands;
- `UIA-001` — read API, scenarios, preflight and frozen execution preview;
- `UIK-001` — semantic tokens/primitives and responsive shell;
- `UI-001` — tested-model Overview;
- `UI-002` — Runs, immutable Run Detail and read-only routing;
- `UI-003` — Model -> Scenario -> Test -> Review;
- `UIA-002` — server-owned run lifecycle, bounded progress, cancellation and restart/interruption semantics;
- `UI-004` — reconnectable Live Run and recovery;
- `UIA-003` — executable loopback composition root and frontend API proxy.

The integrated path is therefore:

```text
Overview
  -> Test a model
  -> Review frozen configuration
  -> launch server-owned job
  -> Live Run / reconnect / cancel
  -> immutable Run Detail

Runs -> Run Detail
```

## Remaining work DAG

| Task | State | Depends on | Acceptance |
| --- | --- | --- | --- |
| UI-005 Compare / regression | READY | UI-002 + UIA-001 | compatibility/identity first; valid dimension deltas only; regression verdict preserves PASS/FAIL/NOT_COMPARABLE/NOT_EVALUATED |
| UI-006 Library + Settings | READY | UIA-001 + UIK-001 | suites/datasets/baselines/policies/endpoints/targets remain secondary and use canonical backend owners |
| E2E-UI-001 browser acceptance | PLANNED | UI-005 + UI-006 | Playwright covers required J1-J6, recovery, bounded failure evidence and cleanup |
| MIG-001 LLS evaluation parity map | PLANNED | UI-005 | classify each Local LLM Server evaluation workflow as migrate / retain-operational / intentionally drop |
| MIG-002 replacement + deprecation | PLANNED | MIG-001 + E2E-UI-001 | route evaluation users to Performance Lab; history/data policy resolved |
| MIG-003 remove redundant LLS evaluation | PLANNED | MIG-002 | no required consumer remains; cross-repo E2E + real-runtime smoke green |
| REL-UI-001 built-product lifecycle | PLANNED | E2E-UI-001 | unique build/source identity, manifest/checksum, build delta, bounded retention, built smoke/stop/clean and zero residue |

Representative real-device/model evidence is a parallel empirical lane and does not block UI-005/UI-006.

## Parallel execution

```text
UI-005 Compare -------------------\
                                  +--> E2E-UI-001 --> REL-UI-001
UI-006 Library / Settings --------/

real Local LLM/device evidence ---------------------------> release evidence

UI-005 --> MIG-001 --> MIG-002 --> MIG-003
                    \-> waits for browser + cross-product evidence
```

Prefer UI-005 and UI-006 in parallel because they share stable read/design foundations but own separate surfaces. Do not serialize representative hardware evidence behind browser implementation.

## UI-005 acceptance

Compare must preserve this order:

```text
selected evidence identity
-> compatibility verdict + reasons
-> only valid dimension-specific deltas
-> regression verdict when applicable
-> recovery / choose another run
```

For incompatible evidence, invalid deltas are absent rather than greyed into apparent validity. Identity differences and recovery remain understandable without opening diagnostics.

## UI-006 acceptance

Library and Settings remain secondary navigation. They expose expert capability without making suite/dataset/evaluator/telemetry architecture the default task model.

Required ownership:

- Library: test suites, datasets, baselines, regression policies;
- Settings: endpoints, device/target context, advanced configuration;
- no frontend-only benchmark semantics or duplicate persistence paths.

## Browser acceptance

Keep Playwright bounded to the critical journeys declared in `design/ux-contract.json`:

- J1 connect/select -> configure -> review -> run -> progress -> result;
- J2 find tested model evidence for a workload/device context;
- J3 compatible comparison -> valid trade-offs;
- J4 incompatible comparison -> reasons visible, invalid deltas absent;
- J5 failure -> actionable recovery -> successful retry;
- J6 cancel -> resources released -> next run succeeds.

Component/integration tests remain primary for deterministic lower-level behavior.

## Release/build lifecycle gap

`REL-UI-001` is intentionally unresolved. Until it lands, `.engineering/commands.json` must continue to report build identity, immutable artifact promotion, manifest/checksum and build delta as deferred rather than claiming template compliance.

REL-UI-001 must implement at least:

- unique build ID plus source revision and dirty-state identity;
- immutable successful artifact publication after validation;
- `build-manifest.json` with SHA-256 checksum metadata;
- build delta against the previous successful comparable build;
- bounded local/CI retention;
- built-artifact smoke and deterministic stop/clean verification;
- no orphan listener/browser/temp state after success, failure, timeout, cancellation or interrupt.

## Completion gate

This workstream completes only when:

- UI-005, UI-006, E2E-UI-001 and REL-UI-001 are integrated;
- J1-J6 evidence is green on the built local surface where applicable;
- accessibility evidence supports the WCAG 2.2 AA target;
- compact/standard/wide layouts preserve information/action priority;
- cancellation/restart/cleanup behavior is proven;
- representative Local LLM Server evidence validates real identity/telemetry assumptions;
- Local LLM Server evaluation migration gates are complete or explicitly moved to their own active bounded workstream.

After completion, transfer durable shipped behavior to `design/`, architecture/features/ADR and `.engineering/commands.json`, then delete this workstream by default. Git history owns the completed plan.
