# Architecture Decision Records

Status: active
Document type: adr-index
Owner: repository
Canonical scope: architecture.decisions
Read when: making or reviewing a durable architectural decision with meaningful migration impact
Last reviewed: 2026-08-17

ADRs preserve decisions whose rationale must remain understandable after an implementation workstream is gone. Routine reversible implementation details belong near code/tests rather than here.

## Status vocabulary

- `proposed`
- `accepted`
- `superseded`
- `deprecated`

## Index

| ADR | Status | Decision |
| --- | --- | --- |
| [`0001-python-core-and-toolchain.md`](0001-python-core-and-toolchain.md) | accepted | Python 3.12+ core and lightweight package/toolchain |
| [`0002-versioned-immutable-domain-contracts.md`](0002-versioned-immutable-domain-contracts.md) | accepted | immutable versioned evidence and dimension-specific comparability |
| [`0003-sqlite-local-run-store.md`](0003-sqlite-local-run-store.md) | accepted | local SQLite run store with immutable completed evidence |
| [`0004-performance-lab-owns-evaluation-product.md`](0004-performance-lab-owns-evaluation-product.md) | accepted | Performance Lab owns benchmark/evaluation product UX; Local LLM Server remains the serving/runtime control plane |

## Minimal ADR shape

```markdown
# ADR 000X — Decision title

Status: proposed
Date: YYYY-MM-DD

## Context
## Decision
## Alternatives considered
## Consequences
## Validation / revisit trigger
```
