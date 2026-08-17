# Automated product acceptance

Status: active
Document type: focused-specification
Owner: E2E
Canonical scope: testing.product-acceptance
Read when: changing product-level E2E coverage, CI gate separation, or real Local LLM Server acceptance smoke
Last reviewed: 2026-08-17

## Purpose

`E2E-001` proves that already-integrated Performance Lab components work together through the same boundaries a user or CI job actually exercises. It is intentionally stronger than unit/integration tests and intentionally weaker than representative real-model/device evidence.

State: `DONE`

Integrated through PR **#34** on `dev` (`f0771936526f5a230d4643ee3ea7e35d11de0440`). The final feature head `a761ad2dd6522946adfd8e03b1895adcaaaaa584` passed Repository validation run **32039271517**: Python 3.12 and 3.13 library validation plus the dedicated Product E2E Python 3.12 job all completed successfully.

This `DONE` state applies to deterministic automated product acceptance. The opt-in real Local LLM Server smoke, representative benchmark/device evidence and human acceptance remain separate empirical stages and are not claimed as completed here.

## Deterministic product gate

The mandatory product E2E gate launches an external deterministic HTTP process that exposes:

```text
GET  /v1/models
POST /v1/chat/completions
GET  /v1/runtime/identity
GET  /status
```

The test then invokes the actual `performance-lab` CLI through subprocesses. It does not inject an `httpx` mock into the adapter and does not call runner/regression functions directly.

The golden workflow is:

```text
probe
  -> baseline run
  -> SQLite publication
  -> .plab.zip integrity/contents
  -> inspect
  -> compatible repeated run
  -> PASS regression
  -> deliberately degraded model candidate
  -> FAIL regress-ci + JSON artifact
```

The fixture-good model deterministically answers the current frozen starter-suite records. The fixture-bad model returns deliberately wrong application output while preserving the same transport/runtime/hardware fixture, so the negative regression exercises quality semantics rather than a network failure.

A separate negative flow makes first-party identity unavailable while `required: true`; the run stops before evaluation and does not create a completed bundle.

The regression acceptance policy deliberately targets the evaluator-qualified canonical metric identity rather than a display-name shortcut. The E2E hardening exposed this contract by correctly producing `NOT_EVALUATED` when an earlier draft policy targeted only `normalized_exact_match`; the final gate uses `normalized_exact_match|normalized-exact-match:text-normalization-v1@1`.

## CI separation

Library validation remains the Python 3.12/3.13 matrix:

```text
ruff format --check
ruff check
mypy src
pytest --ignore=tests/e2e
```

Product E2E runs once in a dedicated Python 3.12 job:

```text
pytest tests/e2e
```

This makes failures attributable and avoids executing the full product workflow twice only to exercise the supported Python matrix. On failure, the Product E2E job retains a bounded pytest log artifact for diagnosis; successful runs do not upload it.

## Real-runtime smoke

`tests/real_runtime/smoke_local_llm_server.py` is opt-in and must run on a machine where a real Local LLM Server model is already resident.

It executes a real `probe`, writes the exact run configuration, requires `local-llm-identity-v1`, samples `/status`, executes the frozen `general-diagnostic-starter` suite and preserves the normal SQLite store and `.plab.zip` evidence.

Hosted CI does not run this smoke. Completion is a bounded acceptance preflight, not representative benchmark evidence and not a release-quality claim.

## Acceptance

`E2E-001` is `DONE` because:

1. Python 3.12/3.13 library validation is green on the final head;
2. the dedicated deterministic Product E2E job is green on the same head;
3. the workflow proves actual CLI + HTTP + persistence + bundle + regression behavior;
4. PASS and deliberate FAIL outcomes are both asserted;
5. required-identity failure is asserted as fail-before-evaluation;
6. real-runtime smoke remains separate, opt-in and documented;
7. the feature is merged into `dev`.

## Evidence boundary

The intended confidence ladder is:

```text
unit/integration
      -> deterministic product E2E
      -> real-runtime smoke
      -> representative evidence campaign
      -> human/UX acceptance where applicable
```

No earlier level substitutes for a later one. In particular, deterministic fixture results must never be used as model-quality, device-performance or hardware-resource claims.
