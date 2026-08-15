# Documentation map

Status: active
Document type: documentation-governance
Owner: repository
Canonical scope: documentation.routing
Read when: locating the canonical source for a project question or deciding where documentation changes belong
Last reviewed: 2026-08-15

Documentation uses progressive disclosure. Read only the source that owns the question, then follow focused links as needed. A fact should have one canonical owner; summaries link to that owner rather than duplicating detailed truth.

## Canonical sources

| Question | Canonical source |
| --- | --- |
| What is integrated, blocked or next? | [`current-state.md`](current-state.md) |
| What exactly are we building? | [`implementation-plan.md`](implementation-plan.md) |
| What can run in parallel and what depends on what? | [`implementation-plan.md`](implementation-plan.md) |
| Which capability milestone is next? | [`roadmap.md`](roadmap.md) |
| Why did a dependency/priority/scope change? | [`plan-changelog.md`](plan-changelog.md) |
| What architectural boundary owns this behavior? | [`architecture.md`](architecture.md) |
| How should datasets, evaluators and benchmark protocols work? | [`evaluation-and-benchmarking.md`](evaluation-and-benchmarking.md) |
| How should resource/device telemetry work? | [`telemetry.md`](telemetry.md) |
| What does Performance Lab require from `local-llm-server` and how is it configured? | [`local-llm-server-integration.md`](local-llm-server-integration.md) |
| What is required before something is considered complete? | [`definition-of-done.md`](definition-of-done.md) |
| Where should a durable architectural decision be recorded? | [`adr/README.md`](adr/README.md) |

## Active source index

### Product and delivery

- [`implementation-plan.md`](implementation-plan.md) — repository target, task IDs, dependencies, workstreams, parallel waves and acceptance criteria.
- [`current-state.md`](current-state.md) — live operational ledger and immediate next work.
- [`roadmap.md`](roadmap.md) — capability milestones and exit gates.
- [`plan-changelog.md`](plan-changelog.md) — material plan-decision history.
- [`definition-of-done.md`](definition-of-done.md) — task, milestone, merge and evidence completion rules.

### Architecture and domain behavior

- [`architecture.md`](architecture.md) — dependency direction, domain objects, inference adapter, run lifecycle, fingerprint, persistence and extension rules.
- [`evaluation-and-benchmarking.md`](evaluation-and-benchmarking.md) — dataset snapshots, sampling, evaluator semantics, performance protocols, workload suites and regression comparability.
- [`telemetry.md`](telemetry.md) — black-box/host/instrumented telemetry levels, metric provenance, sampling and resource comparison.
- [`local-llm-server-integration.md`](local-llm-server-integration.md) — OpenAI-compatible inference requirements, optional `/status` runtime evidence contract, run configuration and measurement limitations for `daniele21/local-llm-server`.
- [`adr/README.md`](adr/README.md) — durable architectural decision log and template.

## Document ownership rules

### `current-state`

Owns only current integrated status, blockers, parallel-ready work and the immediate next block. Update frequently.

### `implementation-plan`

Owns intended target, task decomposition, dependencies and acceptance criteria. Update only when the plan itself materially changes.

### `roadmap`

Owns capability-level milestones and exit gates. It should not become a branch/commit history.

### `plan-changelog`

Owns rationale for material planning changes. Append decisions; do not use it for routine task status movement.

### Feature specifications

Own durable behavior for one bounded domain such as evaluation, telemetry or one runtime integration. New focused specs should be created only when a real concern becomes too detailed for the existing owner.

### ADRs

Own durable decisions with meaningful alternatives/trade-offs, such as the implementation stack, persistence architecture or plugin mechanism.

## Required metadata

Every active Markdown document under `docs/` except ADR entries should start with:

```text
Status: active
Document type: <type>
Owner: <repository or domain>
Canonical scope: <unique dotted scope>
Read when: <specific trigger>
Last reviewed: YYYY-MM-DD
```

## Before creating a new document

1. Check this map for an existing canonical owner.
2. Update the existing source if the information fits its scope.
3. Create a new file only for a durable independently readable concern.
4. Give it a unique canonical scope.
5. Link it from this map or the closest future domain index.
6. If the new document replaces an old source, explicitly redirect/archive the old one.

Do not create a document merely to report that one branch or task completed.

## Update workflow

For a normal implementation change:

```text
code/tests
  + current-state status update
  + focused spec if behavior changed
  + roadmap only if milestone changed
  + implementation-plan only if plan/dependencies changed
  + plan-changelog only if the plan changed materially
```

This separation is important: it keeps frequent progress tracking from rewriting durable specifications and preserves a readable history of why the roadmap changed.

## Precedence

When documentation conflicts, prefer in this order:

1. executable tests/contracts;
2. accepted ADRs;
3. architecture/focused feature specifications;
4. implementation plan;
5. current state;
6. roadmap;
7. root README;
8. historical/archive material.

A contradiction that changes behavior should be corrected in the canonical owner, not silently reconciled in a summary.
