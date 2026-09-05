# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-09-05

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

Performance Lab is converging the remaining **software** for the local text-generation product before consolidated release-time `REAL_ENVIRONMENT` acceptance.

Primary product question:

> For this use case on this device, which available model + quantization + supported configuration gives me the best evidence-backed trade-off, and why?

Deterministic software slices integrate incrementally on `dev` after affected automated gates pass. Representative runtime/device/model claims are deferred to release after software convergence and a fresh exact-head PRE_REAL.

## Integrated baseline

The integration line is `dev`, currently on the adopted repo-template-sw **0.9.2** operating contract. Integration requires affected automated E2E; required `REAL_ENVIRONMENT` evidence does not block entry to `dev` and gates release instead.

`dev` contains the decision-first desktop product: Overview; Find best setup; Test a model; Live Run; Runs/Run Detail/Sample Evidence; Compare; Library/Settings; Light/Dark/System appearance; immutable package lifecycle and configless distributed launch.

Quality, Performance and Resources remain separate. Compatibility precedes recommendation/deltas; unavailable, incompatible and not-retained evidence remain explicit.

## Software convergence status

- **VALUE-01 SOFTWARE DONE** — #117/#118/#119 integrated; #120 representative execution deferred.
- **VALUE-02 SOFTWARE DONE** — #129/#130/#131 integrated; #132 representative multi-model decision deferred.
- **VALUE-03 ACTIVE** — declared generation domains and frozen `configuration_id` are integrated. Remaining non-Fixed sampling/cardinality semantics are a material contract and must not be invented.
- **VALUE-04 ACTIVE** — A/B integrated through #153. Resources distinguish policy-eligible evidence from contextual telemetry. VALUE-04C resource influence/tie-break semantics still require an explicit versioned policy.
- **VALUE-05 SOFTWARE DONE** — A/B/C through #167: same-inference client measurements, exact-fingerprint repeatability projection, explicit failure/cancellation denominators and Run Detail variability UX. VALUE-05D / EVID-002 representative repeated-load evidence is release-deferred.
- **VALUE-06 SOFTWARE DONE** — policy-backed regression projection, Compare outcome/rule rationale and deterministic PASS/FAIL/NOT_COMPARABLE acceptance are integrated through #164. VALUE-06D / EVID-004 is release-deferred.
- **VALUE-08 A/B/C SOFTWARE DONE** — artifact-owned launcher, configless first run, safe loopback preferences and distributed ZIP acceptance are integrated. VALUE-08D representative install/use smoke is deferred.
- **VALUE-07** — pre-cutover implementation/redirect is done; destructive migration remains blocked by its real cross-repository evidence gates.

## Current frontier

```text
current dev
-> resolve + finish remaining VALUE-03 software contract
-> resolve + finish VALUE-04C policy contract
-> keep VALUE-07 destructive cutover evidence-gated
-> converge docs/contracts/tests on final dev
-> fresh exact-head PRE_REAL/Built Product
-> release-time REAL_ENVIRONMENT acceptance
```

Older PRE_REAL artifacts are historical diagnostics after later `dev` movement, not readiness evidence for the final real phase.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Incremental value delivery](workstreams/incremental-value-delivery.md) | software convergence ACTIVE | finish deterministic software, then final-dev PRE_REAL |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | automated acceptance PASS | representative human accessibility/usability acceptance |
| [Representative device evidence](workstreams/representative-device-evidence.md) | release real phase DEFERRED | final-dev PRE_REAL, then retained real runs |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-002 evidence-blocked / MIG-003 blocked | EV-3 + real PL replacement + post-disable smoke |

## Delivery model

- `dev` is the software integration line; `main` remains stable/release-oriented.
- Affected automated E2E and UX/UI evidence block integration; representative hardware/runtime evidence does not.
- Repository-owned deterministic gates prove software semantics, not representative hardware/model claims.
- Required `REAL_ENVIRONMENT` claims are a release gate after planned software convergence.
- Do not invent product/policy semantics or broad subsystems for later slices.

## Evidence still required after software convergence

- fresh exact-head PRE_REAL/Built Product on final candidate `dev`;
- VALUE-01D, VALUE-02D, VALUE-03D and VALUE-04D/EVID-003 representative runs;
- VALUE-05D / EVID-002 repeatability/variability and VALUE-06D / EVID-004 regression evidence;
- VALUE-08D clean install/use smoke;
- representative human accessibility/usability acceptance;
- LLS EV-3 + real PL replacement + post-disable cross-repository smoke before VALUE-07 cutover;
- branch protection/admin work in #61.
