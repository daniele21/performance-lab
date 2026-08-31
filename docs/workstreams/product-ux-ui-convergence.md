# Product UX/UI convergence

Status: active
Owner: product experience / browser UI
Read when: coordinating the remaining premium visual refactor

## Goal

Make Performance Lab feel like a mature precision instrument while preserving the settled product question:

> For this use case on this device, which available model + quantization + configuration is the best evidence-backed fit, and why?

This is a visual/systemic refactor, not a new product architecture. `design/ux-contract.json` owns product semantics; `design/brand-kit.json` owns visual identity; shared frontend tokens/components and page owners implement them.

## Invariants

- Keep `Overview -> Find best setup -> Test a model -> Runs -> Compare`; Library/Settings stay secondary.
- Keep immutable Run/Campaign identity, compatibility-before-ranking and separate Quality/Performance/Resources evidence.
- TypeScript must not invent scores, benchmark semantics, parameter ranges, evaluator rationale or runtime capabilities.
- Keep progressive disclosure: `essential -> contextual -> advanced -> expert/diagnostics`.
- Keyboard/focus, reduced motion and supported desktop adaptation remain blocking.
- v0.5 accepted pixel goldens are the deliberate **before baseline** until PVR-08; do not weaken or incrementally refresh them.

## Direction — Precision Instrument

Use calm hierarchy, restrained navigation, deliberate density, neutral graphite surfaces, subtle depth, compact controls, tabular metrics and low decorative chroma. Accent communicates meaning rather than generic interactivity. Q/P/R evidence remains proprietary product language, not a normalized cross-dimension score.

## Work graph

| ID | Work | State |
| --- | --- | --- |
| UXUI-00..10 | Existing UX/UI, hardening and before-golden baseline | DONE |
| PVR-00 | Visual/component audit | DONE |
| PVR-01 | `brand-kit` v0.6 contract | DONE |
| PVR-02 | Tokens/primitives/foundation | DONE |
| PVR-03 | Workspace-first shell/navigation | DONE |
| PVR-04A | Overview / Find best setup / Campaign | DONE |
| PVR-04B | Test a model / Live Run / Run Detail | DONE |
| PVR-05 | Runs / Compare / evidence drilldowns | DONE |
| PVR-06 | Library / Settings | DONE |
| PVR-07 | Integrated polish/accessibility/adaptation | ACTIVE |
| PVR-08 | Approved v0.6 targets + bounded goldens | BLOCKED |
| PVR-09 | Final PRE_REAL + human acceptance | BLOCKED |

`DONE` for PVR-01..06 means the owner slice was technically complete and validated before integration. It does not make the stack publication-ready. PVR-07 must establish fresh evidence on the integrated exact head.

## Implemented slices

- **PVR-01/#89:** v0.6 visual contract: neutral surface depth, border strength, restrained accent, Q/P/R semantics, compact controls, tabular metrics and functional reduced-motion-safe motion.
- **PVR-02/#90:** canonical graphite shared system in `frontend/src/design/` and shared primitives; no page-specific competing design system.
- **PVR-03/#91:** primary workspace navigation stays persistent; Library/Settings use native progressive disclosure, collapse on primary workflows and auto-open on their routes. Unavailable destinations remain accessible without repeated visible `Pending` noise.
- **PVR-04A/#92:** Overview foregrounds tested-model evidence. Completed Campaign reading order is `status -> Results/best fit -> completed progress -> candidate Runs`; running Campaigns remain progress-first. Compatibility/policy stay before recommendation and J0 locks the terminal DOM order.
- **PVR-04B/#93:** Test a model and Live Run use quieter, denser chrome. Run Detail is `identity/status -> compact separate Q/P/R panel -> samples/evidence -> reproducibility` without aggregate verdicts.
- **PVR-05/#94:** Runs is a compact evidence register. Compare foregrounds compatibility and exact metric deltas; invalid accessible label references found during refactor were removed.
- **PVR-06/#95:** Library/Settings are visually subordinate, use neutral table treatment and flatter advanced context while preserving external-runtime ownership and backend-owned capability semantics.

## Evidence before integration

Each PVR-04A/04B/05/06 exact head passed Repository Validation and Built Product/PRE_REAL before entering PVR-07. Where Browser logs were explicitly classified, functional journeys were 18/19 with the sole failure being the intentionally obsolete v0.5 `overview.png` golden. This is supporting evidence only; integrated evidence supersedes it.

## PVR-07 — integrated owner

PR #100 on `agent/pvr-07-integrated-polish` integrates PVR-04A directly and PVR-04B/05/06 through #97/#98/#99 without moving `dev`.

PVR-07 owns cross-surface reconciliation: wrapping, baselines, action hierarchy, disabled/focus states, dividers, long identities, disclosures, loading/error/recovery, reduced motion and desktop adaptation. It also adds `cross-surface-integrity.spec.ts`, which at the 1024px minimum desktop width traverses canonical primary/Library/Settings routes and fails on horizontal document overflow or unresolved `aria-labelledby` / `aria-describedby` references. This generalizes two concrete invalid-ARIA defects fixed in Campaign/Compare.

Completion of PVR-07 requires the **integrated exact head** to show:

- Repository Health PASS;
- Repository Validation PASS;
- functional Browser journeys PASS apart from the deliberately stale v0.5 pixel baseline;
- PRE_REAL J0-J9 PASS with retained evidence;
- packaged J0/J1/J8/J9 PASS and final readiness/contract checks.

Per-slice green evidence cannot substitute for this integrated run.

## PVR-08/09 acceptance

Acceptance flow:

`v0.5 before baseline -> integrated v0.6 implementation -> review -> approved v0.6 target -> accepted implementation golden`.

PVR-08 is the first owner allowed to replace accepted pixel goldens, and only for the bounded stable surfaces proven obsolete by the approved v0.6 target. PRE_REAL remains the broader screenshot/trace owner.

Before publication readiness, run repository-owned `preflight-change` and every locally reproducible deterministic gate on the exact current head. If local execution is unavailable because of the environment, record it as N/A rather than inferring PASS from CI.

PVR-09 reruns final PRE_REAL and representative human/accessibility acceptance. Human/reference-grade claims remain PENDING until actually executed. On completion, transfer durable truth to `design/` / current-state docs and delete this workstream by default.

## Durable destinations

- `design/ux-contract.json`: task model, IA, hierarchy, states and journeys.
- `design/brand-kit.json`: v0.6 visual identity/system.
- `frontend/src/design/` + canonical components: executable system.
- `.engineering/e2e.json` / PRE_REAL: journey and fidelity evidence.
- accepted target/golden manifests: bounded visual provenance.
