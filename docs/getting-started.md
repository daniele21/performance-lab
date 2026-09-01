# Getting started

Status: active
Document type: operational-guide
Owner: developer experience
Canonical scope: operations.getting-started
Read when: installing Performance Lab or running the local browser product
Last reviewed: 2026-09-01

This is the shortest supported path from a clean checkout to the current local browser product. `dev` is the canonical integration branch; `main` is release-oriented and is promoted deliberately after FULL validation.

## 1. Prerequisites

Performance Lab uses one locked local toolchain:

- `uv 0.12.5` for Python installation, dependency locking, the repository `.venv`, command execution and builds;
- Python `3.12` as the default local line from `.python-version`;
- Node `24.18.0` from `frontend/.nvmrc`;
- pnpm `11.24.0` from `frontend/package.json#packageManager`;
- `uv.lock` and `frontend/pnpm-lock.yaml` as the only dependency lockfiles.

Install `uv` and a Node version manager/Corepack before continuing. Do not create a second virtual environment and do not use `pip install -e`, npm or an alternate lockfile for repository setup.

## 2. Checkout the current product

```bash
git clone https://github.com/daniele21/performance-lab.git
cd performance-lab
git checkout dev
git pull --ff-only origin dev
```

If the repository is already cloned:

```bash
git fetch origin
git checkout dev
git pull --ff-only origin dev
```

## 3. Create the locked environments

From the repository root:

```bash
uv python install 3.12
uv sync --extra dev --locked

corepack enable
corepack install --global pnpm@11.24.0
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend exec playwright install chromium
```

`uv sync` creates and owns `.venv`. You do **not** need to activate it: canonical Python commands use `uv run --extra dev --locked ...`, which executes against the locked repository environment.

Verify the toolchain and environment:

```bash
uv run --extra dev --locked python scripts/doctor.py
```

The doctor should report the repository `.venv`, `uv.lock`, Node, pnpm and `frontend/pnpm-lock.yaml` as `OK`.

## 4. Connect an inference endpoint

The reference adapter expects an OpenAI-compatible endpoint with at least:

```text
GET  /v1/models
POST /v1/chat/completions
```

Probe the endpoint before running the UI:

```bash
uv run --extra dev --locked performance-lab probe \
  --base-url http://127.0.0.1:1235/v1/ \
  --model my-model
```

A healthy probe confirms the minimum inference path, not optional streaming, token-usage or runtime-identity capabilities.

## 5. Create a local run config

Save this as `local-run.json` and replace the endpoint/model values with the service you are testing:

```json
{
  "schema_version": 1,
  "target_id": "local-model",
  "endpoint_identity": "127.0.0.1:1235",
  "endpoint": {
    "profile_id": "local-endpoint",
    "base_url": "http://127.0.0.1:1235/v1/",
    "model_selector": "my-model"
  },
  "model_id": "my-model",
  "store_path": ".performance-lab/runs.sqlite3"
}
```

For Local LLM Server, add the optional first-party identity and telemetry blocks described in [`local-llm-server-integration.md`](local-llm-server-integration.md). The inference base URL includes `/v1/`; identity/status use the server root.

## 6. Run the built local product — recommended for manual testing

Build the same frontend artifact used by the assembled product:

```bash
pnpm --dir frontend run build
```

Serve the built frontend and Performance Lab API from one loopback-owned process:

```bash
uv run --extra dev --locked performance-lab-ui \
  --config local-run.json \
  --assets frontend/dist
```

Open:

```text
http://127.0.0.1:8765
```

Use this mode for product/UX review because it exercises the built frontend with the real local API composition instead of the Vite development server.

Stop it with `Ctrl-C`. The process owns only the loopback listener; model serving remains external.

## 7. Run development mode — optional

Use two terminals when actively changing the frontend.

Terminal 1 — Performance Lab API:

```bash
uv run --extra dev --locked performance-lab-ui \
  --config local-run.json \
  --port 8765
```

Terminal 2 — Vite:

```bash
pnpm --dir frontend run dev
```

Open:

```text
http://127.0.0.1:5173
```

Vite binds to loopback and proxies `/api` to `http://127.0.0.1:8765`. Both development servers use strict ports and fail on collision instead of silently choosing another port.

## 8. Validate the checkout

Canonical repository checks are defined in [`.engineering/commands.json`](../.engineering/commands.json). The common local gates are:

```bash
uv run --extra dev --locked python scripts/validate.py
pnpm --dir frontend run check
pnpm --dir frontend run test
pnpm --dir frontend run build
```

Complete deterministic product E2E:

```bash
uv run --extra dev --locked python -m pytest tests/e2e -v --tb=short
```

PRE_REAL browser evidence:

```bash
uv run --extra dev --locked python scripts/pre_real_e2e.py \
  --output-root build/pre-real-e2e
```

These fixture/hosted environments do not prove real model/device performance; representative runtime/device evidence remains a separate `RUNTIME-1` requirement.

## 9. Run from the CLI without the browser

A single evaluation can be started directly from the same config:

```bash
uv run --extra dev --locked performance-lab run --config local-run.json
```

The run is persisted in SQLite and exported as a portable `.plab.zip` evidence bundle. Use `--json` for machine-readable output.

To compare a baseline and candidate after two completed compatible runs:

```bash
uv run --extra dev --locked performance-lab regress \
  --store .performance-lab/runs.sqlite3 \
  --baseline-run <baseline-run-id> \
  --candidate-run <candidate-run-id> \
  --policy regression-policy.json
```

Compatibility is evaluated before thresholds or deltas.

## 10. Updating dependencies

Python dependency changes update `pyproject.toml` and `uv.lock` together. Frontend dependency changes update `frontend/package.json` and `frontend/pnpm-lock.yaml` together.

Do not hand-edit lockfiles and do not introduce a parallel requirements constraints file, `package-lock.json` or another package-manager path. Toolchain/dependency changes require the repository's FULL validation profile.

For configuration details see [`run-config-reference.md`](run-config-reference.md). For evidence outputs see [`output-and-evidence-reference.md`](output-and-evidence-reference.md). For failures see [`troubleshooting.md`](troubleshooting.md).
