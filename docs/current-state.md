# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-09-05

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

Performance Lab is converging the remaining **software** for the local text-generation product before one consolidated `REAL_ENVIRONMENT` phase.

Primary product question:

> For this use case on this device, which available model + quantization + supported configuration gives me the best evidence-backed trade-off, and why?

Deterministic software slices may integrate incrementally on `dev`; representative device/model acceptance happens only after planned software convergence and a fresh exact-head PRE_REAL on the final candidate.

## Integrated baseline

Current integration head: `dev@01613d0fdc36f230e192ca8586ed360e65619b3a`.

`dev` contains the decision-first desktop product: Overview; Find best setup; Test a model; Live Run; Runs/Run Detail/Sample Evidence; Compare; Library/Settings; Light/Dark/System appearance; immutable package lifecycle and configless distributed launch.

Quality, Performance and Resources remain separate. Compatibility precedes recommendation/deltas; unavailable, incompatible and not-retained evidence remain explicit.

## Software convergence status

- **VALUE-01 SOFTWARE DONE** — #117/#118/#119 integrated; #120 representative execution deferred.
- **VALUE-02 SOFTWARE DONE** — #129/#130/#131 integrated; #132 representative multi-model decision deferred.
- **VALUE-03 ACTIVE** — declared generation domains and frozen `configuration_id` are integrated. Remaining: deterministic non-Fixed configuration expansion + Optimization/Review UX. Quick/Standard/Thorough/Custom sampling/cardinality semantics remain a material contract and must not be invented.
- **VALUE-04 ACTIVE** — A/B integrated through PR #153 / `4c66541e2057f21afafc9e99828c6d7ed8518ce8`. Resources now distinguish policy-eligible evidence from contextual telemetry. Remaining: VALUE-04C versioned decision-policy extension; exact resource influence/tie-break semantics remain a material policy decision.
- **VALUE-08 A/B/C SOFTWARE DONE** — artifact-owned launcher, configless first run, safe loopback preferences and distributed ZIP acceptance are integrated. VALUE-08D representative install/use smoke is deferred.
- **VALUE-07** — pre-cutover implementation/redirect is done; destructive migration remains blocked by its real cross-repository evidence gates.

VALUE-05/06 are next for software decomposition around the already implemented performance/statistics and regression engines rather than new parallel implementations.

## Current frontier

```text
current dev
-> finish remaining VALUE-03 software
-> finish VALUE-04C policy software
-> close only missing VALUE-05/06 product orchestration/projection
-> keep VALUE-07 destructive cutover evidence-gated
-> converge docs/contracts/tests on final dev
-> fresh exact-head PRE_REAL/Built Product
-> consolidated REAL_ENVIRONMENT acceptance
```

Older PRE_REAL artifacts are historical diagnostics after later `dev` movement, not readiness evidence for the final real phase.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Incremental value delivery](workstreams/incremental-value-delivery.md) | software convergence ACTIVE | finish deterministic software, then final-dev PRE_REAL |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | automated acceptance PASS | representative human accessibility/usability acceptance |
| [Representative device evidence](workstreams/representative-device-evidence.md) | real phase DEFERRED | final-dev PRE_REAL, then retained real runs |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-002 evidence-blocked / MIG-003 blocked | EV-3 + real PL replacement + post-disable smoke |

## Delivery model

- `dev` is the software integration line; `main` remains stable/release-oriented.
- Repository-owned deterministic gates prove software semantics, not representative hardware/model claims.
- `REAL_ENVIRONMENT` is a final phase after planned software convergence, not a prerequisite for each intermediate merge.
- Parallel work needs non-conflicting ownership and one convergence gate.
- Do not invent product/policy semantics or broad subsystems for later slices.

## Evidence still required after software convergence

- fresh exact-head PRE_REAL/Built Product on final candidate `dev`;
- VALUE-01D, VALUE-02D, VALUE-03D and VALUE-04D/EVID-003 representative runs;
- VALUE-05 repeatability/variability and VALUE-06 real regression-policy evidence;
- VALUE-08D clean install/use smoke;
- representative human accessibility/usability acceptance;
- LLS EV-3 + real PL replacement + post-disable cross-repository smoke before VALUE-07 cutover;
- branch protection/admin work in #61.
