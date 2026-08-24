# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-24

This is the single short operational ledger for Performance Lab. Durable behavior belongs in architecture/feature/ADR/design contracts; active implementation detail belongs in bounded workstreams; Git history owns implementation history.

## Current phase

The benchmark/evidence core and the local browser product are integrated on `dev`. Compare, Library/Settings, browser acceptance and the built-product lifecycle are no longer implementation gaps. The remaining work is empirical validation on representative hardware plus staged migration of overlapping Local LLM Server evaluation workflows.

Performance Lab now supports reproducible endpoint evaluation, immutable run evidence, quality/runtime/resource measurements, compatible comparison/regression, CLI/CI operation, reviewed run launch, server-owned progress/cancellation, immutable Run Detail, secondary Library/Settings surfaces and a packaged loopback browser product.

Primary product question remains:

> Which model/configuration works best for my workload on this device, and why?

Primary UI task model:

```text
Overview -> Test a model -> Live Run -> Run Detail
                    \-> Runs -> Compare

Library / Settings -> secondary expert capability
```

## Integrated product baseline

Merged on `dev`:

- `UIA-001` — versioned UI read API, scenario catalog, preflight and frozen execution preview;
- `UIK-001` — executable semantic tokens/primitives and responsive application shell;
- `UI-001..004` — Overview, Runs/Run Detail, Test Model wizard and reconnectable Live Run;
- `UIA-002..003` — server-owned run lifecycle and executable loopback composition root;
- `UI-005` — compatibility-first Compare/regression surface;
- `UI-006` — read-only Library and Settings surfaces backed by canonical Python owners;
- `REL-UI-001` — unique build/source identity, immutable artifact publication, manifest/checksum, build delta, bounded retention and built-product smoke/cleanup;
- `E2E-UI-001` — Playwright Chromium acceptance for J1-J6 plus compact/wide, duplicate-ID, overflow and reduced-motion checks.

The final E2E-UI-001 merge head passed Repository Health, Repository Validation, Browser Acceptance and Built Product on the same commit. Browser acceptance ran all seven tests successfully; Built Product executed package, smoke, atomic publication, strict operations verification, bounded history and artifact upload.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Representative device evidence](workstreams/representative-device-evidence.md) | READY | first real Local LLM Server/model/device run with retained fingerprint/bundle |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | READY | MIG-001 parity map before any deprecation/removal |

## Repository-template alignment status

Repo-local `repo-template-sw` 0.5 contracts are now enforced for documentation budgets, agent context, product experience, repository health and the built-product lifecycle. `.engineering/commands.json` is the canonical command map and the strict operations verifier is active.

Still not interchangeable with repository-local compliance:

- representative hardware/model evidence is required before device/performance/thermal/resource claims;
- human usability acceptance may still be required for claims that automated browser checks cannot establish;
- `dev` branch protection/required checks are repository-administration settings and are not configured through the currently available connector.

## Integration lines and drift

- `dev` is the implementation/integration line; feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately after evidence.
- `main` still contains docs-only commit `#52` (use-case-driven README positioning) that must be reconciled into `dev` before a deliberate `dev` -> `main` promotion.

## Evidence still required before broad performance claims

- representative resident-model run(s) with retained fingerprints/bundles;
- controlled repeated/load evidence on known hardware;
- representative compatible/incompatible and regression evidence where the claim depends on it;
- real identity/telemetry validation for supported device/runtime combinations;
- human acceptance when hierarchy/progressive-disclosure usability is part of the release claim.
