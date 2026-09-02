---
name: preflight-change
description: Establish exact-head automated-validation readiness by resolving material ambiguity, verifying target-base freshness, reviewing the complete diff, proving durable documentation is current, selecting validation depth and E2E environment fidelity from blast radius, classifying execution capability and routing every required deterministic gate without turning the user into a test runner.
---

# Preflight Change

Use this Skill immediately before pushing, opening/updating a PR, or otherwise publishing a change for automated validation. `validate-change` owns the iterative test loop; this Skill owns final publication/readiness, documentation freshness, validation-depth selection, E2E environment-fidelity selection and execution routing.

Read `.engineering/e2e.json` when the change affects a complete workflow or a platform/device/browser/runtime/environment-dependent claim. Read `docs/README.md` when documentation ownership or README impact is not obvious.

The governing rules are:

> Validation depth follows blast radius: use the narrowest profile that proves the changed invariants.

> Code and durable documentation ship together: every affected canonical owner must describe the exact-head behavior being published.

> README identity and README usage are separate owners: preserve still-valid purpose/positioning while keeping current setup/run/configuration/public examples truthful.

> E2E environment fidelity follows the claim: use the cheapest declared automated environment that represents the material target dimensions, then leave only irreducible fidelity gaps for real-environment confirmation.

> CI should confirm locally reproducible deterministic failures when the agent has equivalent execution capability.

> An automatable deterministic gate must not be delegated to the user merely because the current agent cannot run it locally.

## 1. Resolve material ambiguity

Before claiming readiness, confirm that implementation is not resting on an unresolved material assumption. Inspect the owning contract/state/config/design source, durable docs/ADRs, direct consumers/fakes/adapters and nearby tests, plus active workstream acceptance criteria when applicable.

Ask the user only when two reasonable interpretations remain and they would materially change product behavior, public/API/protocol contracts, persisted data/migration semantics, security/trust/privacy boundaries, failure/resource/concurrency/lifecycle behavior, backward compatibility, acceptance criteria or meaningful UX. Do not ask about local naming/style/implementation choices that preserve observable semantics.

## 2. Verify the intended base

Read the intended target branch/ref again before final validation.

- Record exact target/base revision and feature head revision.
- Verify the feature is based on, reconciled with, or proven merge-compatible with the current target according to repository policy.
- Treat stacked work as conditional while parent PRs/dependencies are not integrated.
- After a base/dependency/head change, invalidate prior affected evidence and rerun it.

Do not reuse green evidence from an obsolete head/base relationship.

## 3. Review the complete diff

Inspect the whole diff against the intended base, not only the last edited files. Look for accidental/generated/private files or debug/logging residue; unrelated edits or hidden scope expansion; duplicated ownership/policy; weakened tests; stale docs/contracts; missed consumers/fakes/adapters; missing cleanup/resource bounds; compatibility/security/UX drift; and stale E2E target/environment/fidelity assumptions.

## 4. Assess documentation impact

Assess the resulting observable behavior, not filenames alone. Classify every plausible owner as `UPDATED` or `N/A`, with a short reason when impact was plausible but `N/A`:

- `README_IDENTITY` — purpose, primary audience/outcome and stable positioning;
- `README_USAGE` — prerequisites, setup/run, public configuration, CLI/API/UI usage and examples;
- `FEATURE_DOCS` — durable non-obvious shipped behavior;
- `ARCHITECTURE` — boundaries/ownership;
- `ADR` — durable rationale;
- `SECURITY_DATA` — trust/privacy/security/data lifecycle;
- `OPERATIONS` — canonical command/operational semantics;
- `PRODUCT_EXPERIENCE` — `design/*` contracts when affected;
- `CURRENT_STATE` — integrated/blocker/next repository truth.

README identity does not change merely because implementation, commands, configuration or a benchmark workflow changed. README usage must update in the same change whenever current setup/run/configuration/public examples would become incomplete, wrong or misleading. Existing feature docs update in the same change as the behavior they describe; create a new feature doc only when durable non-obvious behavior lacks a better code/API/test/architecture/operational owner.

Static docs validators can prove structure/budgets but not semantic freshness. An affected stale owner makes `DOCS_CURRENT_WITH_IMPLEMENTATION: FAIL` and blocks readiness.

## 5. Select validation depth from blast radius

Read `.engineering/commands.json` and use the project-owned selector to choose `auto -> LEAN | SCOPED | STRONG | FULL`.

- `LEAN` — docs/governance/metadata-only or cheap universal guards with no executable/product blast radius;
- `SCOPED` — contained implementation change: affected owner/module plus direct consumers/tests/lint/compile;
- `STRONG` — cross-boundary or release-sensitive change such as shared contracts, persistence/security, packaging/dependency/variant or multi-owner behavior;
- `FULL` — promotion/release, CI-selector/global build/dependency-inventory/toolchain changes, unknown executable paths, explicit full request or cases where narrowing cannot be trusted.

The selector must report profile and reason. Unknown executable paths fail safe stronger. Changes to the selector/inventory itself force `FULL`. Do not silently downgrade below `auto`; explicit stronger validation is always allowed. If a repair broadens blast radius, re-run selection.

## 6. Select E2E journey and environment fidelity

When the selected profile/claim requires E2E, read `.engineering/e2e.json`.

For each affected critical journey:

1. identify the complete outcome being claimed;
2. identify target environments and material dimensions;
3. select the smallest relevant journey subset;
4. select the cheapest declared automated environment whose fidelity is sufficient;
5. require built/package-artifact execution when distribution/package behavior is part of the claim;
6. escalate to stronger automated fidelity only when the change depends on dimensions missing from the cheaper environment;
7. preserve residual gaps and required/conditional real-environment confirmation separately.

Do not confuse execution capability with environment fidelity. A remote CI run can still be `host_or_fake`, while a physical lab may be `representative_physical`. The executor class does not upgrade the environment claim.

## 7. Classify required gates by execution capability

For every required gate, assign the execution class for the current agent/session:

- `AGENT_LOCAL` — the agent can execute it directly on the exact head;
- `REMOTE_AUTOMATED` — deterministic and automatable, but unavailable in the current agent environment;
- `REAL_ENVIRONMENT` — genuinely requires representative hardware, protected authority, external environment or manual evidence.

Typical deterministic gates include formatter/lint/typecheck, focused unit/component tests, direct-consumer/contract/integration tests, canonical `check`/`test`, build/package/smoke/E2E as selected. For E2E, report both executor class and `.engineering/e2e.json` environment/fidelity.

## 8. Execute or route deterministic validation

Run required `AGENT_LOCAL` gates on the exact head. If all selected deterministic gates are local, documentation is current and they pass, readiness may be `READY_FOR_CI`.

If required deterministic gates are `REMOTE_AUTOMATED` and semantic/base/diff/documentation plus available local gates pass, readiness is `READY_FOR_REMOTE_PREFLIGHT`. Hand off to `remote-preflight` and trigger repository-owned automation with `auto` unless stronger validation is justified.

Do not ask the user to run an automatable deterministic command solely because the agent lacks a shell/toolchain. If no local or repository-owned remote path exists, report `AUTOMATION_CAPABILITY_GAP`. Real-environment evidence may remain pending after automated validation, but blocks stronger claims that depend on it.

## 9. Diagnose failures before editing

Classify every failure before changing production code: `CHANGE_REGRESSION`, `BASELINE_FAILURE`, `ENVIRONMENT`, `FLAKY`, `BASE_DRIFT` or `ASSUMPTION`. Identify the violated invariant and owner; fix the owner and add/strengthen regression evidence at the lowest useful level.

Never weaken/delete/suppress a legitimate gate merely to make the branch green. If the same gate fails again after an attempted fix, re-examine cause, owner and assumptions before another edit. Reconsider documentation impact, selected profile and E2E fidelity after material fixes.

## 10. Check command and evidence parity

Deterministic automation should invoke project-owned canonical commands/scripts regardless of execution location. Workflow YAML may orchestrate scope detection, setup, caching and evidence, but should not secretly own divergent policy.

If remote automation finds a deterministic failure that an equivalent local environment should have found, close the parity/selection gap. If a target-environment run repeatedly discovers ordinary workflow regressions that a declared automated environment could reproduce, strengthen earlier E2E instead of normalizing final manual/device testing as the first complete-system test.

## 11. Output readiness

Report:

```text
HEAD: <revision>
TARGET: <branch>@<revision>
AMBIGUITY: PASS|FAIL
BASE_FRESHNESS: PASS|FAIL
FULL_DIFF_REVIEW: PASS|FAIL
DOCUMENTATION_IMPACT:
  README_IDENTITY: UPDATED|N/A <reason when useful>
  README_USAGE: UPDATED|N/A <reason when useful>
  FEATURE_DOCS: UPDATED|N/A <reason when useful>
  ARCHITECTURE: UPDATED|N/A <reason when useful>
  ADR: UPDATED|N/A <reason when useful>
  SECURITY_DATA: UPDATED|N/A <reason when useful>
  OPERATIONS: UPDATED|N/A <reason when useful>
  PRODUCT_EXPERIENCE: UPDATED|N/A <reason when useful>
  CURRENT_STATE: UPDATED|N/A <reason when useful>
DOCS_CURRENT_WITH_IMPLEMENTATION: PASS|FAIL
VALIDATION_PROFILE: LEAN|SCOPED|STRONG|FULL
PROFILE_REASON: <reason>
EXECUTION_CAPABILITY: local|mixed|remote-only
E2E_JOURNEYS:
  <journey>: <environment-id> / <fidelity-class> / PASS|FAIL|PENDING|N/A
E2E_RESIDUAL_GAPS:
  <journey>: <gap or N/A>
AGENT_LOCAL:
  <gate>: PASS|FAIL|N/A
REMOTE_AUTOMATED:
  <gate>: PASS|FAIL|PENDING|N/A
REAL_ENVIRONMENT:
  <gate>: PASS|PENDING|N/A
READINESS: READY_FOR_CI|READY_FOR_REMOTE_PREFLIGHT|AUTOMATED_PREFLIGHT_CONFIRMED|NOT_READY_FOR_AUTOMATED_PREFLIGHT
```

`AUTOMATED_PREFLIGHT_CONFIRMED` requires current documentation and every deterministic automatable gate selected by the blast-radius profile to pass on the exact current head/base at the required declared E2E fidelity. Any later edit, rebase/merge/replay, dependency change or material base/environment change invalidates affected evidence and requires documentation impact to be rechecked.
