# Performance Lab frontend

This directory is the browser product surface for Performance Lab.

Product behavior remains owned by the Python application/domain layer and the canonical experience contract remains under [`../design/`](../design/).

## Toolchain

- Node: `frontend/.nvmrc`
- package manager: exact npm version in `package.json#packageManager`
- dependencies: exact versions plus committed `package-lock.json`
- framework: React + TypeScript + Vite
- unit test runner: Vitest
- lint: ESLint
- formatting: Prettier

## Local development

The browser and UI API are separate local processes during development.

Install Python UI dependencies and start the loopback API from a versioned `StarterRunConfig` JSON:

```text
python -m pip install -e ".[ui]"
performance-lab-ui --config path/to/run-config.json
```

Then install and start the browser frontend:

```text
npm --prefix frontend ci
npm --prefix frontend run dev
```

Vite binds to `127.0.0.1:5173` with `strictPort` and proxies `/api` to the fixed local API listener at `127.0.0.1:8765`. The Python entrypoint does not expose a remote-host option.

Additional frontend gates:

```text
npm --prefix frontend run check
npm --prefix frontend run test
npm --prefix frontend run build
```

The development and preview servers bind to `127.0.0.1` and fail on a port collision rather than silently moving to a different port.

## Current product path

The integrated local flow is:

```text
Overview
  -> Test a model
      -> Model
      -> Scenario
      -> Test
      -> frozen Review
      -> Run test
      -> Live Run
      -> Run Detail

Runs -> Run Detail
```

Run launch is server-owned. Closing or refreshing the browser does not implicitly cancel active work; Live Run reconnects by job identity. Cancellation is explicit. Completed run evidence remains immutable and is addressed by run identity only after terminal publication.

Compare remains the next primary product slice. Library and Settings remain secondary expert surfaces.

## Ownership boundaries

- Do not read SQLite directly from the frontend.
- Do not reimplement benchmark scoring, comparability, regression or fingerprint semantics in TypeScript.
- Do not infer successful completion from browser state; consume lifecycle/read contracts from `/api/v1`.
- Do not treat a run job identifier as an immutable run/fingerprint identifier.
- Preserve unknown/unavailable/not-comparable evidence rather than fabricating display values.
- Keep benchmark configuration details behind progressive disclosure unless the current task requires them.

Final built-product packaging, static-asset ownership, browser/process lifecycle and release-artifact cleanup remain separate release work; Vite development behavior is not release packaging evidence.
