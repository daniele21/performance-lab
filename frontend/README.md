# Performance Lab frontend

This directory is the browser product surface for Performance Lab.

`UIF-001` establishes the engineering boundary only. Product behavior remains owned by the Python application/domain layer and the canonical experience contract remains under [`../design/`](../design/).

## Toolchain

- Node: `frontend/.nvmrc`
- package manager: exact npm version in `package.json#packageManager`
- dependencies: exact versions plus committed `package-lock.json`
- framework: React + TypeScript + Vite
- unit test runner: Vitest
- lint: ESLint
- formatting: Prettier

## Commands

```text
npm --prefix frontend ci
npm --prefix frontend run dev
npm --prefix frontend run check
npm --prefix frontend run test
npm --prefix frontend run build
```

The development and preview servers bind to `127.0.0.1` and fail on a port collision rather than silently moving to a different port.

## Ownership boundaries

- Do not read SQLite directly from the frontend.
- Do not reimplement benchmark scoring, comparability, regression or fingerprint semantics in TypeScript.
- API/read-model contracts are introduced by `UIA-001`.
- Executable design tokens/components are introduced by `UIK-001`.
- The current shell is foundation evidence, not a shipped implementation of Overview, Runs, Test a model or Compare.
