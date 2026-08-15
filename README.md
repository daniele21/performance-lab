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

The first product slice targets text-generation LLM endpoints, with an OpenAI-compatible adapter as the reference integration. The architecture must remain extensible to other transport adapters and, later, other AI task families such as ASR, embeddings, reranking and vision without coupling the core to one provider.

The first useful version should support:

1. endpoint registration and capability probing;
2. general-purpose and custom evaluation datasets;
3. capability scoring;
4. latency, TTFT, throughput and reliability measurements;
5. optional host/device resource telemetry;
6. immutable run storage and strict execution fingerprints;
7. compatible run comparison and regression rules;
8. CLI execution suitable for automation;
9. a lightweight local UI for configuration, progress, results and comparisons.

## Development

Requires Python 3.12+.

```bash
python -m pip install -e ".[dev]"
python scripts/validate.py
```

The validation command is the shared local/CI gate and runs formatting checks, linting, strict type checking and tests.

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

**M0 — repository and contracts in progress.** The executable Python foundation and canonical domain schemas are complete and validated. Plugin contracts and the first adapter/dataset/telemetry/storage lanes are the current implementation wave. See [`docs/current-state.md`](docs/current-state.md) for the operational ledger.

## License

MIT. See [`LICENSE`](LICENSE).
