# Performance Lab frontend

This directory contains the browser product surface for Performance Lab. Product/evidence semantics remain owned by the Python application/domain layer; the canonical experience and visual contracts live under [`../design/`](../design/).

## Toolchain

- Node: exact version from `.nvmrc`;
- package manager: exact pnpm version from `package.json#packageManager`;
- dependencies: frozen by `pnpm-lock.yaml`;
- framework: React + TypeScript + Vite;
- tests: Vitest + Playwright;
- lint/format: ESLint + Prettier.

Install dependencies from the repository root with:

```bash
corepack enable
corepack install --global pnpm@11.24.0
pnpm --dir frontend install --frozen-lockfile
```

## Commands

```text
pnpm --dir frontend run dev
pnpm --dir frontend run check
pnpm --dir frontend run test
pnpm --dir frontend run build
pnpm --dir frontend run test:e2e
```

The Vite development server binds to `127.0.0.1:5173`, proxies `/api` to the local Performance Lab API on `127.0.0.1:8765`, and fails on a port collision rather than silently moving.

For manual assembled-product testing, prefer the production build served by `performance-lab-ui`:

```bash
pnpm --dir frontend run build
uv run --extra dev --locked performance-lab-ui --config local-run.json --assets frontend/dist
```

See [`../docs/getting-started.md`](../docs/getting-started.md) for the complete checkout/environment/configuration path.

## Ownership boundaries

- Do not read SQLite directly from the frontend.
- Do not reimplement benchmark scoring, compatibility, regression or fingerprint semantics in TypeScript.
- Preserve explicit unknown/unavailable/not-comparable evidence states.
- Keep Quality, Performance and Resources separate.
- Reuse the canonical design system and semantic components before creating new patterns.
- Browser Playwright against mocked `/api` proves browser behavior, not representative runtime/device evidence.
