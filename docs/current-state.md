# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-30

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

The benchmark/evidence core, use-case-first UX/discovery baseline, design-system/brand convergence, canonical desktop IA, Library/Settings convergence, manual evaluation recovery, benchmark/sample evidence drill-down and Find best setup planning are integrated on `dev`. Product UX/UI convergence now advances to campaign lifecycle and recommendation on top of the frozen use-case -> candidate models -> configuration search -> benchmark plan -> campaign review/estimate contract. Representative-hardware evidence and the evidence-gated Local LLM Server evaluation cutover remain separate active work.

Primary product question:

> For this use case on this device, which available model/configuration gives me the best evidence-backed trade-off, and why?

## Integrated baseline

`dev` contains Overview, executable Find best setup planning through a deterministic frozen campaign review/estimate, Test a model with loopback model discovery and frozen Review, Live Run with server-owned cancel/reconnect recovery, Runs/Run Detail with evidence-first action hierarchy, Compare, canonical Library/Settings navigation, Benchmark Detail with inspectable authored cases/evaluator rules, and Run -> Samples -> Sample Evidence drill-down with explicit retention/explanation states. Campaign execution remains intentionally disabled until UXUI-07 owns lifecycle and recommendation. Browser J0-J8 acceptance is executable; packaged-product evidence covers J0, J1 and J8 through the installed wheel, built frontend, real loopback API, real SQLite and deterministic external inference fixture. The repository adopts `repo-template-sw` 0.8.0 at L2 with Python, TypeScript and product-ui profiles.

Hosted CI/fixtures do not prove representative hardware/runtime behavior; `RUNTIME-1` remains real-environment evidence.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | ACTIVE | UXUI-07 makes frozen campaign plans executable and produces compatibility-aware results/recommendations; UXUI-08 then owns same-case cross-candidate comparison |
| [Representative device evidence](workstreams/representative-device-evidence.md) | READY | first real LLS/model/device run with retained fingerprint/bundle |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 EVIDENCE BLOCKED / MIG-003 BLOCKED | retain EV-3 + real PL replacement run, then remove redundant evaluation paths and smoke |

## UX/UI baseline

`design/ux-contract.json` and `design/brand-kit.json` own durable experience truth. Approved desktop targets live under `design/reference/visual-targets/desktop-standard/` and are design intent, not pixel-regression goldens.

The integrated baseline includes use-case-first `Find best setup`, loopback model discovery, canonical shell/IA, converged Library/Settings, manual Run recovery, inspectable Benchmark Detail, and Run -> Samples -> Sample Evidence with immutable attempt identity and truthful aggregate-safe content states. Find best setup now consumes backend-owned use-case/benchmark relevance, candidate inventory and frozen deterministic planning. Parameter sweeps remain unavailable unless the runtime contract supplies bounded ranges, and campaign execution/recommendation remains intentionally blocked until UXUI-07.

UXUI-07 now owns campaign lifecycle/recommendation. Same-case cross-candidate comparison remains downstream of campaign execution.

## Evaluation migration

Post-cutover evaluation evidence belongs to Performance Lab under PL-native identities. Existing LLS `general-purpose@1.0.0` evidence remains legacy and is not automatically relabeled/imported. Serving, residency, runtime identity/status, provider metrics and hardware/resource correctness remain LLS-owned.

MIG-003 still requires post-convergence EV-3 evidence, a real PL run against LLS and post-disable serving/runtime smoke.

## Integration lines

- `dev` is the integration line; ordinary feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately with `FULL` validation.

## Evidence still required

- J9 evidence after campaign execution and same-case cross-candidate comparison become executable;
- UXUI-07 lifecycle/recommendation, UXUI-08 same-case comparison and UXUI-09/10 hardening/acceptance evidence;
- representative resident-model identity/resource/telemetry/repeated-load evidence;
- LLS EV-3, real PL replacement run and post-disable cross-repository smoke;
- human acceptance where release claims depend on usability.
