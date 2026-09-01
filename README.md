# AI Performance Lab

AI Performance Lab is a model- and runtime-agnostic evaluation product for answering one practical deployment question:

> **For my use case, which of the models available to me is the best fit for this device, and with which configuration?**

Rather than ranking models in the abstract, Performance Lab evaluates **model × configuration × device** combinations against the requirements of a specific workload. It maps the selected use case to relevant benchmarks/datasets, runs candidates through an external inference service, keeps quality/runtime/resources as separate evidence dimensions and stores reproducible evidence behind the final decision.

Performance Lab does **not** own model loading or inference-runtime lifecycle. It evaluates externally served endpoints and can optionally consume richer runtime identity/telemetry when an integration exposes it.

## Product question

> **Given my target use case, target device and available models/configurations, which combination gives me the best evidence-backed trade-off for what I actually need?**

The goal is not another generic LLM leaderboard. Recommendations must remain traceable to compatible evidence and an explicit decision policy; unavailable or non-comparable evidence is never repaired into a fake score.

## How it works

**Use case → relevant benchmarks/datasets → candidate model/configuration runs → quality + runtime + resource evidence → compatibility → evidence-backed decision**

Core principles:

- **Use case first.** Benchmark relevance comes from the workload objective.
- **Inference is external.** The lab evaluates endpoints rather than embedding a model runtime.
- **Execution identity is explicit.** Model name alone is not enough; quantization, runtime/configuration, endpoint, dataset/evaluator and hardware identity remain part of reproducible evidence when known.
- **Quality, runtime and resources stay separate.** There is no universal opaque score.
- **Compatibility comes before ranking/deltas.** Evidence is compared only where the relevant identities permit it.
- **Unknown stays unknown.** Missing identity, telemetry or retained content is never fabricated as zero.
- **Regression testing is a first-class secondary use case.** The same immutable evidence can gate model/runtime replacement changes.

## Supported inference endpoint

The current executable product targets text-generation endpoints through the OpenAI-compatible adapter. The minimum inference surface is:

```text
GET  /v1/models
POST /v1/chat/completions
```

For a non-streaming response, `choices[0].message.content` is the required model output. `model`, `finish_reason` and token usage are consumed when available; provider-specific identity/configuration fields are never guessed into the execution fingerprint.

`daniele21/local-llm-server` can additionally expose:

```text
GET /v1/runtime/identity   # stable execution identity
GET /status                # dynamic runtime telemetry
```

Those endpoints enrich first-party evidence but are not required for generic black-box evaluation. See [`docs/local-llm-server-integration.md`](docs/local-llm-server-integration.md) and [`docs/local-llm-identity-contract.md`](docs/local-llm-identity-contract.md).

## How to use locally

### 1. Use the current integration branch

`dev` is the canonical integration line; `main` is stable/release-oriented and is promoted deliberately after FULL validation.

```bash
git clone https://github.com/daniele21/performance-lab.git
cd performance-lab
git checkout dev
git pull --ff-only origin dev
```

### 2. Install the pinned toolchain

Repository development has one dependency/environment path:

- `uv 0.12.5`;
- Python `3.12` by default (`.python-version`);
- Node `24.18.0` (`frontend/.nvmrc`);
- pnpm `11.24.0` (`frontend/package.json#packageManager`);
- `uv.lock` and `frontend/pnpm-lock.yaml` are the only dependency lockfiles.

Install `uv` and Node/Corepack first, then from the repository root run:

```bash
uv python install 3.12
uv sync --extra dev --locked

corepack enable
corepack install --global pnpm@11.24.0
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend exec playwright install chromium
```

`uv` creates and owns the repository `.venv`. **Do not create/activate another virtualenv** and do not use `pip install -e`, npm or a second lockfile for repository setup. Canonical commands execute through `uv run`, so manual activation is unnecessary.

Verify the environment:

```bash
uv run --extra dev --locked python scripts/doctor.py
```

### 3. Configure the inference target

Probe the endpoint first:

```bash
uv run --extra dev --locked performance-lab probe \
  --base-url http://127.0.0.1:1235/v1/ \
  --model my-model
```

Create `local-run.json`:

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

For Local LLM Server, the same run config can add explicit identity and telemetry blocks. See [`docs/run-config-reference.md`](docs/run-config-reference.md) for all supported fields.

### 4. Run the built browser product — recommended

For manual product/UX testing, use the assembled built frontend rather than Vite:

```bash
pnpm --dir frontend run build

uv run --extra dev --locked performance-lab-ui \
  --config local-run.json \
  --assets frontend/dist
```

Open:

```text
http://127.0.0.1:8765
```

The UI and API are served by the same loopback-owned process. Stop it with `Ctrl-C`; model serving remains external.

### 5. Frontend development mode — optional

Run the API and Vite separately.

Terminal 1:

```bash
uv run --extra dev --locked performance-lab-ui \
  --config local-run.json \
  --port 8765
```

Terminal 2:

```bash
pnpm --dir frontend run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to `http://127.0.0.1:8765`; both listeners bind to loopback and use strict ports.

### 6. CLI-only evaluation — optional

```bash
uv run --extra dev --locked performance-lab run --config local-run.json
```

A completed run is persisted in SQLite and exported as a portable `.plab.zip` evidence bundle.

For the full first-run walkthrough, validation commands and regression workflow, use [`docs/getting-started.md`](docs/getting-started.md).

## Validation

Canonical commands live in [`.engineering/commands.json`](.engineering/commands.json). Common local gates are:

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

CI consumes the same `uv.lock` on Python 3.12/3.13 and the same frozen `pnpm-lock.yaml`. Toolchain/dependency changes require FULL validation.

Green hosted fixtures do not prove representative hardware/model behavior; real runtime/model/device resource and telemetry claims remain `RUNTIME-1` evidence.

## Current product surface

The integrated browser product includes:

- Overview;
- **Find best setup** use-case-first planning, campaign execution and decision results;
- **Test a model** and reconnectable Live Run;
- Runs / Run Detail with separate Quality, Performance and Resources evidence;
- Compare with compatibility-before-delta semantics;
- benchmark, sample and same-case cross-candidate evidence drill-down;
- Library surfaces for benchmarks, datasets, evaluators, baselines and regression policies;
- Settings for model connections, devices/targets and advanced product-owned configuration;
- immutable SQLite evidence, portable bundles, explicit baselines and regression policies;
- browser J0-J9 acceptance plus assembled packaged-product evidence.

The current visual system is the v0.6 **Precision Instrument** experience. Final representative-human UX acceptance and representative real-model/runtime/device evidence remain separate evidence gates; see [`docs/current-state.md`](docs/current-state.md).

## Dependency updates

Python dependency changes update `pyproject.toml` + `uv.lock`. Frontend dependency changes update `frontend/package.json` + `frontend/pnpm-lock.yaml`.

Do not hand-edit lockfiles or add parallel `requirements` constraints, `package-lock.json` or another package-manager path to work around resolution problems.

## Documentation

| Question | Canonical source |
| --- | --- |
| First local setup / run | [`docs/getting-started.md`](docs/getting-started.md) |
| Current integrated/blocked/next state | [`docs/current-state.md`](docs/current-state.md) |
| Run configuration | [`docs/run-config-reference.md`](docs/run-config-reference.md) |
| CLI commands | [`docs/cli-reference.md`](docs/cli-reference.md) |
| Evidence/store/bundles | [`docs/output-and-evidence-reference.md`](docs/output-and-evidence-reference.md) |
| Architecture/ownership | [`docs/architecture.md`](docs/architecture.md) |
| Evaluation semantics | [`docs/evaluation-and-benchmarking.md`](docs/evaluation-and-benchmarking.md) |
| Local LLM Server integration | [`docs/local-llm-server-integration.md`](docs/local-llm-server-integration.md) |
| Troubleshooting | [`docs/troubleshooting.md`](docs/troubleshooting.md) |
| Documentation index | [`docs/README.md`](docs/README.md) |

## License

MIT. See [`LICENSE`](LICENSE).
