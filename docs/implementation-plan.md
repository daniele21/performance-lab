# Implementation planning

Status: redirected
Document type: planning-router
Owner: repository
Canonical scope: planning.routing
Read when: deciding which active implementation plan owns current work
Last reviewed: 2026-08-17

The original bootstrap task decomposition in this file is complete enough that keeping its full task registry active would duplicate current-state and workstream truth. Git history preserves that implementation history.

## Current target

Performance Lab remains an independent, hardware-aware evaluation and benchmarking layer for inference endpoints. The evaluated unit is a complete execution fingerprint; quality, runtime performance and resources remain separate dimensions; compatibility is checked before deltas or regression decisions.

ADR 0004 establishes the product boundary:

- Performance Lab owns benchmark/evaluation configuration, execution, history, evidence, comparison, baseline/regression and their UX.
- Local LLM Server owns model serving/runtime lifecycle, resource policy, inference, runtime identity and dynamic status.

## Active implementation plan

The active detailed plan is:

- [`workstreams/ui-productization.md`](workstreams/ui-productization.md) — local product UI, versioned application API, run lifecycle, Playwright acceptance and staged migration of Local LLM Server evaluation ownership.

Live status and the immediate next task belong in [`current-state.md`](current-state.md).

## Durable specifications

- [`architecture.md`](architecture.md) — dependency/ownership boundaries.
- [`evaluation-and-benchmarking.md`](evaluation-and-benchmarking.md) — suites/evaluator/performance semantics.
- [`telemetry.md`](telemetry.md) — telemetry/provenance semantics.
- [`output-and-evidence-reference.md`](output-and-evidence-reference.md) — persisted/exported evidence.
- [`adr/0004-performance-lab-owns-evaluation-product.md`](adr/0004-performance-lab-owns-evaluation-product.md) — evaluation-product ownership.

New implementation efforts should use a bounded `docs/workstreams/<name>.md` DAG rather than re-expanding this repository-wide task registry. Completed workstreams are removed after durable knowledge is transferred, following the repo-template-sw documentation lifecycle.
