# AGENTS.md — AI Performance Lab contributor guide

This repository treats documentation, reproducible evidence and implementation state as part of the product contract.

## 1. Required reading order

For normal implementation work, read only what is needed:

1. [`README.md`](README.md) — product boundary.
2. [`docs/current-state.md`](docs/current-state.md) — integrated baseline, blockers and next work.
3. [`docs/implementation-plan.md`](docs/implementation-plan.md) — locate the task ID, dependencies and acceptance criteria.
4. The closest focused specification:
   - [`docs/architecture.md`](docs/architecture.md)
   - [`docs/evaluation-and-benchmarking.md`](docs/evaluation-and-benchmarking.md)
   - [`docs/telemetry.md`](docs/telemetry.md)
5. [`docs/definition-of-done.md`](docs/definition-of-done.md) before marking work complete.

Use [`docs/README.md`](docs/README.md) to route unfamiliar questions. Do not treat every document as mandatory reading.

## 2. Canonical documentation ownership

- live integrated/blocked/next state -> `docs/current-state.md`
- target, task decomposition, dependencies, acceptance -> `docs/implementation-plan.md`
- capability milestone sequencing -> `docs/roadmap.md`
- material changes to the plan and rationale -> `docs/plan-changelog.md`
- architectural boundaries -> `docs/architecture.md` / ADR
- evaluator/dataset/performance protocol -> `docs/evaluation-and-benchmarking.md`
- telemetry/resource protocol -> `docs/telemetry.md`
- completion requirements -> `docs/definition-of-done.md`

Do not copy the same detailed status table into several files.

## 3. Planning discipline

Every implementation branch/work block should name the task ID(s) it addresses, for example:

```text
ADP-001 OpenAI-compatible adapter
PERF-001 single-request latency protocol
```

Before starting:

- verify dependencies in `implementation-plan.md`;
- verify live state in `current-state.md`;
- if a task is blocked, do not silently bypass the dependency by inventing a duplicate contract.

After implementation:

- update task status in `current-state.md`;
- update `roadmap.md` only when a milestone outcome/status changes;
- update `implementation-plan.md` only when target/dependencies/acceptance change;
- append `plan-changelog.md` only for a material planning change.

## 4. Parallelization discipline

The repository deliberately separates work into lanes:

```text
FND repository/contracts
ADP inference adapters
DAT datasets/suites
EVAL capability evaluation
PERF runtime benchmarking
TEL telemetry
STO storage/comparison
CLI developer control plane
REG regression/CI
UI visual product
INT external integrations
DOC documentation/evidence
```

When dependencies are satisfied, prefer independent workstreams in parallel rather than serializing unrelated tasks.

Current planned fan-out after FND-002:

```text
ADP-001  ||  DAT-001  ||  TEL-001  ||  STO-001  ||  CLI-001(fakes)
```

Later:

```text
EVAL-001  ||  PERF-001  ||  TEL-002  ||  STO-003
```

Parallel work must still converge on one canonical domain contract. Do not create competing copies of schemas/interfaces in separate lanes.

## 5. Core architectural invariants

Do not violate these without an ADR + plan update:

- Performance Lab evaluates externally served inference; core does not own model loading/runtime lifecycle.
- Provider/runtime differences belong behind adapters.
- A model name alone is never the complete benchmark identity.
- Completed run evidence is immutable.
- Dataset selection is frozen into an immutable snapshot identity.
- Effective generation configuration is recorded or explicitly unknown.
- Quality, runtime performance and resource efficiency remain separate metric dimensions.
- Comparison is dimension-specific and must surface incompatibility reasons.
- Unavailable metrics remain unavailable; never encode them as zero.
- Endpoint-reported metrics and lab-observed metrics retain different provenance.
- TTFT is not total latency.
- Token throughput requires trustworthy token counts.
- A first request is not called cold unless a controlled cold precondition exists.
- Telemetry failure does not fail inference unless a suite explicitly requires that telemetry metric.

## 6. Privacy invariants

Never persist in normal aggregate-safe evidence:

- API keys or authorization headers;
- signed URLs/tokens;
- arbitrary environment variables;
- secrets from endpoint configuration;
- private file paths unless sanitized;
- prompt/output text when aggregate-safe mode is active.

Evidence-rich prompt/output persistence must be explicit and documented.

## 7. Test expectations

Use deterministic fakes at the narrowest useful layer.

Expected patterns:

- pure tests for fingerprints, compatibility, evaluators and statistics;
- fake local HTTP server for inference adapter behavior;
- fake collectors for telemetry/orchestrator behavior;
- persistence integration tests for atomic/immutable evidence;
- end-to-end fake-endpoint execution before real-model tests;
- real endpoint/device evidence only for claims that require it.

Do not make CI depend on downloading a large model for ordinary deterministic validation unless a later release gate explicitly requires it.

## 8. Validation

FND-001 will establish the canonical repository validation command and CI workflow. Until then, documentation-only changes should at minimum verify:

```text
all relative documentation links resolve
Markdown is structurally readable
git diff --check equivalent passes
canonical owners do not contradict each other
current-state matches the implementation-plan task IDs
```

Once repository commands exist, update this file and `definition-of-done.md` in the same change.

## 9. New documents

Before adding a document:

1. read `docs/README.md`;
2. update an existing canonical owner if possible;
3. create a new specification only for a durable independently readable concern;
4. give it required metadata and a unique canonical scope;
5. add it to `docs/README.md`;
6. use an ADR for durable architectural decisions with meaningful alternatives.

Do not create per-branch progress documents. Use `current-state.md` and task IDs.

## 10. Scope changes discovered during implementation

If implementation reveals that a task must be split or reordered:

1. do not silently expand the task;
2. update `implementation-plan.md` with the new task/dependency structure;
3. append the rationale to `plan-changelog.md`;
4. update `current-state.md` and roadmap if affected;
5. continue with the now-canonical plan.

This keeps parallel agents from working from stale assumptions.
