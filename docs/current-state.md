# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-31

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

The benchmark/evidence core, use-case-first UX/discovery baseline, design-system/brand convergence, canonical desktop IA, Library/Settings convergence, manual evaluation recovery, benchmark/sample evidence drill-down, Find best setup planning, Campaign lifecycle/recommendation and same-case cross-candidate comparison are integrated on `dev`. Product UX/UI convergence now advances to whole-product hardening on top of stable Campaign, immutable Run and sample-evidence contracts. Representative-hardware evidence and the evidence-gated Local LLM Server evaluation cutover remain separate active work.

Primary product question:

> For this use case on this device, which available model/configuration gives me the best evidence-backed trade-off, and why?

## Integrated baseline

`dev` contains Overview; Find best setup from use case through deterministic frozen campaign review, executable Campaign, policy-backed Results and exact-case candidate comparison; Test a model with loopback model discovery and frozen Review; Live Run with server-owned cancel/reconnect recovery; Runs/Run Detail with evidence-first action hierarchy; Compare; canonical Library/Settings navigation; Benchmark Detail with inspectable authored cases/evaluator rules; and Run -> Samples -> Sample Evidence drill-down with explicit retention/explanation states.

Campaign launch revalidates the exact frozen plan digest on the server. Campaign lifecycle is persisted/reconnectable, groups immutable Runs without replacing their identities and shares bounded local evaluation capacity with manual runs. Results establish dimension-specific compatibility before recommendation. `strict-quality-dominance@1.0.0` recommends only a unique candidate that dominates every alternative on comparable quality metrics; otherwise the UI truthfully reports that there is no single winner and keeps quality, runtime performance and resources separate.

Campaign Results enumerate retained benchmark task/sample identities. The same-case drill-down projects model + quantization + frozen config + immutable Run/sample attempt from Python and reuses canonical capability compatibility before placing evidence side by side. Incompatible candidates and unavailable/not-retained content remain explicit; the case surface does not invent a winner or cross-case delta.

Browser J0-J9 acceptance is executable; packaged-product evidence covers J0/J9, J1 and J8 through the installed wheel, built frontend, real loopback API, real SQLite and deterministic external inference fixture. The repository adopts `repo-template-sw` 0.8.0 at L2 with Python, TypeScript and product-ui profiles.

Hosted CI/fixtures do not prove representative hardware/runtime behavior; `RUNTIME-1` remains real-environment evidence.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | ACTIVE | UXUI-09 hardens failure/accessibility/responsive/long-data behavior; UXUI-10 then proves final built-product acceptance |
| [Representative device evidence](workstreams/representative-device-evidence.md) | READY | first real LLS/model/device run with retained fingerprint/bundle |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 EVIDENCE BLOCKED / MIG-003 BLOCKED | retain EV-3 + real PL replacement run, then remove redundant evaluation paths and smoke |

## UX/UI baseline

`design/ux-contract.json` and `design/brand-kit.json` own durable experience truth. Approved desktop targets live under `design/reference/visual-targets/desktop-standard/` and are design intent, not pixel-regression goldens.

The integrated baseline includes use-case-first `Find best setup`, loopback model discovery, canonical shell/IA, converged Library/Settings, manual Run recovery, inspectable Benchmark Detail, Run -> Samples -> Sample Evidence with immutable attempt identity and truthful aggregate-safe content states, Campaign/Results with server-owned lifecycle and explicit decision-policy identity, and same-case cross-candidate evidence comparison.

Find best setup consumes backend-owned use-case/benchmark relevance, candidate inventory and frozen deterministic planning. Parameter sweeps remain unavailable unless the runtime contract supplies bounded ranges. Campaign execution consumes the exact revalidated fixed plan and each matrix entry resolves to an immutable Run. Compatibility and missing evidence are shown before any recommendation; no hidden universal score is introduced.

Same-case comparison reuses Campaign/Run/sample identities and Python-owned capability compatibility. A zero-match candidate is unavailable; multiple retained attempts are not silently chosen; evaluator identity and response-retention state remain attached to the exact attempt.

## Evaluation migration

Post-cutover evaluation evidence belongs to Performance Lab under PL-native identities. Existing LLS `general-purpose@1.0.0` evidence remains legacy and is not automatically relabeled/imported. Serving, residency, runtime identity/status, provider metrics and hardware/resource correctness remain LLS-owned.

MIG-003 still requires post-convergence EV-3 evidence, a real PL run against LLS and post-disable serving/runtime smoke.

## Integration lines

- `dev` is the integration line; ordinary feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately with `FULL` validation.

## Evidence still required

- UXUI-09/10 hardening and final built-product/human acceptance evidence;
- representative resident-model identity/resource/telemetry/repeated-load evidence;
- LLS EV-3, real PL replacement run and post-disable cross-repository smoke;
- human acceptance where release claims depend on usability.
