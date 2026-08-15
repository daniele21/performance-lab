# Architecture Decision Records

Status: active
Document type: adr-index
Owner: repository
Canonical scope: architecture.decisions
Read when: making or reviewing a durable architectural decision with meaningful alternatives or migration impact
Last reviewed: 2026-08-15

Use ADRs for decisions that should remain understandable after the implementation context is gone.

Good ADR candidates include:

- primary implementation language/runtime;
- package/module structure when it establishes dependency boundaries;
- local persistence and artifact storage architecture;
- schema/versioning strategy;
- plugin/registry mechanism;
- local API/UI process topology;
- instrumented telemetry protocol;
- privacy/evidence persistence defaults.

Do not create ADRs for routine implementation choices that are easily reversible and do not affect public contracts or architecture.

## Status vocabulary

- `proposed`
- `accepted`
- `superseded`
- `deprecated`

## Naming

```text
0001-short-decision-title.md
0002-next-decision.md
```

## Template

```markdown
# ADR 000X — Decision title

Status: proposed
Date: YYYY-MM-DD

## Context

What problem or constraint requires a durable decision?

## Decision

What is being chosen?

## Alternatives considered

### Alternative A

Pros / cons.

### Alternative B

Pros / cons.

## Consequences

Positive and negative consequences, including migration/test/operational impact.

## Validation / revisit trigger

What evidence validates the choice, and what future evidence would justify revisiting it?
```

## Index

| ADR | Status | Decision |
| --- | --- | --- |
| [`0001-python-core-and-toolchain.md`](0001-python-core-and-toolchain.md) | accepted | Python 3.12+ core, lightweight PEP 621 toolchain, shared validation gate, MIT |
| [`0002-versioned-immutable-domain-contracts.md`](0002-versioned-immutable-domain-contracts.md) | accepted | immutable schema-v1 evidence and dimension-specific comparability |
