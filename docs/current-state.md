# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-23

This is the single short operational ledger for Performance Lab. Durable behavior belongs in architecture/feature/ADR/design contracts; active implementation detail belongs in bounded workstreams; Git history owns implementation history.

## Current phase

The benchmark/evidence core and the first end-to-end local UI path are integrated on `dev`. The remaining productization work is **Compare + secondary management surfaces + browser acceptance + release/build lifecycle**, while representative real-device evidence proceeds independently.

Performance Lab already supports reproducible endpoint evaluation, immutable run evidence, quality/runtime/resource measurements, compatible comparison/regression, CLI/CI operation, local UI read models, reviewed run launch, server-owned progress/cancellation and immutable Run Detail.

Primary product question remains:

> Which model/configuration works best for my workload on this device, and why?

Primary UI task model remains:

```text
Overview -> Test a model -> Live Run -> Run Detail
                    \-> Runs -> Compare

Library / Settings -> secondary expert capability
```

## Integrated UI/product baseline

Merged on `dev`:

- `UIA-001` — versioned UI read API, scenario catalog, preflight and frozen execution preview;
- `UIK-001` — executable semantic tokens/primitives and responsive application shell;
- `UI-001` — tested-model Overview;
- `UI-002` — Runs list, immutable Run Detail and read-only routing;
- `UI-003` — Model -> Scenario -> Test -> Review with server-validated frozen configuration;
- `UIA-002` — bounded server-owned run jobs, progress, cancellation and restart/interruption semantics;
- `UI-004` — reconnectable Live Run and explicit cancellation/recovery;
- `UIA-003` — executable loopback UI composition root and Vite API proxy.

These slices were merged with Python 3.12/3.13, frontend check/test/build and deterministic Product E2E evidence on their respective heads. That evidence does not prove representative hardware/model performance or browser-level J1-J6 acceptance.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [UI productization](workstreams/ui-productization.md) | ACTIVE | `UI-005 Compare` and `UI-006 Library / Settings` can proceed in parallel |
| Representative model/device evidence | READY | first real Local LLM Server run + retained run bundle |
| Repo-template-sw 0.5 alignment | ACTIVE in current change | governance/design contracts and bounded documentation; release lifecycle remains truthful/pending |

## Immediate next block

1. Build **UI-005 Compare** compatibility-first: identity/reasons before valid dimension-specific deltas; invalid deltas stay absent.
2. Build **UI-006 Library / Settings** in parallel as secondary surfaces backed by canonical Python owners.
3. Add focused **Playwright J1-J6** browser acceptance only after UI-005/UI-006 complete the critical product surface.
4. Implement **REL-UI-001**: unique build identity, source/dirty metadata, manifest/checksum, build delta, bounded artifact retention, built-product smoke/stop/clean and zero-residue evidence.
5. Run representative Local LLM Server/device evidence in parallel; do not block UI work on hardware access.
6. Start Local LLM Server evaluation deprecation only after replacement parity and cross-product evidence are complete.

## Repository-template alignment status

Aligned or being enforced in the current change:

- repo-template-sw baseline metadata and documentation budgets;
- task-routed root/scoped `AGENTS.md` model;
- `product-ui` UX contract 0.5 decision order, motion/graphics rules and motion tokens;
- security/trust-boundary policy and evidence-oriented PR template;
- bounded `current-state` and active-workstream documentation.

Still intentionally **not claimed complete**:

- `REL-UI-001` build identity, immutable artifact lifecycle and build-delta requirements;
- full repository-health verifier adoption that depends on those guarantees;
- browser Playwright/accessibility/usability evidence;
- representative model/device evidence.

## Integration lines and drift

- `dev` is the implementation/integration line; feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately after evidence.
- At this review, `dev` is one docs-only commit behind `main` (`#52`, use-case-driven README positioning). Reconcile that drift before the next deliberate `dev` -> `main` promotion.

## Evidence still required before broad release claims

- representative resident-model run(s) with retained fingerprints/bundles;
- controlled repeated/load evidence on known hardware;
- browser J1-J6, recovery and cleanup evidence;
- automated/manual accessibility evidence toward WCAG 2.2 AA;
- compact/standard/wide adaptive-layout evidence;
- release build identity/artifact lifecycle evidence;
- human acceptance of hierarchy and progressive disclosure.
