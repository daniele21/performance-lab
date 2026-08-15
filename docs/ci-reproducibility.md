# CI dependency reproducibility

Status: active
Document type: focused-specification
Owner: release hardening
Last reviewed: 2026-08-15

Repository validation uses an exact dependency snapshot in `requirements/ci-constraints.txt` for the Ubuntu Python 3.12/3.13 matrix.

The snapshot has a deliberately narrow scope: it makes repository CI dependency resolution repeatable and reviewable. It is **not** presented as a universal release lock for every operating system or Python environment.

## Validation contract

CI performs three separate checks:

1. install the pinned pip version used by the validated snapshot;
2. install `.[dev]` under the exact CI constraints;
3. run `scripts/validate_ci_constraints.py` before the normal repository validation.

The constraint validator fails when:

- a direct runtime/dev dependency from `pyproject.toml` has no exact CI constraint;
- a constraint is not an exact `==` pin;
- a constrained package is missing from the installed environment;
- the installed version differs from the committed snapshot.

This means adding or changing a direct dependency cannot silently reintroduce an unconstrained resolver path in CI.

## Updating the snapshot

Dependency updates should be intentional:

1. resolve and test the proposed dependency set on both supported CI Python versions;
2. update `requirements/ci-constraints.txt` in the same PR as any dependency-range change;
3. run the full repository gate on Python 3.12 and 3.13;
4. review dependency changes separately from product behavior changes when practical.

## Remaining release work

A future release-candidate step still needs a cross-platform distribution strategy for wheel/sdist build reproducibility and installation verification. The CI constraint snapshot does not claim to solve build-backend or platform-specific locking by itself.
