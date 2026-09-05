# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-09-03

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

Performance Lab is product-software complete for the current local text-generation UI scope. The decision-first desktop experience is integrated on `dev`, including the four-stage **Find best setup** flow and the Light-first visual system with optional Dark/System appearance.

Primary product question:

> For this use case on this device, which available model + quantization + configuration gives me the best evidence-backed trade-off, and why?

Work advances through vertical VALUE slices that unlock end-to-end outcomes. M1-M9 remain the capability/maturity coverage map rather than the delivery sequence.

## Integrated baseline

Current integration head: `dev@0b9c376f2dbcbb167f8df8488374c1b0c5d0ace2`.

`dev` contains Overview; Find best setup `Goal -> Models -> Optimization -> Review -> Campaign -> Results`; Test a model; Live Run recovery; Runs/Run Detail; Compare; Library/Settings; Benchmark Detail; Run -> Samples -> Sample Evidence; same-case comparison; browser-local Light/Dark/System appearance; and built/package lifecycle support.

Campaigns revalidate frozen plan digests, persist reconnectable lifecycle separately from immutable Runs and apply compatibility before explicit decision policy. Quality, Performance and Resources remain separate; missing, incompatible, unavailable and not-retained evidence remain explicit.

VALUE-01 software/readiness lanes are integrated:

- **VALUE-01A / #117 DONE** — real built-browser journey against Local LLM Server;
- **VALUE-01B / #118 DONE** — retained evidence completeness/portability verifier;
- **VALUE-01C / #119 DONE** — exact-head PRE_REAL-gated real-run entry point and retained run manifest.

VALUE-02 software lanes are also integrated through PR #141:

- **VALUE-02A / #129 software DONE** — configured-target multi-model discovery and per-candidate Local LLM Server identity/telemetry attribution;
- **VALUE-02B / #130 software DONE** — bounded real multi-model Campaign/browser harness;
- **VALUE-02C / #131 software DONE** — retained multi-model decision evidence verifier.

This software integration does not satisfy the representative real-device acceptance owned by VALUE-01D / #120 and VALUE-02D / #132.

## Current value frontier

The next convergence sequence is:

```text
fresh exact-head PRE_REAL on current dev
-> VALUE-01D / #120 single-model REAL_ENVIRONMENT PASS
-> VALUE-02D / #132 multi-model REAL_ENVIRONMENT PASS
-> integrate the prepared VALUE-03 / VALUE-04 / VALUE-08 lanes
```

VALUE-01 remains **ACTIVE** until #120 passes. VALUE-02 software is integrated, but VALUE-02 acceptance remains **BLOCKED** by #120 and then #132.

The previous VALUE-01 PRE_REAL handoffs are historical only because PR #141 moved `dev`; a new exact-head PRE_REAL/Built Product PASS is required for the current `dev` revision before representative execution.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Incremental value delivery](workstreams/incremental-value-delivery.md) | VALUE-01 ACTIVE; VALUE-02 software integrated / acceptance blocked | refresh exact-head PRE_REAL -> execute #120 -> execute #132 |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | automated product/visual acceptance PASS | representative human accessibility/usability acceptance; then finalize/delete |
| [Representative device evidence](workstreams/representative-device-evidence.md) | EVID-001 READY | #120 retained real run supplies the first representative artifact set |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 evidence-blocked / MIG-003 blocked | EV-3 + real PL replacement evidence; consumed by VALUE-07 |

Prepared off `dev`, but intentionally not integrated until VALUE-02 real acceptance:

- **VALUE-03A / PR #149** — consume runtime/model-declared generation parameter domains;
- **VALUE-04A / PR #148** — classify decision-grade device/resource evidence separately from contextual telemetry;
- **VALUE-08A / PR #147** — artifact-owned launcher that removes repository-development setup from normal launch.

## Delivery model

- `dev` is the integration line; ordinary feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately with `FULL` validation.
- VALUE slices are vertical user outcomes. After VALUE-02 real acceptance, configuration optimization, device-aware evidence and distribution may proceed in parallel when ownership does not conflict.
- Parallel work uses explicit non-conflicting owners and one convergence gate; it must not create competing implementations of the same contract.
- Do not build broad subsystems in anticipation of later slices.

## Evidence still required

- fresh exact-head PRE_REAL/Built Product readiness for current `dev`;
- VALUE-01D retained real target/model/device execution with verifier PASS;
- VALUE-02D retained 2+ real-model decision with verifier PASS;
- later VALUE-04/05/06 real telemetry/repeatability and regression evidence;
- representative human accessibility/usability acceptance before a reference-grade human UX claim;
- LLS EV-3 + real PL replacement run + post-disable cross-repository smoke before VALUE-07 cutover;
- branch protection/admin work remains tracked separately in GitHub issue #61.
