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

Primary product question:

> For this use case on this device, which available model/configuration gives me the best evidence-backed trade-off, and why?

The use case determines the relevant capability/evaluation evidence; regression is one downstream use of the same evidence rather than the product's primary framing.

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
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 READY-EVIDENCE-BLOCKED | freeze legacy dataset/history policy and run replacement path on a representative real runtime before deprecation/removal |

MIG-001 confirmed that Local LLM Server still owns a complete evaluation subsystem: test-set/scoring contracts, built-in/custom datasets, resident evaluation execution, history/comparison APIs and evaluation UI. Those are migration candidates. Runtime identity, `/status`, serving, residency/resource/reclamation evidence and provider-observed metrics remain Local LLM Server responsibilities and must not move into Performance Lab.

The frozen LLS `general-purpose@1.0.0` evaluation set is a temporary migration dependency because the active LLS correctness evidence campaign still requires EV-3 real-device runs on that exact identity. MIG-003 removal is therefore correctly blocked until those results and the Performance Lab cross-repo replacement smoke exist.

## Repository-template alignment status

Repo-local `repo-template-sw` 0.5 contracts are enforced for documentation budgets, agent context, product experience, repository health and the built-product lifecycle. `.engineering/commands.json` is the canonical command map and the strict operations verifier is active.

Still not interchangeable with repository-local compliance:

- representative hardware/model evidence is required before device/performance/thermal/resource claims;
- human usability acceptance may still be required for claims that automated browser checks cannot establish;
- `dev` branch protection/required checks are repository-administration settings and cannot be configured through the currently exposed GitHub connector.

## Integration lines and drift

- `dev` is the implementation/integration line; feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately after evidence.
- this branch reconciles the use-case-first positioning introduced by main-only PR #52 into the current `dev` README without restoring obsolete foundation/status text. After merge, `main` will remain behind `dev` but will no longer own unique product-positioning truth that could be lost on promotion.

## Evidence still required before broad performance claims

- representative resident-model run(s) with retained fingerprints/bundles;
- controlled repeated/load evidence on known hardware;
- representative compatible/incompatible and regression evidence where the claim depends on it;
- real identity/telemetry validation for supported device/runtime combinations;
- cross-repository replacement evidence before redundant LLS evaluation paths are removed;
- human acceptance when hierarchy/progressive-disclosure usability is part of the release claim.
