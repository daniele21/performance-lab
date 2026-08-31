# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-31

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

The browser product now covers use-case-first planning, executable Campaign/results, benchmark/sample drill-down and same-case cross-candidate comparison. Product UX/UI convergence advances to whole-product hardening. Representative-hardware evidence and the evidence-gated Local LLM Server evaluation cutover remain separate active work.

Primary product question:

> For this use case on this device, which available model/configuration gives me the best evidence-backed trade-off, and why?

## Integrated baseline

`dev` contains Overview; Find best setup through frozen campaign review, execution, Results and exact-case comparison; Test a model; Live Run recovery; Runs/Run Detail; Compare; Library/Settings; Benchmark Detail; and Run -> Samples -> Sample Evidence.

Campaign launch revalidates the frozen plan digest, persists reconnectable lifecycle separately from immutable Runs and shares bounded evaluation capacity with manual runs. Results establish dimension-specific compatibility before `strict-quality-dominance@1.0.0`; no single winner is produced unless one candidate uniquely dominates comparable quality evidence.

Campaign Results enumerate retained task/sample identities. Same-case comparison projects candidate/config/Run/sample-attempt evidence in Python and reuses canonical capability compatibility. Missing, incompatible and not-retained evidence remain explicit; no case-level winner or cross-case delta is invented.

Browser J0-J9 acceptance is executable; packaged-product evidence covers J0, J1, J8 and J9 through the installed wheel, built frontend, loopback API, SQLite and deterministic inference fixture. The repository adopts `repo-template-sw` 0.8.0 at L2 with Python, TypeScript and product-ui profiles.

Hosted CI/fixtures do not prove representative hardware/runtime behavior; `RUNTIME-1` remains real-environment evidence.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | ACTIVE | UXUI-09 hardens failure/accessibility/responsive/long-data behavior; UXUI-10 then proves final built-product acceptance |
| [Representative device evidence](workstreams/representative-device-evidence.md) | READY | first real LLS/model/device run with retained fingerprint/bundle |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 EVIDENCE BLOCKED / MIG-003 BLOCKED | retain EV-3 + real PL replacement run, then remove redundant evaluation paths and smoke |

## UX/UI baseline

`design/ux-contract.json` and `design/brand-kit.json` own durable experience truth; approved desktop targets under `design/reference/visual-targets/desktop-standard/` are design intent, not pixel-regression goldens.

Find best setup consumes backend-owned use-case relevance, candidate inventory and deterministic planning. Parameter sweeps remain unavailable without runtime-supplied bounded ranges. Campaign entries resolve to immutable Runs; compatibility and missing evidence appear before recommendation.

Same-case comparison reuses Campaign/Run/sample identity and Python-owned compatibility. Zero matches are unavailable, multiple attempts are not silently chosen, and evaluator/retention state stays attached to the exact attempt.

## Evaluation migration

Post-cutover evaluation evidence belongs to Performance Lab under PL-native identities. Existing LLS `general-purpose@1.0.0` evidence remains legacy. Serving, residency, runtime identity/status, provider metrics and hardware/resource correctness remain LLS-owned.

MIG-003 still requires EV-3 evidence, a real PL run against LLS and post-disable serving/runtime smoke.

## Integration lines

- `dev` is the integration line; ordinary feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately with `FULL` validation.

## Evidence still required

- UXUI-09/10 hardening and final built-product/human acceptance evidence;
- representative resident-model identity/resource/telemetry/repeated-load evidence;
- LLS EV-3, real PL replacement run and post-disable cross-repository smoke;
- human acceptance where release claims depend on usability.
