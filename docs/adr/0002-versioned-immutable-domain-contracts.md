# ADR 0002 — Versioned immutable domain contracts and dimension-specific comparability

Status: accepted
Date: 2026-08-15

## Context

The lab must compare results across models, quantizations, runtimes, generation settings and devices without silently treating incompatible experiments as equivalent. At the same time, the configuration under test must be allowed to change; otherwise the comparison engine would reject the exact experiments the product exists to perform.

Persisted evidence also needs explicit schema/version behavior and privacy-safe endpoint configuration.

## Decision

Use strict, immutable Pydantic domain values with `extra=forbid` and schema version `1` for persisted/exported top-level objects.

Rules:

- completed evidence is represented by immutable values rather than mutable ORM/domain objects;
- `None` on optional identity fields means explicitly **unknown / not observed**; the system does not invent values;
- raw credentials are not representable in `EndpointProfile`; authentication references environment-variable names only;
- exported `Run`/`ExecutionFingerprint` values contain a persistence-safe endpoint identity rather than the connection URL/credential configuration;
- loaders reject unsupported schema versions instead of guessing migrations;
- canonical JSON provides deterministic SHA-256 fingerprint identity;
- comparability is evaluated by result dimension.

Initial dimension invariants:

- **capability:** dataset snapshot, evaluator versions, prompt-template version and benchmark protocol must match;
- **runtime:** hardware identity, load profile and benchmark protocol must match;
- **resource:** hardware identity, telemetry level/protocol/collectors and benchmark protocol must match.

Model identity, quantization, runtime identity and generation configuration are allowed experimental variables. Their differences are reported in run identity diffs later, but are not automatically non-comparability reasons.

## Alternatives considered

### Require complete execution fingerprints to be identical

Scientifically strict but useless for comparing model/runtime/config changes, which are the primary product use case.

### Permit all runs to compare and annotate caveats

Convenient but unsafe: it would produce precise-looking percentages across changed datasets, evaluators, hardware or measurement protocols.

### Mutable persistence entities as the domain model

Simple for database-first implementation, but makes completed evidence easier to alter and couples core behavior to storage choices.

## Consequences

Positive:

- downstream workstreams share one stable identity vocabulary;
- incompatible comparisons fail with typed reasons;
- unknown telemetry/runtime identity is explicit;
- model/runtime/config experiments remain possible without weakening dimension-specific invariants;
- storage can preserve canonical immutable evidence.

Negative:

- schema evolution requires deliberate migration/version handling;
- some legitimate comparisons may need future explicit comparison modes rather than relaxing core rules globally;
- generation-config changes are comparable but must be surfaced prominently in identity diffs to avoid over-interpreting causality.

## Validation / revisit trigger

Round-trip, version-rejection and compatibility tests are required in FND-002. Revisit individual invariants when a real benchmark protocol demonstrates that a stricter or more permissive rule is needed; record that as a versioned protocol/ADR change rather than silently changing historical semantics.
