# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-24

This is the single short operational ledger for Performance Lab. Durable behavior belongs in architecture/feature/ADR/design contracts; active implementation detail belongs in bounded workstreams; Git history owns implementation history.

## Current phase

The benchmark/evidence core and local browser product are integrated on `dev`. Compare, Library/Settings, browser acceptance and the built-product lifecycle are no longer implementation gaps. Remaining work is empirical validation on representative hardware plus evidence-gated cutover of evaluation responsibilities duplicated in Local LLM Server.

Performance Lab now supports reproducible endpoint evaluation, immutable run evidence, quality/runtime/resource measurements, compatible comparison/regression, CLI/CI operation, reviewed run launch, server-owned progress/cancellation, immutable Run Detail, secondary Library/Settings surfaces and a packaged loopback browser product.

Primary product question:

> For this use case on this device, which available model/configuration gives me the best evidence-backed trade-off, and why?

The use case determines the relevant capability/evaluation evidence; regression is one downstream use of the same evidence rather than the product's primary framing.

## Integrated product baseline

Merged on `dev`:

- `UIA-001`, `UIK-001`, `UI-001..006`, `UIA-002..003` — versioned browser/product path through Overview, Test, Live Run, Runs/Run Detail, Compare, Library and Settings;
- `REL-UI-001` — unique build/source identity, immutable artifact publication, manifest/checksum, build delta, bounded retention and built-product smoke/cleanup;
- `E2E-UI-001` — Playwright Chromium J1-J6 plus compact/wide, duplicate-ID, overflow and reduced-motion checks;
- `MIG-001` — Local LLM Server evaluation parity/ownership map;
- `MIG-002` non-hardware work — replacement/history policy fixed and Local LLM Server Studio transition notice integrated in LLS PR #149;
- main-only PR #52 use-case-first positioning reconciled into the current `dev` README without restoring stale implementation state.

The E2E/productization merge heads passed Repository Health, Repository Validation, Browser Acceptance and Built Product on the same commits. LLS PR #149 passed Ruff, Python 3.10/3.11/3.12 and Playwright E2E before merge.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Representative device evidence](workstreams/representative-device-evidence.md) | READY | first real Local LLM Server/model/device run with retained fingerprint/bundle |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 IMPLEMENTATION DONE-EVIDENCE BLOCKED / MIG-003 BLOCKED | retain LLS EV-3 + run PL replacement on real LLS endpoint, then disable/remove redundant evaluation surfaces and run cross-repo smoke |

## Evaluation migration policy

The migration no longer has an unresolved architecture, history or redirect question:

- `general-purpose@1.0.0` and existing LLS evaluation JSON stay **legacy Local LLM Server evidence** under their original identities;
- new evaluation evidence after cutover belongs to Performance Lab and uses PL-native suite/dataset/evaluator/fingerprint identities;
- no automatic import into the PL canonical run store is required for the initial migration;
- `general-purpose@1.0.0` is not relabeled as equivalent to `general-diagnostic-starter`, and cross-product comparisons are not claimed;
- exact LLS custom-test-set JSON, per-sample request/task semantics and evaluation-specific reasoning controls are not cloned without a demonstrated retained consumer;
- LLS serving, model residency, `/v1/runtime/identity`, `/status`, provider metrics and resource/hardware correctness remain LLS-owned;
- LLS PR #149 visibly directs new Studio evaluation work to Performance Lab while deliberately preserving EV-3 and legacy history behavior until the evidence gate is satisfied.

Repository-known consumers of the legacy evaluation APIs are the LLS Studio evaluation/history surfaces, their tests and the active EV-3 device-evidence workflow. The redirect requirement is now satisfied; removal is blocked by real evidence, not by missing migration design.

MIG-003 requires two post-convergence EV-3 reports, a real Performance Lab run against LLS with identity/status evidence, then a post-disable cross-repository smoke that preserves serving/runtime behavior.

## Repository-template alignment status

Repo-local `repo-template-sw` 0.5 contracts are enforced for documentation budgets, agent context, product experience, repository health and the built-product lifecycle. `.engineering/commands.json` is the canonical command map and the strict operations verifier is active.

Still outside automated repo-local compliance:

- representative hardware/model evidence is required before device/performance/thermal/resource claims;
- human usability acceptance may still be required for claims automated browser checks cannot establish;
- `dev` branch protection/required checks are repository-administration settings. Issue #61 records the exact required-check configuration because the current GitHub connector cannot write branch protection/rulesets.

## Integration lines

- `dev` is the implementation/integration line; feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately after evidence.
- PR #52 no longer contains unique product-positioning truth absent from `dev`; future `dev -> main` promotion can preserve the use-case-first framing from the current line.

## Evidence still required before broad performance or migration claims

- representative resident-model run(s) with retained fingerprints/bundles;
- controlled repeated/load evidence on known hardware;
- real identity/telemetry validation for supported device/runtime combinations;
- LLS EV-3 on the frozen legacy evaluation contract;
- a real cross-repository PL replacement run and post-disable serving/runtime smoke;
- human acceptance when hierarchy/progressive-disclosure usability is part of the release claim.
