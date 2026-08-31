# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-31

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

The desktop browser product covers use-case-first planning/results, evidence drill-down, same-case comparison and product hardening. Product UX/UI convergence remains active for final human accessibility/usability review. `PRE_REAL_E2E` now gates representative-hardware work so real-device runs confirm residual runtime/hardware gaps rather than discover ordinary product-flow defects.

Primary product question:

> For this use case on this device, which available model/configuration gives me the best evidence-backed trade-off, and why?

## Integrated baseline

`dev` contains Overview; Find best setup through frozen Campaign review/execution/Results/exact-case comparison; Test a model; Live Run recovery; Runs/Run Detail; Compare; Library/Settings; Benchmark Detail; and Run -> Samples -> Sample Evidence.

Campaigns revalidate frozen plan digests, persist reconnectable lifecycle separately from immutable Runs and apply compatibility before `strict-quality-dominance@1.0.0`. Same-case comparison stays tied to candidate/config/Run/sample-attempt identity; missing, incompatible and not-retained evidence remain explicit.

Product hardening covers keyboard/focus semantics, assistive loading/error feedback, reduced motion, long-content containment and 1024/1280/1600 desktop widths. Five provenance-bound 1536x960 browser goldens protect selected high-value surfaces.

`PRE_REAL_E2E` requires every J0-J9 browser journey to pass with retained screenshot and Playwright trace, then requires assembled packaged-product evidence for J0/J1/J8/J9. The current acceptance evidence satisfies both layers and reports `READY_FOR_REAL_ENVIRONMENT: YES`; subsequent real-device work must still use a current passing gate rather than treating this status text as evidence.

Hosted fixtures never prove representative hardware/runtime behavior; `RUNTIME-1` remains real-environment evidence.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | ACTIVE | UXUI-10 manual compact/standard/wide accessibility and representative-user review |
| [Representative device evidence](workstreams/representative-device-evidence.md) | READY | first real LLS/model/device run with retained fingerprint/bundle; re-check current `PRE_REAL_E2E` before execution |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 EVIDENCE BLOCKED / MIG-003 BLOCKED | EV-3 + real PL replacement run, then redundant-path removal/smoke |

## UX/UI baseline

`design/ux-contract.json` and `design/brand-kit.json` own experience truth. Approved design targets and the bounded implementation-golden set remain separate owners.

Find best setup consumes backend-owned relevance, candidate inventory and planning; Performance Lab does not invent parameter sweep ranges. Campaign compatibility/missing evidence precede recommendation. Same-case comparison preserves exact attempt/evaluator/retention identity.

UXUI-10 has automated implementation-golden evidence; manual assistive-technology/contrast and representative-user/reference-grade acceptance remain explicit human evidence.

## Evaluation migration

Post-cutover evaluation evidence belongs to Performance Lab under PL-native identities; existing LLS `general-purpose@1.0.0` evidence remains legacy. Serving, residency, runtime identity/status, provider metrics and hardware/resource correctness remain LLS-owned.

MIG-003 still requires EV-3, a current passing `PRE_REAL_E2E`, a real PL run against LLS and post-disable serving/runtime smoke.

## Integration lines

- `dev` is the integration line; ordinary feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately with `FULL` validation.

## Evidence still required

- UXUI-10 manual accessibility/representative-user acceptance;
- representative resident-model identity/resource/telemetry/repeated-load evidence after pre-real acceptance;
- LLS EV-3, real PL replacement run and post-disable cross-repository smoke;
- human acceptance where release claims depend on usability.
