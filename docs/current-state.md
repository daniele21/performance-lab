# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-09-01

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

The premium `Precision Instrument` browser experience is integrated in `dev`. The visual refactor itself, deterministic visual acceptance and final automated browser/PRE_REAL/package evidence are complete. Product-experience work now has one remaining gate: representative human accessibility/usability acceptance before any reference-grade human UX claim.

Primary product question:

> For this use case on this device, which available model/configuration gives me the best evidence-backed trade-off, and why?

## Integrated baseline

`dev` contains Overview; Find best setup through frozen Campaign review/execution/Results/exact-case comparison; Test a model; Live Run recovery; Runs/Run Detail; Compare; Library/Settings; Benchmark Detail; and Run -> Samples -> Sample Evidence.

Campaigns revalidate frozen plan digests, persist reconnectable lifecycle separately from immutable Runs and apply compatibility before `strict-quality-dominance@1.0.0`. Same-case comparison stays tied to candidate/config/Run/sample-attempt identity; missing, incompatible and not-retained evidence remain explicit.

The browser now uses the v0.6 graphite `Precision Instrument` visual system. Five provenance-bound v0.6 target-backed goldens cover Overview, Test a model frozen review, Benchmark Detail, Sample Evidence Detail and Campaign Results. Product hardening covers keyboard/focus semantics, assistive loading/error feedback, reduced motion, long-content containment and 1024/standard/1600 desktop contexts.

E2E contract 0.1.1 requires screenshot and video artifacts for UI journeys. Current integrated evidence is fully green: Browser Acceptance is 20/20 with screenshot/video/trace retained, PRE_REAL browser J0-J9 passes with retained media, packaged J0/J1/J8/J9 passes with retained media, and the finalizer reports `READY_FOR_REAL_ENVIRONMENT: YES`.

Hosted fixtures never prove representative hardware/runtime behavior; `RUNTIME-1` remains separate real-environment evidence.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | PVR-00..08 DONE / PVR-09 automated + agent media review DONE / human acceptance PENDING | representative human review at supported desktop contexts; on PASS finalize and delete the workstream |
| [Representative device evidence](workstreams/representative-device-evidence.md) | READY | first real LLS/model/device run with retained fingerprint/bundle; re-check current `PRE_REAL_E2E` before execution |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 EVIDENCE BLOCKED / MIG-003 BLOCKED | EV-3 + real PL replacement run, then redundant-path removal/smoke |

## UX/UI baseline

`design/ux-contract.json` remains the settled task/semantic owner. `design/brand-kit.json` v0.6 owns the integrated visual system. The current direction is `Precision Instrument`: neutral graphite hierarchy, restrained accent usage, compact controls, deliberate depth, higher evidence density and less default explanatory copy while preserving truthful evidence semantics.

Final retained browser/PRE_REAL/package screenshots and videos were inspected after CI. They show the expected complete transitions for campaign planning/results, model connection/run, failure recovery, cancellation/restart, progressive secondary navigation, supported desktop containment and packaged-product evidence flow, with no blocking regression found. This is agent-reviewed evidence, not representative-human acceptance; `human_reference_grade_claim` remains false until the human gate is recorded.

## Evaluation migration

Post-cutover evaluation evidence belongs to Performance Lab under PL-native identities; existing LLS `general-purpose@1.0.0` evidence remains legacy. Serving, residency, runtime identity/status, provider metrics and hardware/resource correctness remain LLS-owned.

MIG-003 still requires EV-3, a current passing `PRE_REAL_E2E`, a real PL run against LLS and post-disable serving/runtime smoke.

## Integration lines

- `dev` is the integration line; ordinary feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately with `FULL` validation.

## Evidence still required

- PVR-09 representative human accessibility/usability acceptance before a reference-grade human UX claim;
- representative resident-model identity/resource/telemetry/repeated-load evidence;
- LLS EV-3, real PL replacement run and post-disable cross-repository smoke;
- any other human acceptance only where a release claim explicitly depends on it.
