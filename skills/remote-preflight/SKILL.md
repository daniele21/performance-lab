---
name: remote-preflight
description: Execute and close the narrowest sufficient deterministic validation through repository-owned remote automation when the current coding agent lacks an equivalent local execution environment, without delegating automatable test work to the user or running full CI by default.
---

# Remote Preflight

Use this Skill when `preflight-change` classifies one or more required deterministic gates as `REMOTE_AUTOMATED`.

The governing rules are:

> Do not turn the user into a CI runner because the current agent lacks a shell, checkout, SDK or platform toolchain.

> Do not turn every small PR into a full repository/release build. Select validation from the actual blast radius.

## 1. Confirm remote execution ownership

Read `.engineering/commands.json` and identify the remote-preflight trigger, validation-profile selector, target PR/head, canonical jobs each profile can execute, how results are surfaced, timeout/retention behavior and trust/security restrictions.

Performance Lab uses GitHub pull-request workflows as the remote execution surface: opening or synchronizing the exact-head PR triggers repository-owned checks, and a failed/cancelled exact-head job may be re-run without asking the user to execute it locally.

If no usable remote path exists for a required automatable gate, report `AUTOMATION_CAPABILITY_GAP`. If scope cannot be narrowed safely, report `VALIDATION_SCOPE_GAP` and fail safe stronger while fixing the selector.

## 2. Resolve profile

Default to the repository's `auto` selector:

- `LEAN` — docs/governance/metadata-only or cheap universal guards;
- `SCOPED` — contained implementation owner/module plus direct consumers;
- `STRONG` — cross-boundary/shared-contract/persistence/security/packaging/dependency/user-facing behavior;
- `FULL` — promotion/release, selector/global-build/dependency-inventory/toolchain changes, unknown executable paths, or explicit full validation.

The run must report selected profile and reason. Do not silently request `full` merely because it is simpler. Stronger explicit validation is allowed; weaker-than-auto is exceptional and must be justified.

## 3. Trigger exact-head validation

Verify the PR still targets the intended base, record the head SHA, trigger the declared pull-request automation by opening/updating the PR or re-run the exact-head job when retrying, and correlate results with that head SHA. Do not reuse a result from an older head after edits/rebase/base changes.

## 4. Inspect result and logs

Record selected profile, profile reason, affected scope and each required remote gate as `PASS`, `FAIL`, `PENDING` or `N/A`.

On failure, inspect the failing job/step/log; classify it as `CHANGE_REGRESSION`, `BASELINE_FAILURE`, `ENVIRONMENT`, `FLAKY`, `BASE_DRIFT` or `ASSUMPTION`; identify the owning invariant/configuration; determine whether the runner exposed a parity/scope gap; then form a falsifiable repair hypothesis before editing.

A remote failure is not permission to suppress legitimate gates or downgrade the profile to escape the failure.

## 5. Repair and retrigger autonomously

When failure is actionable and unambiguous, patch the owning cause, run any available cheap local checks/static review, refresh head/base identity and diff review, re-run profile selection, retrigger remote preflight and inspect the new exact-head result.

Do not ask the user to execute the same automatable test between repair attempts. If the same gate fails after a repair, form a new root-cause hypothesis before the next edit; involve the user only when a material product/contract decision becomes genuinely ambiguous or `REAL_ENVIRONMENT` evidence is required.

## 6. Profile quality feedback

If `FULL` runs frequently for contained changes, improve deterministic path/dependency mapping instead of adding manual labels. Conversely, if a narrower profile misses a deterministic failure in a materially affected component, strengthen the mapping so the same class escalates automatically next time.

## 7. Security requirements

Remote execution of change-branch code must remain least-privilege: trusted requesters/same-repository PRs by default, exact-head pinning, `contents: read`, no production/deployment/signing secrets in execution jobs, bounded timeouts and bounded failure-artifact retention. Use separate write-capable reporting only if required.

## 8. Output

```text
HEAD: <revision>
TARGET: <branch>@<revision>
REMOTE_TRIGGER: GitHub pull_request workflow / exact-head rerun
VALIDATION_PROFILE: LEAN|SCOPED|STRONG|FULL
PROFILE_REASON: <reason>
AFFECTED_SCOPE: <paths/components/jobs>
REMOTE_GATES:
  <gate>: PASS|FAIL|PENDING|N/A
FAILURE_CLASS: <class|N/A>
REAL_ENVIRONMENT:
  <gate>: PENDING|PASS|N/A
READINESS: AUTOMATED_PREFLIGHT_CONFIRMED|NOT_READY_FOR_AUTOMATED_PREFLIGHT
```

`AUTOMATED_PREFLIGHT_CONFIRMED` requires every deterministic automatable gate selected by the blast-radius profile to pass on the exact current head/base. It does not imply physical-device, hardware, representative-user or release evidence unless those gates also ran.
