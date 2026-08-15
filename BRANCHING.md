# Branching and integration policy

Status: active
Last reviewed: 2026-08-15

The repository uses a lightweight two-line policy once concurrent implementation begins.

- `main` is stable and release-oriented.
- `dev` is the normal integration branch for feature, fix, dependency, documentation and UX work.
- Feature branches are short-lived and should use a descriptive prefix such as `feat/`, `fix/`, `docs/` or `agent/`.
- Pull requests should normally target `dev`; promotion from a validated `dev` to `main` is deliberate.
- Until `dev` is created/protected, bootstrap foundation changes may land directly on `main`, but this exception ends when parallel lanes start.

## Parallel work

The workstream IDs in `docs/implementation-plan.md` define ownership boundaries. Concurrent branches should avoid modifying another lane's implementation unless the shared contract change is coordinated first.

When a shared domain contract changes:

1. update the owning FND contract and tests;
2. record material dependency/acceptance changes in `docs/plan-changelog.md`;
3. rebase/update dependent workstreams;
4. validate the complete integration before merging subsequent dependent changes.

## Merge readiness

A branch is merge-ready when the relevant Definition of Done is satisfied and:

```bash
python scripts/validate.py
```

passes from a clean environment. A green feature branch is not release evidence if required real-endpoint or representative-device evidence is still deferred.
