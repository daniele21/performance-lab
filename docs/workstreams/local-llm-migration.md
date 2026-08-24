# Local LLM Server evaluation migration

Status: active
Owner: Performance Lab / Local LLM Server integration
Canonical scope: migration.lls-evaluation
Last reviewed: 2026-08-24

## Goal

Move overlapping benchmark/evaluation responsibilities from Local LLM Server to Performance Lab without breaking required workflows, losing retained evidence or moving model-serving ownership into Performance Lab.

Performance Lab is the evaluation product. Local LLM Server remains an inference/runtime provider where that role is useful.

## Durable owners

- [`../adr/0004-performance-lab-owns-evaluation-product.md`](../adr/0004-performance-lab-owns-evaluation-product.md) — long-term ownership decision;
- [`../local-llm-server-integration.md`](../local-llm-server-integration.md) — integration boundary;
- [`../architecture.md`](../architecture.md) — Performance Lab ownership/dependency rules;
- [`../../design/ux-contract.json`](../../design/ux-contract.json) — shipped evaluation task model.

## Migration gates

| Task | State | Depends on | Acceptance |
| --- | --- | --- | --- |
| MIG-001 parity map | **DONE** | integrated Performance Lab product | LLS evaluation workflows classified; data/history/consumer dependencies and non-overlapping runtime evidence identified |
| MIG-002 replacement + deprecation | READY / EVIDENCE-BLOCKED | MIG-001 + representative real-runtime evidence | required migrated workflows are usable in Performance Lab; users/consumers have a documented replacement path; retained history policy is explicit |
| MIG-003 remove redundant evaluation paths | BLOCKED | MIG-002 | no required consumer depends on removed LLS evaluation behavior; cross-repo E2E and real-runtime smoke are green; serving/runtime responsibilities remain intact |

## MIG-001 parity map

The current Local LLM Server repository contains a complete evaluation subsystem rather than only legacy scripts. The classification below is intentionally capability-based so removal does not erase runtime evidence that still belongs to the serving product.

| Local LLM Server capability / owner | Classification | Performance Lab replacement / action | Migration constraint |
| --- | --- | --- | --- |
| `evaluation.py`: sample/test-set/selection/score/run-manifest contracts | **MIGRATE / REMOVE AFTER PARITY** | canonical `DatasetSnapshot`, `EvaluationSuite`, `TaskSpec`, evaluator refs, immutable execution fingerprints and run evidence | LLS contracts remain readable until stored-history policy is resolved |
| `evaluation_builtin.py`: `general-purpose@1.0.0` + deterministic objective scorer | **TRANSITIONAL RETAIN** | Performance Lab already has versioned authored diagnostic datasets + deterministic evaluators, but not the same frozen dataset identity | do not remove before the LLS EV-3 real-device campaign using `general-purpose@1.0.0`, 10 samples, seed 0, reasoning off is complete; afterwards freeze/import exact content for continuity or declare it historical-only |
| `evaluation_testsets.py`: validated custom test-set upload/store | **MIGRATE / PARTIAL PARITY** | Performance Lab supports versioned JSONL/CSV dataset import, explicit mappings/sampling and evaluator-owned scoring | map LLS expectation vocabulary (`exact`, `exact_ci`, `contains`, `word_count`, `comma_count`, `json`) to supported Performance Lab evaluator/config paths; do not promise UI upload parity because Library is currently read-only |
| `evaluation_service.py` + `evaluation_runner.py`: resident-runtime evaluation execution | **MIGRATE** | Performance Lab run engine evaluates the external OpenAI-compatible endpoint and freezes runtime/device/dataset/evaluator identity | LLS keeps runtime residency, request execution and capability truth; Performance Lab must not absorb model loading/lease ownership |
| `evaluation_reasoning.py`: evaluation-specific reasoning policy/profile | **MIGRATE POLICY / RETAIN RUNTIME CAPABILITY** | evaluation configuration belongs in Performance Lab; effective reasoning/thinking support remains an LLS serving capability | current Performance Lab `GenerationConfig` does not encode LLS `enable_thinking/show_thinking`; MIG-002 needs an explicit bounded adapter/config mapping before reasoning-policy parity is claimed |
| `EvaluationStore`, `evaluation_history.py`, `evaluation_history_service.py` | **MIGRATE HISTORY OWNERSHIP** | Performance Lab immutable SQLite run store, portable `.plab.zip`, Runs/Run Detail and compatibility-first Compare | existing LLS JSON reports are historical evidence; choose import/side-by-side read-only archive/explicit retirement before removal |
| `/api/v1/evaluation/history*` | **DEPRECATE AFTER REPLACEMENT** | Performance Lab run/read/comparison APIs and browser surfaces | retain until known UI/API consumers are redirected and history policy is explicit |
| evaluation run/test-set HTTP endpoints installed by LLS server | **DEPRECATE AFTER REPLACEMENT** | Performance Lab Test a model + canonical run API/CLI | cross-repo smoke must prove LLS inference/identity/status remain sufficient after evaluation routes are disabled |
| `static/control-plane-evaluation*` and evaluation-history UI | **DEPRECATE AFTER REPLACEMENT** | Performance Lab Test/Live Run/Runs/Run Detail/Compare/Library | add user-facing replacement path before removal; no dead navigation or hidden consumer |
| evaluation unit/UI tests | **REMOVE WITH OWNER** | corresponding Performance Lab dataset/evaluator/run/browser tests | LLS retains only tests for serving/runtime contracts that remain its responsibility |
| `test_inference.py`, `inference_test_config.json`, `inference_results_report.json` | **INTENTIONALLY DROP OR ARCHIVE** | Performance Lab CLI/product run + retained evidence bundles | first confirm no automation/docs consumer; historical report must not be presented as current representative evidence |
| `/v1/models`, `/v1/chat/completions` | **RETAIN OPERATIONAL** | consumed by Performance Lab OpenAI-compatible adapter | core LLS serving contract |
| `/v1/runtime/identity` and artifact/runtime identity modules | **RETAIN OPERATIONAL** | consumed into Performance Lab `ExecutionFingerprint` | first-party provider evidence; not evaluation duplication |
| `/status`, completion/streaming/runtime metrics | **RETAIN OPERATIONAL** | sampled by Performance Lab runtime telemetry integration | provider-observed metrics keep provenance and must not be re-owned by the lab |
| hardware/resource/reclamation/admission evidence | **RETAIN OPERATIONAL** | may be correlated/referenced by Performance Lab but remains LLS runtime correctness evidence | current LLS representative-device campaign depends on these contracts |

## MIG-002 executable scope

MIG-002 can start without deleting anything, but it cannot be declared complete until the real-runtime evidence gate is satisfied.

1. **Freeze the legacy evidence boundary.** Treat `general-purpose@1.0.0` and existing LLS JSON history as immutable migration inputs; no silent semantic rewrite.
2. **Decide exact dataset continuity.** Either import/freeze the exact 20-sample `general-purpose@1.0.0` content in Performance Lab under an explicit legacy identity, or document that completed LLS reports remain historical-only and future runs use the Performance Lab diagnostic suite.
3. **Map reasoning policy explicitly.** Add a bounded Local LLM Server generation/config adapter if Performance Lab must reproduce `reasoning off/on`; do not infer it from filenames or model names.
4. **Define history handling.** Prefer an explicit one-time importer or documented read-only archive. Do not make Performance Lab parse arbitrary LLS storage directories at runtime.
5. **Redirect consumers.** LLS evaluation UI/API must point to the supported Performance Lab workflow before route/code removal.
6. **Run cross-repo acceptance.** Use a real Local LLM Server endpoint with identity + status enabled, execute the replacement Performance Lab flow, retain the bundle/fingerprint and verify LLS serving/runtime behavior remains intact.

## Current blockers

MIG-003 is intentionally blocked. Local LLM Server's current correctness evidence plan still requires new real-device evaluation evidence, including EV-3 on the frozen `general-purpose@1.0.0` set. Removing its evaluation subsystem before that evidence is retained would invalidate the active evidence workflow rather than simplify ownership.

Performance Lab's representative-device workstream is also still open. Fixture/browser CI proves product behavior but cannot satisfy this cross-repository real-runtime gate.

## Migration rules

- Do not delete before parity/consumer evidence exists.
- Do not copy serving/runtime ownership into Performance Lab to make migration easier.
- Preserve or explicitly retire durable evidence/history; never silently orphan it.
- Keep compatibility adapters explicit and bounded if temporary coexistence is required.
- Deprecation messaging must point users to the supported Performance Lab path before removal.
- Cross-repository claims require evidence from both sides of the integration, not only unit tests in Performance Lab.

## Completion gate

Complete when redundant LLS evaluation behavior is either migrated, deliberately retained for a documented non-overlapping reason, or intentionally removed with consumer/history evidence; the final integration smoke is green on a real runtime path.

After completion, transfer durable migration outcomes to the integration/ADR docs, update `current-state.md`, and delete this workstream by default.
