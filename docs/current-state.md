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

The next phase is **incremental real-value delivery**, not capability-by-capability completion. M1-M6 remain implemented/evidence-pending coverage areas; work now advances through vertical VALUE slices that each unlock an end-to-end usable outcome.

## Integrated baseline

`dev` contains Overview; Find best setup `Goal -> Models -> Optimization -> Review -> Campaign -> Results`; Test a model; Live Run recovery; Runs/Run Detail; Compare; Library/Settings; Benchmark Detail; Run -> Samples -> Sample Evidence; same-case comparison; browser-local Light/Dark/System appearance; and built/package lifecycle support.

Campaigns revalidate frozen plan digests, persist reconnectable lifecycle separately from immutable Runs and apply compatibility before explicit decision policy. Quality, Performance and Resources remain separate; missing, incompatible, unavailable and not-retained evidence remain explicit.

Repository-owned deterministic validation, Browser Acceptance and Built Product are green for the integrated UX/theme change. Hosted fixtures prove product behavior at their declared fidelity, not representative physical-device/runtime claims.

## Current value frontier

Current executable slice: **VALUE-01 — Real single-model evidence loop** in [`workstreams/incremental-value-delivery.md`](workstreams/incremental-value-delivery.md).

Target loop:

```text
real target/device -> discover one real model -> Test a model -> real inference
-> Run Detail -> sample evidence -> retained .plab.zip
```

VALUE-01 is accepted only with current applicable PRE_REAL/Built Product readiness plus retained `real-runtime-device` evidence. It is intentionally smaller than the whole M1-M6 evidence campaign: the goal is to unlock one real usable loop first, then extend based on evidence and feedback.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [Incremental value delivery](workstreams/incremental-value-delivery.md) | VALUE-01 READY; VALUE-02..08 dependency-gated | execute one retained real single-model evidence loop |
| [Product UX/UI convergence](workstreams/product-ux-ui-convergence.md) | automated product/visual acceptance PASS | representative human accessibility/usability acceptance; then finalize/delete |
| [Representative device evidence](workstreams/representative-device-evidence.md) | real-environment evidence READY | supplies protocol/artifacts for VALUE-01 and later VALUE-02/04/05/06 |
| [Local LLM Server migration](workstreams/local-llm-migration.md) | MIG-001 DONE / MIG-002 evidence-blocked / MIG-003 blocked | EV-3 + real PL replacement evidence; consumed by VALUE-07 |

## Delivery model

- M1-M9 in [`roadmap.md`](roadmap.md) are capability/maturity coverage, not the implementation order.
- VALUE slices are vertical user outcomes. After VALUE-02, configuration optimization, device-aware evidence and distribution may proceed in parallel when ownership does not conflict.
- Do not build broad subsystems in anticipation of later slices; add only the capability needed to close the current value loop.
- Feedback from an accepted slice may reshape later slices without weakening evidence/ownership invariants.

## Integration lines

- `dev` is the integration line; ordinary feature branches start from current green `dev` and target `dev`.
- `main` is stable/release-oriented and is promoted deliberately with `FULL` validation.

## Evidence still required

- VALUE-01 retained real target/model/device execution and portable evidence bundle;
- later VALUE-02/04/05/06 real decision, telemetry/repeatability and regression evidence;
- representative human accessibility/usability acceptance before a reference-grade human UX claim;
- LLS EV-3 + real PL replacement run + post-disable cross-repository smoke before VALUE-07 cutover;
- branch protection/admin work remains tracked separately in GitHub issue #61.