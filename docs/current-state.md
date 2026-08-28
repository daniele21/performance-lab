# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-29

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

The benchmark/evidence core and local browser product are integrated on `dev`. Remaining product evidence is representative-hardware validation plus the evidence-gated cutover of evaluation responsibilities duplicated in Local LLM Server.

Primary product question:

> For this use case on this device, which available model/configuration gives me the best evidence-backed trade-off, and why?

Use case determines the relevant capability/evaluation evidence; regression is a downstream use of the same evidence.

## Integrated baseline

Merged on `dev` before the 0.8 engineering migration:

- `UIA-001`, `UIK-001`, `UI-001..006`, `UIA-002..003` — Overview, Test, Live Run, Runs/Run Detail, Compare, Library and Settings;
- `REL-UI-001` — unique build/source identity, immutable artifacts, manifest/checksum, build delta, retention and built-product smoke/cleanup;
- `E2E-UI-001` — Playwright J1-J6 plus adaptive, duplicate-ID, overflow and reduced-motion checks;
- deterministic Python Product E2E — real CLI/HTTP/orchestrator/SQLite/regression against a deterministic external inference fixture;
- `MIG-001` — LLS evaluation parity/ownership map;
- `MIG-002` non-hardware work — replacement/history policy fixed and LLS Studio transition notice integrated in PR #149;
- main-only PR #52 use-case-first positioning reconciled into `dev`.

Productization merge heads passed Repository Health, Repository Validation, Browser Acceptance and Built Product. LLS PR #149 passed Ruff, Python 3.10/3.11/3.12 and Playwright E2E.

## Engineering-standard migration

The current integration target adopts `repo-template-sw` **0.8.0** at L2 with `python`, `typescript` and `product-ui` profiles.

The migration adds:

- exact-head pre-publication readiness and material-ambiguity/base/diff checks;
- `AGENT_LOCAL` / `REMOTE_AUTOMATED` / `REAL_ENVIRONMENT` classification with no human-as-runner fallback for deterministic automation;
- automatic `LEAN` / `SCOPED` / `STRONG` / `FULL` blast-radius selection;
- `.engineering/e2e.json` environment-fidelity ownership;
- packaged J1 full-product E2E: Chromium -> built frontend -> packaged Python API -> real SQLite -> deterministic external inference fixture;
- strict E2E-fidelity verification and bounded failure evidence.

Existing strong mechanisms are preserved: native Python/npm commands, Playwright, Product E2E, package/build identity, smoke/cleanup, product-experience contracts and representative-runtime evidence.

Hosted CI/fixtures do not prove `RUNTIME-1`. Real model/runtime identity, physical memory/resources, telemetry sensor provenance, thermals and repeated-load behavior remain target-environment evidence.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Representative device evidence](workstreams/representative-device-evidence.md) | READY | first real LLS/model/device run with retained fingerprint/bundle |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 IMPLEMENTATION DONE-EVIDENCE BLOCKED / MIG-003 BLOCKED | retain EV-3 + run PL against real LLS, then remove redundant evaluation paths and smoke |

## Evaluation migration

Architecture, history and redirect decisions are settled:

- `general-purpose@1.0.0` and existing LLS evaluation JSON remain legacy LLS evidence;
- post-cutover evaluation evidence belongs to PL under PL-native identities; no automatic legacy import is required;
- `general-purpose@1.0.0` is not relabeled as `general-diagnostic-starter` or assumed comparable;
- legacy custom-test/task/reasoning semantics are not cloned without a demonstrated consumer;
- serving, residency, `/v1/runtime/identity`, `/status`, provider metrics and hardware/resource correctness remain LLS-owned;
- LLS PR #149 directs new Studio evaluation work to PL while preserving EV-3 and legacy history until the evidence gate passes.

MIG-003 requires two post-convergence EV-3 reports, a real PL run against LLS with identity/status evidence, then a post-disable cross-repository smoke preserving serving/runtime behavior.

## Integration lines

- `dev` is the integration line; ordinary feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately with `FULL` validation.
- PR #52 no longer owns product-positioning truth absent from `dev`.

## Evidence still required

- representative resident-model run(s) with retained fingerprints/bundles;
- controlled repeated/load evidence on known hardware;
- real identity/telemetry validation;
- LLS EV-3 on the frozen legacy contract;
- real cross-repository PL replacement run and post-disable serving/runtime smoke;
- human acceptance where release claims depend on usability.
