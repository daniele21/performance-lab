# Definition of Done

Status: active
Document type: completion-policy
Owner: repository
Canonical scope: delivery.definition-of-done
Read when: assessing task completion, merge readiness, milestone completion or release readiness
Last reviewed: 2026-08-24

A Performance Lab change is complete only when the behavior, evidence semantics, failure/resource lifecycle, tests and applicable durable documentation agree. A successful happy-path demo or green compile is not sufficient.

## Completion levels

1. **Implementation complete** — behavior exists behind the intended owner/boundary and focused deterministic tests pass.
2. **Merge ready** — applicable repository/product checks pass and current state/contracts are truthful.
3. **Benchmark trustworthy** — enough real endpoint/device evidence exists for the claims enabled by the feature.
4. **Release ready** — milestone, build/artifact, compatibility/migration and representative-evidence gates required by the release are satisfied.

A change may be merge-ready while representative hardware evidence remains pending, but docs/UI must preserve that distinction.

## Universal completion path

Applicable slices should satisfy:

```text
OWNER / CONTRACT
-> CODE
-> DIRECT CONSUMERS
-> FAILURE + CANCELLATION + RECOVERY
-> RESOURCE + DATA LIFECYCLE
-> SECURITY / TRUST BOUNDARY
-> OBSERVABILITY
-> TEST / INTEGRATION / E2E AS JUSTIFIED
-> DURABLE DOCS / DESIGN CONTRACT
-> PRODUCT CLAIM
```

For user-facing work, insert the `design/ux-contract.json` decision order before component/polish decisions.

## Core evidence invariants

Changes affecting evaluation evidence preserve:

- schema and protocol versions;
- dataset snapshot / sample-selection identity;
- task/evaluator versions;
- effective generation/load configuration;
- complete execution fingerprint or explicit unknown fields;
- immutable completed run evidence;
- typed partial/interrupted state that cannot masquerade as completion;
- quality, runtime and resource dimensions as separate evidence;
- endpoint-reported vs lab-observed provenance.

Materially different executions must not collapse into indistinguishable fingerprints.

## Comparison / regression

Complete only when:

- identity differences and compatibility are established before deltas;
- comparability is dimension-specific with typed reasons;
- invalid/incomparable deltas are absent rather than made visually plausible;
- missing metrics never silently pass policy;
- explicit baselines/policies are versioned and auditable;
- PASS / FAIL / NOT_COMPARABLE / NOT_EVALUATED remain distinct outcomes.

## Adapter / dataset / evaluator

Adapters cover applicable probe, streaming/non-streaming, malformed/provider error, timeout, cancellation, token-usage absence, unsupported parameter and secret-redaction paths. Provider-specific behavior remains inside the adapter.

Dataset/task changes preserve stable source/snapshot identity, deterministic selection, invalid/empty behavior, mapping/parser failures, evaluator assignment and provenance/license information where relevant.

Evaluators have static fixtures for known correct/incorrect/malformed behavior, deterministic normalization/versioning and mathematically consistent aggregation. Evaluator infrastructure failures are not counted as model errors. Judge-based evaluation persists judge/rubric/config identity.

## Runtime / telemetry

Runtime measurements define clock, exact event boundaries, warmup, repetitions, cold-state assumptions, token-count provenance, aggregation and failure denominators. TTFT is reported only when a first-output event can actually be observed; tokens/sec requires trustworthy token counts.

Telemetry defines metric scope/unit/provenance, unavailable/permission/error states, collector version/sampling protocol and overhead limitations. Telemetry can fail independently unless explicitly required by the suite. Device-specific performance/resource claims require representative hardware evidence.

## Persistence / API / CLI

Persistence changes cover schema/migration, atomic publication, interruption, completed-run immutability, export/import, corrupt/incompatible artifacts, secret exclusion and retention/delete behavior where implemented.

CLI/API behavior provides typed/stable validation/failure semantics, cancellation, machine-readable outputs where automation is intended, deterministic configuration parsing and IDs/links to persisted evidence. Automation must not depend on parsing human console prose.

## Product UI

Meaningful UI work follows the durable experience contract:

```text
user outcome
-> task model
-> IA / critical journey
-> information + action hierarchy
-> progressive disclosure / defaults
-> interactions / states / feedback / recovery
-> adaptive/platform behavior
-> accessibility
-> semantic components/tokens
-> purposeful motion
-> visual polish / functional graphics
-> validation
```

UI completion additionally requires:

- canonical application/read models rather than frontend reimplementation of benchmark truth;
- loading, empty, error, disabled and other reachable critical states;
- explicit unknown/unavailable/partial/not-comparable evidence;
- clear primary/secondary/destructive action hierarchy;
- keyboard/focus/assistive semantics and reduced-motion behavior where applicable;
- supported compact/standard/wide contexts preserving content priority;
- semantic component/token reuse instead of one-off drift;
- motion only for feedback/continuity/progress/state/orientation purposes;
- critical-journey E2E when lower levels cannot prove the complete user outcome.

A screenshot alone does not prove interaction, accessibility, recovery, adaptive behavior or usability.

## Privacy / security

By default, normal evidence/logs/CI artifacts must not expose API keys, authorization headers, signed tokens, arbitrary environment variables, private paths or prompt/output content when aggregate-safe mode is selected.

Evidence-rich prompt/output storage must be explicit, visibly sensitive and have a defined retention/delete boundary. Local-only behavior must not silently fall back to cloud processing.

## Resource and operational lifecycle

Changes that create processes, listeners, queues, caches, temp files, browser profiles, workspaces or other owned resources define bounds, timeout/cancellation and cleanup across success, failure, timeout, cancellation, interrupt and partial initialization.

When build/package/release behavior is affected, the strict `.engineering/commands.json` contract requires:

- unique build identity plus source revision/dirty state;
- immutable successful artifacts promoted only after validation;
- manifest and SHA-256 checksums;
- build delta against the previous successful comparable build;
- bounded local/CI retention;
- smoke/stop/clean proving no orphan project-owned process/listener/temp state.

These guarantees are enforced by the canonical Built Product and strict operations-verifier paths; changes to that lifecycle must keep those gates green rather than weakening the contract.

## Validation evidence

Choose the lowest deterministic layer that proves the invariant, then expand with blast radius:

- unit/component tests for local logic/state;
- contract/integration tests for shared boundaries;
- canonical repository `check`/`test` for broad changes;
- E2E for complete critical workflows not established below that level;
- smoke for built/runtime viability;
- accessibility/adaptive/visual/usability evidence when the product claim requires it;
- real endpoint/device evidence for hardware/runtime/thermal/resource or real-integration claims.

Record evidence as PASS / FAIL / PENDING / N/A. Synthetic/emulator/fixture evidence cannot satisfy a stronger representative claim.

## Documentation completion

Update exactly the canonical owner that changed:

- architecture/ownership -> `architecture.md` or ADR;
- durable shipped behavior needing explanation -> `features/` or the focused operational reference;
- integrated/blocker/next state -> `current-state.md`;
- milestone outcome -> `roadmap.md`;
- coordinated active dependencies/acceptance -> the single owning `workstreams/*.md`;
- benchmark/evaluator protocol -> `evaluation-and-benchmarking.md`;
- telemetry semantics -> `telemetry.md`;
- UX/design-system contract -> `design/`;
- agent routing -> `AGENTS.md` only when durable routing/invariants change.

Do not create or append plan/progress/changelog documents for implementation history. When a workstream completes, transfer durable truth, update current state and delete the workstream by default; Git history is the normal archive.

## Milestone / release rule

Do not close a milestone or make a release claim merely because most code exists. Required comparability, evidence identity, cleanup, migration, browser/user, build/artifact or representative-device gates must either pass or remain explicitly pending.
