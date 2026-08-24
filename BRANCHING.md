# Branching and integration policy

Status: active
Last reviewed: 2026-08-24

Performance Lab uses a lightweight two-line policy for parallel implementation.

- `main` is stable/release-oriented.
- `dev` is the canonical integration branch for feature, fix, dependency, documentation and UX work.
- Ordinary branches start from the latest green `dev` and target `dev`.
- Use short-lived descriptive prefixes such as `feat/`, `fix/`, `docs/`, `chore/` or `agent/`.
- Promotion from validated `dev` to `main` is deliberate and should not be confused with merging an ordinary feature branch.

## Parallel work

Parallelism is defined by the active bounded workstream(s) under `docs/workstreams/`, not by historical bootstrap task IDs.

Parallel branches are safe when:

- ownership/write boundaries do not conflict; or
- a shared contract change has an explicit integration point and lands before dependent slices consume it.

When a shared domain/application/design contract changes:

1. update the canonical owner and focused tests first;
2. update the active workstream only if dependencies/acceptance materially change;
3. rebase/update dependent branches on the new integration contract;
4. validate the complete shared boundary before merging dependent behavior.

Current high-value lanes are listed in [`docs/current-state.md`](docs/current-state.md) and routed through [`docs/workstreams/README.md`](docs/workstreams/README.md). Do not preserve branch lists in this policy; branches are ephemeral and Git already records them.

## Merge readiness

A branch is merge-ready when:

- applicable Definition of Done / workstream acceptance criteria are satisfied;
- the relevant `.engineering/commands.json` validation gates pass;
- repository-health checks pass;
- Browser Acceptance and/or Built Product pass when the changed scope reaches those boundaries;
- exact evidence is recorded in the PR without upgrading unexecuted hardware/accessibility/usability claims to PASS;
- owned processes/listeners/temp state are cleaned for any lifecycle work.

`dev` branch protection should require the applicable Repository Validation, Repository Health, Browser Acceptance and Built Product checks once repository settings are configured. The branch currently relies on review/CI convention rather than protected required-status enforcement; enabling protection is repository administration work, not an application-code workaround.

## Promotion to main

Before `dev` -> `main` promotion:

- reconcile any commits that landed directly on `main` so neither line silently drops product/documentation truth;
- require the applicable release/build lifecycle evidence;
- preserve immutable run/build evidence and source identity where the release claim depends on it;
- keep representative device/model evidence explicitly pending unless it was actually executed.
