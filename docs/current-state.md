# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-09-05

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

Performance Lab is converging the remaining **software** needed for the current local text-generation product before entering one consolidated `REAL_ENVIRONMENT` phase.

Primary product question:

> For this use case on this device, which available model + quantization + supported configuration gives me the best evidence-backed trade-off, and why?

The delivery rule is now explicit: deterministic software slices may integrate incrementally on `dev`; representative real-device/model acceptance is refreshed and executed only after the planned software modifications have converged on the final candidate `dev` head.

## Integrated baseline

Current integration head: `dev@01613d0fdc36f230e192ca8586ed360e65619b3a`.

`dev` contains the decision-first desktop product: Overview; Find best setup `Goal -> Models -> Optimization -> Review -> Campaign -> Results`; Test a model; Live Run recovery; Runs/Run Detail; Compare; Library/Settings; Benchmark Detail; Run -> Samples -> Sample Evidence; same-case comparison; Light/Dark/System appearance; immutable package lifecycle and configless distributed launch.

Campaigns revalidate frozen plan digests, persist reconnectable lifecycle separately from immutable Runs and apply compatibility before explicit decision policy. Quality, Performance and Resources remain separate; missing, incompatible, unavailable and not-retained evidence remain explicit.

## Software convergence status

### VALUE-01 / VALUE-02

Software/readiness lanes are integrated:

- **VALUE-01A / #117 DONE** — built-browser real-runtime journey;
- **VALUE-01B / #118 DONE** — evidence completeness/portability verifier;
- **VALUE-01C / #119 DONE** — PRE_REAL-gated real-run operator entry point;
- **VALUE-02A / #129 SOFTWARE DONE** — configured-target multi-model discovery and evidence attribution;
- **VALUE-02B / #130 SOFTWARE DONE** — multi-model Campaign/browser real-runtime harness;
- **VALUE-02C / #131 SOFTWARE DONE** — multi-model decision evidence verifier.

VALUE-01D / #120 and VALUE-02D / #132 remain representative acceptance only. They are intentionally deferred until software convergence finishes and a fresh exact-head PRE_REAL is generated for the final `dev` candidate.

### VALUE-03 — configuration decision

Integrated:

- runtime/model-declared generation parameter domains;
- frozen `configuration_id` and exact generation configuration identity through Campaign planning/execution/read models.

Remaining software:

- deterministic expansion of non-Fixed search strategies into reviewed configuration matrices;
- Optimization UX for declared domains/exact planned configurations.

The exact Quick/Standard/Thorough/Custom sampling/cardinality semantics are a material product contract and must not be invented implicitly by implementation.

### VALUE-04 — device-aware decision

**VALUE-04A/B SOFTWARE DONE** through PR #153 / `4c66541e2057f21afafc9e99828c6d7ed8518ce8`:

- decision-eligible resource evidence is classified separately from contextual telemetry;
- Campaign Results and same-case comparison expose Resources as `available`, `unavailable` or `not_comparable`;
- contextual host/runtime telemetry remains inspectable without being promoted into policy evidence.

Remaining software: VALUE-04C backend decision-policy extension. The exact quality-first/resource tie-break semantics remain a material policy decision and are not guessed.

### VALUE-08 — low-friction distribution

**VALUE-08A/B/C SOFTWARE DONE**:

- artifact-owned `launch.py` owns the bounded local Performance Lab runtime;
- first run can start without a pre-authored config and connect a loopback inference target from the UI;
- only safe non-sensitive loopback preferences are browser-local;
- packaged acceptance proves `ZIP -> launch.py configless -> UI connect -> Find best setup -> bounded evaluation`;
- `distributed-artifact-evidence.json` retains artifact/runtime/source/cleanup identity.

VALUE-08D representative install/use smoke remains part of the final REAL_ENVIRONMENT phase.

## Current value frontier

The active frontier is **software convergence**, not representative execution:

```text
current dev
-> finish remaining VALUE-03 software
-> finish VALUE-04C policy software
-> decompose/close any remaining VALUE-05/06 software gaps using existing performance/regression engines
-> keep VALUE-07 destructive cutover blocked by its real cross-repo evidence gates
-> converge docs/contracts/tests on final dev
-> fresh exact-head PRE_REAL/Built Product
-> consolidated REAL_ENVIRONMENT acceptance phase
```

Older PRE_REAL artifacts remain useful historical diagnostics but are not readiness evidence for the final real phase after subsequent `dev` movement.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Incremental value delivery](workstreams/incremental-value-delivery.md) | software convergence ACTIVE | finish remaining software slices, then refresh exact-head PRE_REAL |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | automated product/visual acceptance PASS | representative human accessibility/usability acceptance |
| [Representative device evidence](workstreams/representative-device-evidence.md) | real phase DEFERRED until software convergence | final-dev PRE_REAL, then retained REAL_ENVIRONMENT runs |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 evidence-blocked / MIG-003 blocked | EV-3 + real PL replacement + post-disable cross-repo smoke |

## Delivery model

- `dev` is the software integration line; ordinary feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately with `FULL` validation.
- Repository-owned deterministic gates prove software semantics; they do not establish representative hardware/model claims.
- `REAL_ENVIRONMENT` is one final phase after planned software convergence, not an integration prerequisite for each intermediate software slice.
- Parallel work uses explicit non-conflicting owners and one convergence gate; it must not create competing implementations of the same contract.
- Do not build broad subsystems or invent product/policy choices in anticipation of later slices.

## Evidence still required

After software convergence:

- fresh exact-head PRE_REAL/Built Product readiness on the final candidate `dev`;
- VALUE-01D retained real target/model/device execution with verifier PASS;
- VALUE-02D retained 2+ real-model decision with verifier PASS;
- VALUE-03D representative 2+ supported-configuration decision;
- VALUE-04D / EVID-003 representative resource/telemetry validation;
- VALUE-05 repeatability/variability evidence and VALUE-06 real regression-policy evidence;
- VALUE-08D representative clean install/use smoke;
- representative human accessibility/usability acceptance before a reference-grade human UX claim;
- LLS EV-3 + real PL replacement run + post-disable cross-repository smoke before destructive VALUE-07 cutover;
- branch protection/admin work remains tracked separately in GitHub issue #61.
