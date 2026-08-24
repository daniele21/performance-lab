# Local LLM Server evaluation migration

Status: active
Owner: Performance Lab / Local LLM Server integration
Canonical scope: migration.lls-evaluation
Last reviewed: 2026-08-24

## Goal

Move overlapping benchmark/evaluation responsibilities from Local LLM Server to Performance Lab without breaking required workflows, losing retained evidence or moving model-serving ownership into Performance Lab.

Performance Lab is the evaluation product. Local LLM Server remains the inference/runtime provider.

## Durable owners

- [`../adr/0004-performance-lab-owns-evaluation-product.md`](../adr/0004-performance-lab-owns-evaluation-product.md) — long-term ownership decision;
- [`../local-llm-server-integration.md`](../local-llm-server-integration.md) — integration boundary;
- [`../architecture.md`](../architecture.md) — Performance Lab ownership/dependency rules;
- [`../../design/ux-contract.json`](../../design/ux-contract.json) — shipped evaluation task model.

## Migration gates

| Task | State | Depends on | Acceptance |
| --- | --- | --- | --- |
| MIG-001 parity map | **DONE** | integrated Performance Lab product | LLS evaluation workflows classified; data/history/consumer dependencies and non-overlapping runtime evidence identified |
| MIG-002 replacement + deprecation | **IMPLEMENTATION DONE / EVIDENCE-BLOCKED** | MIG-001 + representative real-runtime evidence | replacement/history/non-parity policy fixed and Studio redirect integrated; remaining gates are EV-3 plus the real PL replacement run |
| MIG-003 remove redundant evaluation paths | **BLOCKED** | MIG-002 evidence gates | EV-3 retained; no required consumer depends on removed behavior; cross-repo real-runtime smoke green; serving/runtime responsibilities intact |

## MIG-001 parity map

| Local LLM Server capability / owner | Classification | Performance Lab replacement / action | Migration constraint |
| --- | --- | --- | --- |
| `evaluation.py`: sample/test-set/selection/score/run-manifest contracts | **MIGRATE / REMOVE AFTER REPLACEMENT** | canonical `DatasetSnapshot`, `EvaluationSuite`, `TaskSpec`, evaluator refs, execution fingerprints and immutable run evidence | old contracts remain readable with legacy history until LLS removal gate |
| `evaluation_builtin.py`: `general-purpose@1.0.0` + deterministic scorer | **TRANSITIONAL RETAIN** | future evaluations use Performance Lab-owned suites with their own identities | frozen until LLS EV-3; no false relabel/import as `general-diagnostic-starter` |
| `evaluation_testsets.py`: custom test-set upload/store | **REPLACE, NOT FEATURE-CLONE** | versioned PL JSONL/CSV import, explicit mappings/sampling and evaluator-owned scoring | exact legacy expectation vocabulary is not a migration requirement unless a real retained consumer is identified |
| `evaluation_service.py` + `evaluation_runner.py` | **MIGRATE** | Performance Lab run engine evaluates the external endpoint and freezes model/runtime/device/dataset/evaluator identity | LLS keeps model residency, request execution and capability truth |
| `evaluation_reasoning.py` | **DROP EVAL-SPECIFIC POLICY BY DEFAULT / RETAIN RUNTIME CAPABILITY** | future PL evaluation uses PL-native configuration; provider-supported thinking remains LLS runtime truth | do not build a legacy adapter unless a retained consumer/use case requires exact ON/OFF reproduction |
| evaluation store/history/comparison | **HISTORICAL LLS / NEW RUNS PL** | PL SQLite store, `.plab.zip`, Runs/Run Detail/Compare for all new PL evidence | no automatic history import in the initial migration; no cross-product comparability claim |
| `/api/v1/evaluation/history*` | **TRANSITIONAL READ PATH** | PL run/read/comparison APIs for new evidence | keep until EV-3/removal gate; legacy reports remain LLS historical evidence |
| evaluation run/test-set HTTP endpoints | **DEPRECATE AFTER REPLACEMENT EVIDENCE** | PL Test a model + canonical run API/CLI | cross-repo smoke must prove LLS serving/identity/status are sufficient after evaluation routes are disabled |
| Studio `control-plane-evaluation*` and history UI | **REDIRECTED / TRANSITIONAL** | PL Test/Live Run/Runs/Run Detail/Compare/Library | LLS PR #149 adds the visible PL transition notice while deliberately retaining EV-3 and legacy history behavior |
| evaluation unit/UI tests | **REMOVE WITH OWNER** | PL dataset/evaluator/run/browser tests plus retained LLS runtime tests | remove only tests whose production owner disappears |
| `test_inference.py`, `inference_test_config.json`, `inference_results_report.json` | **LEGACY / ARCHIVE OR DROP** | PL CLI/product evidence bundles | not canonical current evaluation evidence; do not import into PL run history |
| `/v1/models`, `/v1/chat/completions` | **RETAIN OPERATIONAL** | consumed by PL OpenAI-compatible adapter | core LLS serving contract |
| `/v1/runtime/identity` | **RETAIN OPERATIONAL** | consumed into PL `ExecutionFingerprint` | first-party provider evidence, not evaluation duplication |
| `/status`, completion/streaming/runtime metrics | **RETAIN OPERATIONAL** | sampled by PL runtime telemetry integration | provider-observed provenance remains explicit |
| hardware/resource/reclamation/admission evidence | **RETAIN OPERATIONAL** | may be correlated by PL but remains LLS runtime correctness evidence | current representative-device campaign depends on these contracts |

## MIG-002 decisions

### History boundary: historical LLS, new evidence PL

The migration deliberately does **not** import arbitrary Local LLM Server evaluation JSON into Performance Lab's canonical run store.

- Existing and EV-3 LLS reports remain immutable **legacy LLS evidence** under their original contracts.
- Performance Lab owns all new evaluation evidence after cutover and persists it under PL-native dataset/suite/evaluator/fingerprint identities.
- `general-purpose@1.0.0` and `general-diagnostic-starter` are distinct experiments. They are never relabeled as equivalent and are not compared as if they shared an evidence contract.
- A future one-time importer is justified only by a concrete archival/query requirement; it is not part of MIG-002/MIG-003 by default.
- Legacy root `inference_results_report.json` is not promoted into canonical PL history.

This keeps provenance truthful and avoids a compatibility layer whose only purpose would be cosmetic history continuity.

### Replacement is capability-oriented, not feature-for-feature cloning

Performance Lab already replaces the core user outcome: choose a model/configuration, run a versioned evaluation against an external endpoint, inspect immutable evidence and compare compatible runs.

Legacy LLS-specific mechanics are intentionally **not** copied unless a current consumer requires them:

- custom expectation keys (`exact`, `exact_ci`, `contains`, `word_count`, `comma_count`, `json`) may be translated to PL-native dataset/evaluator contracts when needed, but the old upload JSON schema is not itself a product requirement;
- LLS evaluation reasoning policy (`enable_thinking` / `show_thinking`) is not reproduced automatically. Runtime support/capability remains LLS-owned; PL gains an explicit integration control only if an actual replacement workflow requires it;
- per-sample LLS `CHAT` vs `STRUCTURED_GENERATION` request semantics make exact legacy-suite replay a separate compatibility feature, not a prerequisite for the new product owner.

### Repository-known consumers and redirect

The source repository proves these current consumers:

- Studio `control-plane-evaluation.js` calls evaluation test-set list/import and run endpoints and presents current-session results;
- Studio `control-plane-evaluation-history.js` calls history list/detail/compare endpoints;
- evaluation API/service/history/UI tests exercise those same owners;
- the active device-evidence runbook/workstream requires the frozen EV-3 path.

No additional external consumer can be established from repository contents. LLS PR #149 now provides the visible, non-destructive transition notice: new evaluation work is directed to Performance Lab while the current EV-3 path and legacy history remain available. The PR passed Ruff, Python 3.10/3.11/3.12 and Playwright E2E before merge.

## Remaining executable MIG-002 evidence work

1. **Finish EV-3 on the real device.** Retain the two post-convergence `general-purpose@1.0.0 / 10 / seed 0 / reasoning off` reports before touching the legacy owner.
2. **Run the PL replacement path on a real LLS endpoint.** Require runtime identity, sample `/status`, retain the PL fingerprint and `.plab.zip`, and verify the new run appears in PL Runs/Run Detail.
3. **Freeze legacy history at cutover.** Once no new LLS evaluation run is required, stop creating legacy evaluation evidence; preserve the retained reports as historical artifacts according to the LLS release/archive policy.
4. **Cross-repo smoke after disable/removal.** Prove `/v1/models`, `/v1/chat/completions`, `/v1/runtime/identity`, `/status` and runtime/resource correctness remain intact while PL evaluation still works.

## Current blockers

MIG-002 has no remaining architecture, history-policy, consumer-inventory or redirect implementation gap. It is evidence-blocked only: Local LLM Server still requires EV-3 on the frozen legacy evaluation contract, and Performance Lab's representative-device workstream still lacks a real cross-repository run. Browser/fixture CI cannot satisfy either claim.

MIG-003 therefore remains intentionally blocked. No additional compatibility implementation is justified before those evidence gates; building an exact legacy suite/reasoning adapter now would add a second semantic path without a demonstrated consumer.

## Migration rules

- Do not delete before consumer and real-runtime evidence exists.
- Do not copy serving/runtime ownership into Performance Lab.
- Preserve legacy history under its original identity; never silently rewrite provenance.
- New PL runs use PL-native evidence contracts; do not claim cross-product comparability without an explicit compatibility protocol.
- Add compatibility adapters only for demonstrated retained requirements.
- Keep the redirect visible until the old surface is removed.
- Cross-repository claims require evidence from both products, not only fixture/unit tests.

## Completion gate

Complete when EV-3 and the representative PL real-runtime run are retained, redundant LLS evaluation behavior is disabled/removed without affecting serving/runtime behavior, and the final cross-repository smoke is green.

After completion, transfer durable migration outcomes to integration/ADR docs, update `current-state.md`, and delete this workstream by default.
