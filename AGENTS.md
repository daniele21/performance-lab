# Performance Lab — Coding Agent Guide

Performance Lab evaluates externally served AI inference endpoints and determines which available model/configuration gives the best evidence-backed trade-off for a use case/device. It owns evaluation, evidence, comparison and regression; serving-runtime lifecycle remains external.

## Durable invariants

- Execution fingerprints are explicit/immutable and completed evidence/datasets are versioned.
- Quality, runtime and resource dimensions stay separate; compatibility is established before deltas, rankings or regression claims.
- Endpoint provenance and lab provenance stay distinct; raw authorization is never persisted.
- Python is the semantic owner; TypeScript projects those semantics rather than redefining them.
- Local listeners/jobs/temp/artifacts are bounded and cleaned.
- Hosted fixtures never become real model/runtime/device/telemetry/thermal evidence by implication.

## Ownership

| Change | Owner | Inspect / prove |
| --- | --- | --- |
| Domain/comparability | `src/performance_lab/domain/` | domain/comparison tests |
| Inference adapters | `adapters/` | adapter contracts |
| Dataset/evaluation | `datasets/`, `evaluation/` | evidence/repeatability tests |
| Benchmark/telemetry | `performance/`, `telemetry/` | metrics/provenance tests |
| Persistence/regression | `storage/`, `regression/` | migration/regression tests |
| App/API | `application/`, `ui_api.py`, `ui_server.py` | API/product tests |
| Browser/UI | `frontend/AGENTS.md`, `design/` | browser/product journeys |

Follow applicable scoped `AGENTS.md`; extend the canonical owner before adding state/policy and inspect material consumers for shared boundaries.

## Read by task

| Task | Read now |
| --- | --- |
| Pure docs/copy | affected source/links; `docs/README.md` only if ownership unclear |
| Behavior/bug/contract | `skills/structured-change/SKILL.md`, `skills/validate-change/SKILL.md`, relevant commands |
| Material UI | above + `skills/design-product-experience/SKILL.md`, relevant `design/*` |
| Integration/release | `skills/preflight-change/SKILL.md`, commands, affected `.engineering/e2e.json` |
| Missing deterministic remote gate | `skills/remote-preflight/SKILL.md` |
| Persistent multi-session work | `skills/plan-workstream/SKILL.md` + active plan; finalize with `skills/finalize-workstream/SKILL.md` |

## Delivery and evidence

- **ITERATION**: focused Python/frontend owner-local falsification; no exact-head/full-diff/docs/publication ceremony per edit.
- **INTEGRATION** (`PR -> dev`): exact candidate/base, complete diff, affected durable docs, selected automated gates and affected critical E2E. Material UI/UX integration journeys require `FULL_MEDIA`. Required `REAL_ENVIRONMENT` evidence remains explicit but `DEFERRED_TO_RELEASE`.
- **RELEASE** (`dev -> main`): `FULL` plus release-critical artifact/E2E and every applicable required residual real-environment confirmation.

The native selector resolves risks -> concrete gates -> profile; profiles are shorthand. `.github/workflows/validate.yml` is the automatic PR owner and should avoid duplicate overlapping cones. `PRE_REAL_E2E` proves the complete automatable cone only; `RUNTIME-1` keeps real model/runtime/device/telemetry/thermal/repeated-load claims in release evidence.

## Context, diagnosis and completion

`.engineering/documentation-policy.json` owns bounded context routes. Use `python3 scripts/verify_agent_context.py --route bug --format json`, optionally with `--path`/`--workstream`; routes estimate reading cost, not validation scope.

For meaningful work state observable outcome, owner, invariants and proof. Classify failures before patching. Each failed repair needs a falsifiable hypothesis; after two failed repairs with the same signature, change diagnostic strategy and obtain new discriminating evidence before a third. On resume refresh head/tree/base; checkpoint evidence is a pointer, not current-source proof.

Before integration update affected canonical docs. Transfer durable truth and deferred release obligations before deleting completed plans. Never suppress legitimate gates, persist credentials, create competing semantic owners or promote hosted evidence into a real-device/runtime claim.
