# AI Performance Lab

AI Performance Lab is a model- and runtime-agnostic evaluation system for measuring whether an AI model exposed through an inference service is **good enough, fast enough and resource-efficient enough for a specific device and workload**.

The lab does not own model loading or inference runtimes. It connects to an inference endpoint, executes reproducible evaluation suites, captures quality and runtime measurements, optionally correlates them with host/device telemetry, and stores comparable run evidence.

## Product question

> Can this model/runtime/configuration replace another model for this workload on this device, without unacceptable quality, latency or resource regressions?

## Core principles

- **Inference is external.** The lab evaluates endpoints; it does not embed a model runtime in its core.
- **A model name is not a benchmark identity.** Results belong to a complete execution fingerprint: model, quantization, runtime, generation configuration, endpoint, hardware, dataset snapshot and evaluator version.
- **Quality and runtime performance are separate dimensions.** A single opaque performance score must never hide trade-offs.
- **Black-box first, instrumentation optional.** Any compatible inference endpoint can be evaluated; richer RAM/VRAM/CPU/GPU/thermal measurements are enabled through optional telemetry adapters.
- **Reproducibility before leaderboard aesthetics.** Runs are versioned, immutable and comparable only when their relevant identities are compatible.
- **Workload evaluation matters as much as public benchmarks.** General-purpose benchmarks, focused capability suites and user-provided datasets share the same execution model.
- **Regression testing is a first-class use case.** The lab must be usable interactively, from a CLI and eventually as a CI quality/performance gate.

## Initial scope

The first product slice targets text-generation LLM endpoints, with an OpenAI-compatible adapter as the reference integration. The architecture remains extensible to other transports and later AI task families such as ASR, embeddings, reranking and vision.

The first useful version should support endpoint registration/probing, general-purpose and custom datasets, capability scoring, latency/TTFT/throughput/reliability measurements, optional resource telemetry, immutable run storage, compatible comparison/regression, CLI automation and a lightweight local UI.

## Foundation

The executable foundation is Python 3.12+ with strict immutable Pydantic domain contracts. The core package intentionally has no HTTP client, database, CLI/UI or model-runtime dependency yet.

Implemented contracts include:

- target and endpoint profile identity;
- model/runtime/hardware/generation/load identity;
- evaluation suites and immutable dataset snapshots;
- execution fingerprints with deterministic SHA-256 identity;
- run/sample/measurement/score evidence;
- explicit schema versioning and unsupported-version rejection;
- dimension-specific typed comparability.

See [ADR 0001](docs/adr/0001-python-core-and-toolchain.md) and [ADR 0002](docs/adr/0002-versioned-immutable-domain-contracts.md).

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python scripts/validate.py
```

The validation command is shared by local development and GitHub Actions and runs formatting checks, lint, strict typing and tests.

## Documentation

The documentation follows progressive disclosure inspired by `android-local-llm-harness`: one canonical source owns each kind of truth.

| Question | Canonical source |
| --- | --- |
| What is integrated, blocked or next? | [`docs/current-state.md`](docs/current-state.md) |
| What exactly are we building and what are the acceptance criteria? | [`docs/implementation-plan.md`](docs/implementation-plan.md) |
| Which capability milestones come next? | [`docs/roadmap.md`](docs/roadmap.md) |
| Which tasks can run in parallel and what blocks what? | [`docs/implementation-plan.md`](docs/implementation-plan.md) |
| Why did the plan change? | [`docs/plan-changelog.md`](docs/plan-changelog.md) |
| What architecture and boundaries should implementation preserve? | [`docs/architecture.md`](docs/architecture.md) |
| How should benchmarks, datasets and metrics behave? | [`docs/evaluation-and-benchmarking.md`](docs/evaluation-and-benchmarking.md) |
| What telemetry is required and optional? | [`docs/telemetry.md`](docs/telemetry.md) |
| What is required before a task, milestone or release is considered done? | [`docs/definition-of-done.md`](docs/definition-of-done.md) |
| Where is all active documentation indexed? | [`docs/README.md`](docs/README.md) |

## Project status

**M0 — repository and contracts is in implementation/validation.** FND-001 and FND-002 are implemented; the next fan-out is FND-003 + ADP-001 + DAT-001 + TEL-001 + STO-001. See [`docs/current-state.md`](docs/current-state.md) for the live ledger.

## License

MIT. See [`LICENSE`](LICENSE).
