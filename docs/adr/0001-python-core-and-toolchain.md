# ADR 0001 — Python core and validation toolchain

Status: accepted
Date: 2026-08-15

## Context

AI Performance Lab needs a runtime-agnostic core that can integrate with HTTP inference endpoints, dataset/evaluation tooling and Python-first benchmark ecosystems without embedding a model runtime. The repository also needs a low-friction local/CI validation path before adapter, dataset, telemetry and storage work splits into parallel lanes.

## Decision

Use Python 3.12+ for the initial core package.

The foundation uses:

- `src/` package layout;
- PEP 621 metadata in `pyproject.toml`;
- setuptools as the build backend;
- Pydantic v2 for strict typed domain serialization;
- Ruff for formatting/linting;
- mypy strict mode for static typing;
- pytest for deterministic tests;
- one repository gate, `python scripts/validate.py`, used locally and in GitHub Actions.

The core package must remain free of model-runtime dependencies. HTTP clients, storage drivers, CLI/UI libraries and external evaluation frameworks are added only in their owning workstreams.

MIT is the initial repository license.

## Alternatives considered

### Kotlin/JVM

Strong typing and good fit with the Android harness ecosystem, but weaker fit with the Python evaluation/benchmark ecosystem and higher friction for dataset/benchmark integrations.

### TypeScript/Node

Good control-plane/UI ecosystem, but less natural for benchmark/data-science integrations and numerical evaluation tooling.

### Python with a large framework from day one

Fast to bootstrap, but would make transport, persistence or web process choices leak into the core before their boundaries are proven.

## Consequences

Positive:

- evaluation libraries and dataset tooling are easy to integrate later;
- the domain layer stays lightweight and independently testable;
- local and CI validation use the same command;
- adapters and storage can evolve behind typed boundaries.

Negative:

- Python type safety depends on runtime validation plus static tooling rather than the compiler alone;
- exact dependency locking is still required before a release artifact is claimed reproducible;
- CPU-bound distributed execution may eventually require worker/process architecture outside the core.

## Validation / revisit trigger

Validate the choice by completing M0-M3 without transport/storage concerns leaking into domain models. Revisit only if Python becomes the limiting factor for the control plane itself, not merely because a specific inference runtime is implemented in another language.
