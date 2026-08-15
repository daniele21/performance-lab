# Definition of Done

Status: active
Document type: completion-policy
Owner: repository
Canonical scope: delivery.definition-of-done
Read when: assessing task completion, merge readiness, milestone completion or release readiness
Last reviewed: 2026-08-15

A Performance Lab feature is complete only when behavior, evidence semantics, tests, failure paths, observability and documentation are complete.

Compilation or a successful happy-path demo is not sufficient.

## 1. Completion levels

The repository distinguishes:

1. **Implementation complete** — behavior exists behind the intended boundary and focused tests pass.
2. **Merge ready** — repository validation passes from a clean checkout and documentation/status is current.
3. **Benchmark trustworthy** — the feature has enough real endpoint/device evidence to support the claims it enables.
4. **Release ready** — all required milestone gates and compatibility/migration checks pass.

A feature can be merge-ready while device-specific evidence remains pending, but documentation and UI must not describe unvalidated metrics or integrations as proven.

## 2. Functional completion

A task is functionally complete when:

- intended behavior exists through the correct architectural boundary;
- public behavior is represented through typed/stable contracts rather than implementation internals;
- invalid configuration, network failure, timeout, cancellation and partial failure are handled where applicable;
- unavailable measurements remain unavailable rather than becoming fake zeros/defaults;
- effective endpoint configuration is recorded or explicitly unknown;
- completed run evidence is immutable;
- partial state cannot be mistaken for completed evidence;
- resource ownership and cleanup are explicit.

## 3. Reproducibility completion

Any change that affects evaluation evidence must preserve:

- schema/version identity;
- dataset snapshot identity;
- task/evaluator versioning;
- benchmark protocol versioning;
- effective generation configuration;
- execution fingerprint stability;
- deterministic sample-selection behavior when configured;
- explicit unknown fields rather than inferred identity.

A benchmark feature is incomplete if two materially different configurations can produce indistinguishable fingerprints.

## 4. Comparison completion

A comparison/regression feature is complete only when:

- it computes and displays identity differences first;
- it determines comparability per metric dimension;
- incompatible metrics return typed reasons;
- quality, runtime and resource dimensions remain separable;
- explicit baselines are immutable;
- relative deltas handle zero/near-zero baselines safely;
- missing metrics do not pass thresholds silently;
- user-configured thresholds are versioned and auditable.

## 5. Adapter completion

An inference adapter must test:

- capability probe success/failure;
- non-streaming success;
- streaming success where supported;
- malformed response;
- provider/server error;
- timeout;
- cancellation;
- token usage present/absent;
- unsupported generation parameters;
- effective/unknown parameter recording;
- secret/header redaction.

Provider-specific behavior remains inside the adapter and must not leak conditionals into the orchestrator.

## 6. Dataset/task completion

A dataset/task feature must cover:

- stable source/snapshot identity;
- deterministic sample selection;
- empty/invalid dataset behavior;
- requested sample count larger than available population;
- mapping validation for custom data;
- parser failures;
- evaluator assignment/version identity;
- upstream license/provenance documentation where relevant.

## 7. Evaluator completion

An evaluator must have static fixture tests that prove:

- known correct output scores correctly;
- known incorrect output scores correctly;
- malformed/unparseable output has explicit behavior;
- normalization rules are deterministic and versioned;
- aggregation is mathematically consistent;
- evaluator exceptions are not counted as model errors.

Judge-based evaluators additionally require judge identity/rubric/configuration persistence.

## 8. Runtime benchmark completion

A runtime measurement feature must define:

- what clock is used;
- exact start/end events;
- warmup policy;
- repetition/sample count;
- cold-state assumptions;
- token-count provenance;
- statistical aggregation;
- failure/timeout denominator semantics.

TTFT is complete only for a protocol that can observe a first streamed output event or a clearly sourced provider timing. Total latency must never be relabeled TTFT.

Tokens/second is complete only when token counts are trustworthy.

## 9. Telemetry completion

Telemetry features must:

- identify metric scope, unit and provenance;
- report unavailable/permission/collector error states;
- fail independently from inference unless the suite explicitly requires the metric;
- record collector version and sampling protocol;
- avoid overclaiming process attribution;
- document sampling overhead/limitations;
- redact sensitive process/environment data.

Device-specific performance claims require representative hardware evidence.

## 10. Storage completion

Persistence changes must test:

- schema creation/migration;
- atomic publication of completed runs;
- interrupted/partial run handling;
- completed-run immutability;
- export/import round trip;
- corrupt/incompatible artifact behavior;
- credential/secret exclusion;
- retention/delete behavior where implemented.

## 11. CLI/API completion

Command/API features must provide:

- stable validation errors;
- non-zero exit/status for real failures;
- cancellation behavior;
- machine-readable output where automation is intended;
- deterministic configuration parsing;
- no requirement to parse human console text for CI;
- links/IDs to persisted run evidence.

## 12. UI completion

UI features must:

- consume domain/read models instead of recalculating benchmark semantics;
- show loading, empty, unavailable, partial and error states;
- surface identity differences in comparisons;
- distinguish unavailable from zero;
- preserve quality/runtime/resource separation;
- support keyboard/accessibility fundamentals;
- avoid exposing stored secrets;
- preserve cancellation and long-running progress state safely.

## 13. Test completion

Every implementation change should use the lowest useful deterministic layer.

Expected categories as applicable:

- unit tests for domain/evaluator/statistics logic;
- adapter tests using deterministic local fake servers;
- persistence integration tests;
- orchestrator tests using fake adapters/collectors/stores;
- end-to-end local test with a fake inference endpoint;
- real endpoint smoke evidence for benchmark claims;
- representative device evidence for hardware/resource claims.

Regression fixes should include a test that fails under the old behavior where practical.

## 14. Privacy/security completion

By default, evidence must not contain:

- API keys or authorization headers;
- signed URLs/tokens;
- arbitrary environment variables;
- private file paths unless sanitized;
- prompt/output content when aggregate-safe mode is selected.

If evidence-rich mode stores prompt/output text, the UI/report must clearly mark the artifact as potentially sensitive and retention/delete behavior must be defined.

## 15. Documentation completion

The same change updates the canonical owner:

- architecture/dependency boundary -> `architecture.md` or ADR;
- target/task/dependency/acceptance change -> `implementation-plan.md`;
- live integrated/blocker/next state -> `current-state.md`;
- milestone outcome/status -> `roadmap.md`;
- material planning decision -> `plan-changelog.md`;
- benchmark/evaluator protocol -> `evaluation-and-benchmarking.md`;
- telemetry semantics -> `telemetry.md`;
- developer navigation/validation -> `AGENTS.md` when present.

Do not duplicate a detailed status table across multiple documents.

## 16. Plan/task completion rule

A task ID in the implementation plan may be marked `DONE` in current state only when:

- all listed deliverables exist;
- acceptance criteria are met;
- required tests pass;
- required real-world evidence exists or the parent task explicitly distinguishes implementation from evidence;
- documentation is current;
- any remaining limitation is moved to a new explicit task rather than hidden in prose.

## 17. Milestone completion rule

A roadmap milestone closes only when its exit gate is satisfied.

Do not close a milestone because most code exists if:

- comparable identities are incomplete;
- sample/evaluator versions are ambiguous;
- real TTFT/token throughput semantics are unproven;
- resource metrics lack provenance;
- regression thresholds can compare incompatible runs;
- automation requires manual interpretation.

## 18. Validation discipline

FND-001 will establish the exact repository commands. The expected shape is one canonical local validation entrypoint that covers:

```text
format/lint
static/type checks
unit tests
integration tests
schema/documentation checks
build/package checks where applicable
git diff --check equivalent
```

CI should run the same core validation from a clean checkout.

A documentation-only change may use a narrower gate, but still requires link/navigation and formatting validation.

## 19. Merge checklist

```text
correct domain ownership
no provider/runtime coupling in core
explicit schema/version changes
stable execution fingerprint semantics
failure/cancellation paths covered
unavailable metrics remain unavailable
quality/runtime/resources not conflated
immutable completed evidence
privacy-safe persisted artifacts
focused + repository tests passing
current-state/roadmap/plan docs updated
material planning changes logged
claims match available evidence
```
