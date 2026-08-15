# Branching and integration policy

Status: active
Last reviewed: 2026-08-15

The repository uses a lightweight two-line policy for concurrent implementation.

- `main` is stable and release-oriented.
- `dev` is the canonical integration branch for feature, fix, dependency, documentation and UX work.
- Feature branches are short-lived and should use a descriptive prefix such as `feat/`, `fix/`, `docs/` or `agent/`.
- Ordinary pull requests target `dev`; promotion from a validated `dev` to `main` is deliberate.
- The direct-to-`main` bootstrap exception ended after the validated FND-001/FND-002 foundation. New parallel work starts from `dev`.

## Parallel work

The workstream IDs in `docs/implementation-plan.md` define ownership boundaries. Concurrent branches should avoid modifying another lane's implementation unless the shared contract change is coordinated first.

When a shared domain contract changes:

1. update the owning FND contract and tests;
2. record material dependency/acceptance changes in `docs/plan-changelog.md`;
3. rebase/update dependent workstreams;
4. validate the complete integration before merging subsequent dependent changes.

Prefer separate branches for the currently unlocked lanes:

```text
agent/fnd-003-plugin-contracts
agent/adp-001-openai-adapter
agent/dat-001-dataset-loading
agent/tel-001-collector-contract
agent/sto-001-run-store
```

These branches may proceed concurrently after `dev` exists. Shared contract changes should land in `dev` before dependent branches rely on them.

## Merge readiness

A branch is merge-ready when the relevant Definition of Done is satisfied and:

```bash
python scripts/validate.py
```

passes from a clean environment. A green feature branch is not release evidence if required real-endpoint or representative-device evidence is still deferred.
