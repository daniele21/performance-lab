# Performance Lab — coding agent guide

Repository-wide routing and durable invariants. Status belongs in `docs/current-state.md`; detailed behavior belongs in architecture/features/workstreams.

## Read only what the task requires

Always read this guide, then only the closest scoped `AGENTS.md`, the owning implementation/contracts/tests, and the canonical sources relevant to the change:

- `.engineering/commands.json` for setup/check/test/E2E/build/run/cleanup;
- `.engineering/e2e.json` for complete-workflow or environment-dependent claims;
- `docs/README.md` for documentation ownership/README impact;
- `design/ux-contract.json` + `design/brand-kit.json` for meaningful user-facing work;
- `docs/current-state.md` only when integrated/blocked/next state matters.

Do not load every plan or all documentation for a local change.

## Repository purpose

Performance Lab evaluates externally served AI inference endpoints and answers: for a use case and device, which available model/configuration gives the best evidence-backed trade-off? It owns evaluation, evidence, comparison and regression; serving-runtime lifecycle remains external.

## Non-negotiable invariants

- Core does not own model loading or serving-runtime lifecycle.
- Model name alone is not benchmark identity; execution fingerprints stay explicit and immutable.
- Completed run evidence and dataset snapshots are immutable/versioned.
- Quality, runtime performance and resources remain separate; unknown/unavailable is never fabricated as zero.
- Compatibility precedes deltas, rankings and regression verdicts; endpoint and lab measurements retain distinct provenance.
- Secrets/raw authorization are never persisted in portable evidence.
- UI projections consume canonical Python semantics; TypeScript does not recreate benchmark/comparability truth or read SQLite directly.
- Local listeners, jobs, temporary state and artifacts have bounded lifecycle/cleanup ownership.
- Hosted CI/fakes do not become real device/model evidence. Execution capability and environment fidelity are independent.
- Code and affected durable documentation ship together; stale canonical docs block publication.
- README identity and usage are separate owners: preserve valid purpose/positioning, but keep setup/run/configuration/public examples current.

## Ownership and routing

| Change | Start here | Inspect next |
| --- | --- | --- |
| Domain/fingerprint/comparability | `src/performance_lab/domain/` | architecture, consumers, tests |
| Inference integration | `src/performance_lab/adapters/` | plugin contracts/tests |
| Dataset/evaluator | `src/performance_lab/datasets/`, `src/performance_lab/evaluation/` | spec, fixtures/tests |
| Runtime benchmark/telemetry | `src/performance_lab/performance/`, `src/performance_lab/telemetry/` | provenance/resource contracts |
| Persistence/comparison/regression | `src/performance_lab/storage/`, `src/performance_lab/regression/` | evidence reference/tests |
| UI application/API | `src/performance_lab/application/`, `src/performance_lab/ui_api.py`, `src/performance_lab/ui_server.py` | frontend client/lifecycle tests |
| Browser UI | `frontend/AGENTS.md` | `design/`, page/components/tests |
| Product experience | `design/ux-contract.json` | brand kit, design system, journeys |
| Active coordinated work | `docs/current-state.md` | relevant workstream only |
| Documentation impact | `docs/README.md` | affected canonical owner |

Add scoped `AGENTS.md` only for meaningful local hazards/ownership/validation rules.

## Operating and validation

`.engineering/commands.json` is the intent-to-command source of truth. `check` is broad cheap validation, `test` unit/integration/contract behavior, `e2e` complete workflow evidence, `build` the production browser build, `smoke` built/runtime viability, `package` publish packaging, and `stop`/`clean` release owned state. E2E and smoke are not synonyms.

Use `skills/validate-change/SKILL.md` while iterating and `skills/preflight-change/SKILL.md` before publication. `python scripts/select_validation_profile.py` selects blast radius:

- `LEAN` — docs/governance only;
- `SCOPED` — contained implementation owner/module;
- `STRONG` — cross-boundary, user-facing, persistence, E2E or release-sensitive behavior;
- `FULL` — engineering/CI/dependency/toolchain/selector changes, promotion or unknown executable scope.

Never silently downgrade below `auto`; broadened repairs require reselection. If an automatable gate cannot run locally, classify it `REMOTE_AUTOMATED` and use repository-owned GitHub workflows rather than asking the user to run it. Use `REAL_ENVIRONMENT` only when the claim truly requires it.

Preflight must classify `README_IDENTITY`, `README_USAGE`, `FEATURE_DOCS`, `ARCHITECTURE`, `ADR`, `SECURITY_DATA`, `OPERATIONS`, `PRODUCT_EXPERIENCE`, `CURRENT_STATE`; `DOCS_CURRENT_WITH_IMPLEMENTATION` must be `PASS`.

## E2E fidelity

`.engineering/e2e.json` owns environments:

- `browser-built-mocked-api`: built React + Chromium + mocked API (`host_or_fake`);
- `python-product-fixture`: real CLI/application/HTTP/SQLite/regression + deterministic inference fixture (`representative_virtual`);
- `packaged-product-fixture`: packaged wheel + built frontend + real API/SQLite/Chromium + deterministic fixture (`representative_virtual`);
- `real-runtime-device`: real external runtime/model/device (`target_environment`).

Use the cheapest environment that proves the claim. `RUNTIME-1` keeps real model/runtime identity, physical resource/telemetry/thermal/repeated-load evidence as residual real-environment requirements.

## Product experience

The repository adopts `product-ui`. Follow `skills/design-product-experience/SKILL.md` at proportional depth: resolve task model/journey/hierarchy before interaction polish; cover states, recovery, adaptive behavior and accessibility when affected; visual-only work preserves settled semantics and existing design-system tokens/components. Do not expose backend complexity merely because it exists, and do not use motion/graphics to mask unresolved flow or hierarchy.

## Change workflow

1. Confirm owner and smallest coherent scope; inspect owner, consumers, fakes and tests before shared-contract changes.
2. Use the single owning workstream only when persistent coordination is justified.
3. Implement one coherent slice and validate narrowly while iterating, then expand by blast radius.
4. For complete workflows choose the relevant `.engineering/e2e.json` journey and sufficient fidelity; keep residual real-environment evidence explicit.
5. Assess documentation impact from observable behavior. Update only affected canonical owners; README identity and usage are independent.
6. Update `docs/current-state.md` only for integrated/blocked/next changes; finalize completed workstreams by transferring durable knowledge and deleting them by default.
7. Run preflight, review the full diff and publish only exact-head evidence with current documentation.

## Documentation ownership

`README.md` owns stable identity plus the shortest current public usage entry point; `docs/architecture.md` architecture/boundaries; `docs/features/` durable non-obvious shipped behavior; `docs/adr/` accepted decisions; `docs/current-state.md` operational state; `docs/workstreams/` active bounded plans; `design/` experience/brand contracts; Git implementation history. Existing feature docs update in the same change as behavior they describe. Do not create branch-progress docs or duplicate status registries.

## Stop conditions

Never claim validation, accessibility, real-device performance, cleanup or release evidence not executed. Surface conflicts instead of bypassing a durable invariant/ADR, sensitive-state boundary, canonical evidence/comparability/lifecycle ownership, affected documentation, product-experience contract or E2E fidelity.
