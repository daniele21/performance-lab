# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-31

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

The desktop browser product covers use-case-first planning/results, evidence drill-down, same-case comparison and product hardening. The next product-experience phase is a premium visual refactor: preserve settled journeys/semantics while moving the UI from a generic technical dashboard toward a calm, precise evidence instrument. Final human/reference-grade UX acceptance is intentionally deferred until that refactor is complete.

Primary product question:

> For this use case on this device, which available model/configuration gives me the best evidence-backed trade-off, and why?

## Integrated baseline

`dev` contains Overview; Find best setup through frozen Campaign review/execution/Results/exact-case comparison; Test a model; Live Run recovery; Runs/Run Detail; Compare; Library/Settings; Benchmark Detail; and Run -> Samples -> Sample Evidence.

Campaigns revalidate frozen plan digests, persist reconnectable lifecycle separately from immutable Runs and apply compatibility before `strict-quality-dominance@1.0.0`. Same-case comparison stays tied to candidate/config/Run/sample-attempt identity; missing, incompatible and not-retained evidence remain explicit.

Product hardening covers keyboard/focus semantics, assistive loading/error feedback, reduced motion, long-content containment and 1024/1280/1600 desktop widths. Five provenance-bound 1536x960 browser goldens remain the pre-refactor implementation baseline, not the final premium target.

`PRE_REAL_E2E` requires every J0-J9 browser journey to pass with retained screenshot and Playwright trace, then requires assembled packaged-product evidence for J0/J1/J8/J9. Current integrated evidence reports `READY_FOR_REAL_ENVIRONMENT: YES`; every material UI change must re-establish affected readiness evidence before relying on it.

Hosted fixtures never prove representative hardware/runtime behavior; `RUNTIME-1` remains real-environment evidence.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | PVR-00/PVR-01 ACTIVE | finish implementation audit + `brand-kit` v0.6 visual contract, then unlock shared foundation refactor |
| [Representative device evidence](workstreams/representative-device-evidence.md) | READY | first real LLS/model/device run with retained fingerprint/bundle; re-check current `PRE_REAL_E2E` before execution |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 EVIDENCE BLOCKED / MIG-003 BLOCKED | EV-3 + real PL replacement run, then redundant-path removal/smoke |

## UX/UI baseline

`design/ux-contract.json` remains the settled task/semantic owner. `design/brand-kit.json` is the visual-system owner and will move from v0.5 to v0.6 before implementation CSS changes.

The premium direction is `Precision Instrument`: neutral graphite hierarchy, restrained accent usage, compact controls, deliberate depth, higher evidence density and less default explanatory copy. Linear/Raycast/Vercel are reference qualities only; Performance Lab keeps a distinct evidence language and never invents normalized scores or visual semantics unsupported by backend evidence.

PVR-00 audits real implementation/PRE_REAL screenshots and component ownership. PVR-01 defines the durable v0.6 visual contract in parallel. Shared tokens/primitives/shell stay blocked until both agree; page slices may parallelize only after the common design foundation is integrated.

## Evaluation migration

Post-cutover evaluation evidence belongs to Performance Lab under PL-native identities; existing LLS `general-purpose@1.0.0` evidence remains legacy. Serving, residency, runtime identity/status, provider metrics and hardware/resource correctness remain LLS-owned.

MIG-003 still requires EV-3, a current passing `PRE_REAL_E2E`, a real PL run against LLS and post-disable serving/runtime smoke.

## Integration lines

- `dev` is the integration line; ordinary feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately with `FULL` validation.

## Evidence still required

- PVR-00..08 premium visual implementation and refreshed bounded targets/goldens;
- PVR-09 final accessibility/representative-user acceptance after the visual refactor;
- representative resident-model identity/resource/telemetry/repeated-load evidence;
- LLS EV-3, real PL replacement run and post-disable cross-repository smoke;
- human acceptance where release claims depend on usability.