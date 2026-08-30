# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-30

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

The benchmark/evidence core, use-case-first UX/discovery baseline, design-system/brand convergence, canonical desktop IA, Library/Settings convergence, manual evaluation recovery and backend sample-evidence read models are integrated on `dev`. Product UX/UI convergence now concentrates on Benchmark Detail, Run Samples and Sample Evidence frontend drill-down before campaign planning can begin. Representative-hardware evidence and the evidence-gated Local LLM Server evaluation cutover remain separate active work.

Primary product question:

> For this use case on this device, which available model/configuration gives me the best evidence-backed trade-off, and why?

## Integrated baseline

`dev` contains Overview, Find best setup's truthfully blocked campaign shell, Test a model with loopback model discovery and frozen Review, Live Run with server-owned cancel/reconnect recovery, Runs/Run Detail with evidence-first action hierarchy, Compare, canonical Library/Settings navigation, backend Benchmark/Evaluator definitions, Run -> Samples -> Sample Evidence projections, browser J0-J6 acceptance, deterministic Python Product E2E and the built-product artifact/smoke lifecycle. The repository adopts `repo-template-sw` 0.8.0 at L2 with Python, TypeScript and product-ui profiles.

Hosted CI/fixtures do not prove representative hardware/runtime behavior; `RUNTIME-1` remains real-environment evidence.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | ACTIVE | UXUI-05 frontend Benchmark Detail / Run Samples / Sample Evidence makes J7-J8 executable, then campaign planning can start |
| [Representative device evidence](workstreams/representative-device-evidence.md) | READY | first real LLS/model/device run with retained fingerprint/bundle |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 EVIDENCE BLOCKED / MIG-003 BLOCKED | retain EV-3 + real PL replacement run, then remove redundant evaluation paths and smoke |

## UX/UI baseline

`design/ux-contract.json` and `design/brand-kit.json` own durable experience truth. Approved desktop targets live under `design/reference/visual-targets/desktop-standard/` and are design intent, not pixel-regression goldens.

The integrated baseline includes use-case-first `Find best setup`, loopback model discovery, canonical shell/IA, converged Library/Settings, manual Run recovery, backend Benchmark/Evaluator registries and Run -> Samples -> Sample Evidence projections. The automatic campaign remains intentionally blocked until backend-owned use-case planning, configuration search, campaign lifecycle and compatibility-aware recommendation contracts exist.

UXUI-05 now owns the remaining benchmark/sample frontend drill-down. Campaign planning/lifecycle/recommendation remains sequential because it shares one new product contract.

## Evaluation migration

Post-cutover evaluation evidence belongs to Performance Lab under PL-native identities. Existing LLS `general-purpose@1.0.0` evidence remains legacy and is not automatically relabeled/imported. Serving, residency, runtime identity/status, provider metrics and hardware/resource correctness remain LLS-owned.

MIG-003 still requires post-convergence EV-3 evidence, a real PL run against LLS and post-disable serving/runtime smoke.

## Integration lines

- `dev` is the integration line; ordinary feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately with `FULL` validation.

## Evidence still required

- J7-J9 evidence as benchmark/sample/campaign contracts become executable;
- UXUI-05 frontend drill-down and later campaign/product-hardening evidence;
- representative resident-model identity/resource/telemetry/repeated-load evidence;
- LLS EV-3, real PL replacement run and post-disable cross-repository smoke;
- human acceptance where release claims depend on usability.
