# ADR 0003 — SQLite for the first local run store

Status: accepted
Date: 2026-08-15

## Context

Performance Lab needs a durable local evidence store before comparison and regression work can be trustworthy. The store must keep mutable in-progress state separate from completed immutable evidence, publish terminal runs atomically, support portable export/import and remain usable in a local-first desktop/CLI context without introducing a server dependency.

## Decision

Use Python's standard-library SQLite driver for the first durable run store.

The storage contract uses two logical state classes:

- `working_runs` for replaceable non-terminal state;
- `completed_runs` for immutable terminal evidence.

Publishing a terminal run uses one SQLite transaction that inserts completed evidence and removes matching working state atomically. A completed `run_id` may be re-published only when its canonical payload is byte-identical; conflicting replacement is rejected.

Portable run exchange uses a versioned ZIP bundle containing only `manifest.json` and `run.json`. The manifest includes a SHA-256 digest of the canonical run payload. Raw endpoint credentials are not representable in the persisted `Run` schema.

## Alternatives considered

### Directory of JSON files

Pros:

- extremely transparent;
- no database API.

Cons:

- atomic multi-file publication and concurrent updates become filesystem-specific;
- history/query/index operations become progressively harder;
- corruption and partial-state handling require custom conventions.

### DuckDB

Pros:

- strong analytical query capabilities;
- attractive for later aggregate analysis.

Cons:

- adds a runtime dependency before analytical workloads justify it;
- the initial need is transactional evidence publication rather than columnar analytics.

### PostgreSQL or hosted database

Pros:

- robust multi-user/server capabilities.

Cons:

- conflicts with the local-first MVP;
- adds deployment and operations requirements unrelated to endpoint evaluation.

## Consequences

Positive:

- atomic local publication with no new runtime dependency;
- simple migration path for indexed comparison queries;
- easy separation of working versus immutable completed state;
- portable bundle export remains independent from SQLite internals.

Negative:

- schema migrations must be managed explicitly as storage evolves;
- SQLite is not the target for distributed multi-runner coordination;
- large raw telemetry series or binary artifacts should not automatically be embedded in the main database.

## Validation / revisit trigger

Validate the choice through STO-001 tests for working-state replacement, atomic terminal publication, immutable conflict rejection and bundle round-trip.

Revisit if distributed runners, high-volume telemetry storage, concurrent multi-user writes or analytical workloads become primary requirements rather than future extensions.
