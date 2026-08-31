# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-31

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

The browser product now covers use-case-first planning, executable Campaign/results, benchmark/sample drill-down, same-case cross-candidate comparison and whole-product interaction hardening. Product UX/UI convergence advances to final built-product acceptance and implementation goldens. Representative-hardware evidence and the evidence-gated Local LLM Server evaluation cutover remain separate active work.

Primary product question:

> For this use case on this device, which available model/configuration gives me the best evidence-backed trade-off, and why?

## Integrated baseline

`dev` contains Overview; Find best setup through frozen campaign review, execution, Results and exact-case comparison; Test a model; Live Run recovery; Runs/Run Detail; Compare; Library/Settings; Benchmark Detail; and Run -> Samples -> Sample Evidence.

Campaign launch revalidates the frozen plan digest, persists reconnectable lifecycle separately from immutable Runs and shares bounded evaluation capacity with manual runs. Results establish dimension-specific compatibility before `strict-quality-dominance@1.0.0`; no single winner is produced unless one candidate uniquely dominates comparable quality evidence.

Campaign Results enumerate retained task/sample identities. Same-case comparison projects candidate/config/Run/sample-attempt evidence in Python and reuses canonical capability compatibility. Missing, incompatible and not-retained evidence remain explicit; no case-level winner or cross-case delta is invented.

Shared product hardening now provides keyboard skip navigation, route-change focus restoration, assistive semantics for loading/error states, reduced-motion behavior and long technical-content containment. Browser evidence exercises recoverable failure, the supported 1024/1280/1600 desktop widths, extreme model/run/case identities, long case content and dense evaluator evidence without recreating backend semantics.

Browser J0-J9 acceptance is executable; packaged-product evidence covers J0, J1, J8 and J9 through the installed wheel, built frontend, loopback API, SQLite and deterministic inference fixture. The repository adopts `repo-template-sw` 0.8.0 at L2 with Python, TypeScript and product-ui profiles.

Hosted CI/fixtures do not prove representative hardware/runtime behavior; `RUNTIME-1` remains real-environment evidence.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | ACTIVE | UXUI-10 performs final built-product acceptance, manual accessibility/usability review where required and approved implementation goldens |
| [Representative device evidence](workstreams/representative-device-evidence.md) | READY | first real LLS/model/device run with retained fingerprint/bundle |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 EVIDENCE BLOCKED / MIG-003 BLOCKED | retain EV-3 + real PL replacement run, then remove redundant evaluation paths and smoke |

## UX/UI baseline

`design/ux-contract.json` and `design/brand-kit.json` own durable experience truth; approved desktop targets under `design/reference/visual-targets/desktop-standard/` are design intent, not pixel-regression goldens.

Find best setup consumes backend-owned use-case relevance, candidate inventory and deterministic planning. Parameter sweeps remain unavailable without runtime-supplied bounded ranges. Campaign entries resolve to immutable Runs; compatibility and missing evidence appear before recommendation.

Same-case comparison reuses Campaign/Run/sample identity and Python-owned compatibility. Zero matches are unavailable, multiple attempts are not silently chosen, and evaluator/retention state stays attached to the exact attempt.

UXUI-09 hardening is integrated at shared shell/state/foundation owners: keyboard focus remains visible and recoverable, loading/error feedback is announced semantically, reduced motion is respected and long evidence remains contained across compact/standard/wide desktop contexts. Manual assistive-technology/contrast review and reference-grade implementation screenshots remain UXUI-10 evidence rather than automated claims.

## Evaluation migration

Post-cutover evaluation evidence belongs to Performance Lab under PL-native identities. Existing LLS `general-purpose@1.0.0` evidence remains legacy. Serving, residency, runtime identity/status, provider metrics and hardware/resource correctness remain LLS-owned.

MIG-003 still requires EV-3 evidence, a real PL run against LLS and post-disable serving/runtime smoke.

## Integration lines

- `dev` is the integration line; ordinary feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately with `FULL` validation.

## Evidence still required

- UXUI-10 final built-product/manual accessibility/usability and approved implementation-golden evidence;
- representative resident-model identity/resource/telemetry/repeated-load evidence;
- LLS EV-3, real PL replacement run and post-disable cross-repository smoke;
- human acceptance where release claims depend on usability.
