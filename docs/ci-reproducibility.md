# CI dependency reproducibility

Status: active
Document type: focused-specification
Owner: release hardening
Last reviewed: 2026-09-01

Performance Lab uses one dependency-resolution model locally and in CI:

- `uv.lock` is the canonical locked Python dependency graph for the project;
- `frontend/pnpm-lock.yaml` is the canonical frozen browser dependency graph;
- `.python-version` pins the default local Python line to 3.12;
- `frontend/.nvmrc` pins Node and `frontend/package.json#packageManager` pins pnpm.

There is no parallel pip-constraints or npm-lock ownership path. Repository setup, validation, E2E and packaging must consume these lockfiles through `uv` and `pnpm`.

## Python contract

Local setup runs `uv sync --extra dev --locked`. `uv` creates and owns the repository-local `.venv`; contributors do not need to activate it because canonical Python commands use `uv run --extra dev --locked ...`.

CI validates the same `uv.lock` on both supported Python lines, 3.12 and 3.13, by selecting the matrix interpreter and running a locked sync before repository validation. A dependency change that makes the universal lock incompatible with either supported interpreter fails CI instead of silently resolving a different graph.

`uv build` owns wheel creation. Release smoke and packaged-product E2E also use `uv venv` and `uv pip install --python ...` for their disposable artifact-test environments; those temporary environments do not become a second project dependency source.

## Frontend contract

Frontend dependencies are installed only with:

```bash
pnpm --dir frontend install --frozen-lockfile
```

CI uses the exact pnpm version declared by `frontend/package.json` and caches against `frontend/pnpm-lock.yaml`. Playwright, frontend validation, browser E2E and production builds all execute through pnpm.

## Updating dependencies

Dependency updates are intentional changes to the locked environment:

1. edit the dependency range or package metadata in `pyproject.toml` or `frontend/package.json`;
2. regenerate the owning lock with `uv lock` and/or `pnpm --dir frontend install`;
3. review the lockfile delta separately from product behavior where practical;
4. run the repository's FULL validation profile, including Python 3.12/3.13, frontend, browser and built-product gates when selected;
5. commit metadata and lockfile changes together.

Never hand-edit either lockfile and never add a second constraints/lock mechanism to work around a resolver failure. Fix the owning dependency contract instead.

## Scope

The committed locks make source-checkout development and CI resolution repeatable. Built wheel/ZIP verification, build identity, checksums, artifact retention and cross-platform distribution claims remain owned by the release artifact pipeline rather than by the dependency lockfiles alone.
