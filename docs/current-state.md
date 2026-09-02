# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-09-02

Short operational ledger only. Durable behavior belongs in architecture/ADR/design docs; active detail belongs in workstreams; Git history owns implementation history.

## Current phase

Performance Lab is product-software complete for the current local text-generation UI scope. The decision-first desktop experience is integrated on `dev`, including the four-stage **Find best setup** flow and the Light-first visual system with optional Dark/System appearance.

Primary product question:

> For this use case on this device, which available model + quantization + configuration gives me the best evidence-backed trade-off, and why?

Work now advances through vertical VALUE slices that unlock end-to-end outcomes. M1-M9 remain the capability/maturity coverage map rather than the delivery sequence.

## Integrated baseline

`dev` contains Overview; Find best setup `Goal -> Models -> Optimization -> Review -> Campaign -> Results`; Test a model; Live Run recovery; Runs/Run Detail; Compare; Library/Settings; Benchmark Detail; Run -> Samples -> Sample Evidence; same-case comparison; browser-local Light/Dark/System appearance; and built/package lifecycle support.

Campaigns revalidate frozen plan digests, persist reconnectable lifecycle separately from immutable Runs and apply compatibility before explicit decision policy. Quality, Performance and Resources remain separate; missing, incompatible, unavailable and not-retained evidence remain explicit.

VALUE-01 software/readiness lanes are integrated:

- **VALUE-01A / #117 DONE** — real built-browser journey against Local LLM Server;
- **VALUE-01B / #118 DONE** — retained evidence completeness/portability verifier;
- **VALUE-01C / #119 DONE** — exact-head PRE_REAL-gated real-run entry point and retained run manifest.

Their branch validation passed Repository Validation, Browser Acceptance, Built Product/PRE_REAL and Repository Health before integration. The merge commits moved `dev`, so the representative run still requires a **fresh exact-head PRE_REAL PASS** for the final `dev` revision.

## Current value frontier

Current executable slice: **VALUE-01 — Real single-model evidence loop** in [`workstreams/incremental-value-delivery.md`](workstreams/incremental-value-delivery.md).

Target loop:

```text
real target/device -> discover one real model -> Test a model -> real inference
-> Run Detail -> sample evidence -> retained .plab.zip
```

VALUE-01 remains **ACTIVE**. Its only remaining acceptance gate is **VALUE-01D / #120**, now READY for one retained `REAL_ENVIRONMENT` execution after a fresh exact-head PRE_REAL/Built Product pass.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Incremental value delivery](workstreams/incremental-value-delivery.md) | VALUE-01 ACTIVE; A/B/C DONE; D READY | refresh exact-head PRE_REAL, then execute #120 on representative hardware |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | automated product/visual acceptance PASS | representative human accessibility/usability acceptance; then finalize/delete |
| [Representative device evidence](workstreams/representative-device-evidence.md) | EVID-001 READY | #120 retained real run supplies the first representative artifact set |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 evidence-blocked / MIG-003 blocked | EV-3 + real PL replacement evidence; consumed by VALUE-07 |

## Delivery model

- `dev` is the integration line; ordinary feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately with `FULL` validation.
- VALUE slices are vertical user outcomes. After VALUE-02, configuration optimization, device-aware evidence and distribution may proceed in parallel when ownership does not conflict.
- Parallel work uses explicit non-conflicting owners and one convergence gate; it must not create competing implementations of the same contract.
- Do not build broad subsystems in anticipation of later slices.

## Evidence still required

- fresh exact-head PRE_REAL/Built Product readiness for the final integrated `dev` revision;
- VALUE-01D retained real target/model/device execution with verifier PASS;
- later VALUE-02/04/05/06 real decision, telemetry/repeatability and regression evidence;
- representative human accessibility/usability acceptance before a reference-grade human UX claim;
- LLS EV-3 + real PL replacement run + post-disable cross-repository smoke before VALUE-07 cutover;
- branch protection/admin work remains tracked separately in GitHub issue #61.
