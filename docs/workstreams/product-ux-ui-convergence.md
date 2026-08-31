# Product UX/UI convergence

Status: active
Owner: product experience / browser UI
Read when: coordinating the remaining UX/UI convergence and premium visual refactor

## Goal

Make Performance Lab feel like a mature premium precision instrument while preserving the settled product question and task model:

> For this use case on this device, which available model + quantization + configuration is the best evidence-backed fit, and why?

The refactor is visual/systemic, not a new product architecture. Canonical semantics remain in `design/ux-contract.json`; visual identity and design-system rules remain in `design/brand-kit.json`; implementation remains in shared frontend tokens/components plus page owners.

## Invariants

- Keep `Overview -> Find best setup -> Test a model -> Runs -> Compare`; Library and Settings remain secondary.
- Keep Run/Campaign identity, compatibility-before-ranking, and Quality/Performance/Resources separation unchanged.
- Do not invent scores, scales, benchmark semantics, parameter ranges, evaluator rationale or runtime capabilities in TypeScript.
- Progressive disclosure remains `essential -> contextual -> advanced -> expert/diagnostics`.
- Existing accessibility, keyboard/focus, reduced-motion and 1024/1280/1600 desktop requirements remain blocking.
- Existing visual goldens are a `before` regression baseline during the refactor, not the final visual target.
- Shared design primitives/tokens have one owner at a time; page slices may proceed in parallel only after that owner is stable.

## Visual direction — Precision Instrument

Reference qualities, not copies:

- Linear: calm hierarchy, restrained navigation, deliberate density.
- Raycast: micro-polish, compact controls, precise interaction states.
- Vercel: neutral surfaces, subtle borders/depth, technical clarity.
- Performance Lab: proprietary evidence language for trustworthy Quality/Performance/Resources and compatibility.

Desired outcome: neutral graphite canvas, low decorative chroma, stronger information hierarchy, less explanatory copy above the fold, compact controls, deliberate depth, tabular metrics and evidence-first composition. Accent color communicates meaning rather than generic interactivity.

## Work graph

| ID | Work | Depends on | State |
| --- | --- | --- | --- |
| UXUI-00..09 | Existing product UX/UI + hardening | — | DONE |
| UXUI-10 | Existing automated built-product/golden baseline | UXUI-09 | DONE |
| PVR-00 | Visual/component baseline audit | UXUI-10 | DONE |
| PVR-01 | Visual direction + `brand-kit` v0.6 contract | UXUI-10 | DONE |
| PVR-02 | Tokens/primitives/foundation refactor | PVR-00/01 | DONE |
| PVR-03 | App shell + navigation visual refactor | PVR-02 | DONE |
| PVR-04A | Overview + Find best setup + Campaign decision surfaces | PVR-02/03 | DONE |
| PVR-04B | Test a model + Live Run + Run Detail | PVR-02/03 | DONE |
| PVR-05 | Runs + Compare + benchmark/sample/case evidence surfaces | PVR-02/03 | DONE |
| PVR-06 | Library + Settings secondary surfaces | PVR-02/03 | DONE |
| PVR-07 | States, responsive polish, copy disclosure, accessibility hardening | PVR-04A/04B/05/06 | ACTIVE |
| PVR-08 | New approved targets + bounded implementation goldens | PVR-07 | BLOCKED |
| PVR-09 | PRE_REAL E2E + final human accessibility/usability acceptance | PVR-08 | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

`DONE` for PVR-01..06 means each owner slice is technically complete and had current deterministic/PRE_REAL evidence before integration. It does **not** mean the draft stack is publication-ready: the accepted v0.5 pixel goldens intentionally remain the before-baseline until PVR-08. PVR-07 owns the integrated candidate and must establish fresh exact-head evidence after reconciliation.

## Current stack evidence

- **PVR-01 / #89:** `brand-kit` v0.6 contract + verifier ownership implemented and validated before foundation work.
- **PVR-02 / #90:** graphite shared foundation implemented; deterministic and Built Product/PRE_REAL evidence passed, with Browser Acceptance differing only from the intentionally obsolete v0.5 Overview golden.
- **PVR-03 / #91:** workspace-first shell at validated head `d3bc4199c5047ba79c011052d48c2dbb5a67d898`; Repository Health, Repository Validation and Built Product/PRE_REAL PASS; Browser 18/19 with only v0.5 `overview.png` mismatch.
- **PVR-04A / #92:** exact head `22ff327cc307b05d8cefabed3b7b4648d68acb70`; Repository Health, Repository Validation and Built Product/PRE_REAL PASS; Browser 18/19 with J0 terminal Campaign reading-order regression passing and only v0.5 `overview.png` failing.
- **PVR-04B / #93:** exact head `75164b90a30a57ae76b3360b96002f7f58af72c6`; Repository Health, Repository Validation and Built Product/PRE_REAL PASS; Browser 18/19 with only v0.5 `overview.png` failing.
- **PVR-05 / #94:** exact head `5ef8f8fdaf9cd367c7c4072a80af33cfb07b0e17`; Repository Validation and Built Product/PRE_REAL PASS. Its page owner changes were integrated only after that evidence was current.
- **PVR-06 / #95:** exact head `2d9e199daa85a0122505946aba8edef572fe23ea`; Repository Health, Repository Validation and Built Product/PRE_REAL PASS; Browser 18/19 with only v0.5 `overview.png` failing.
- **PVR-07 / #100:** integrates 04A directly and 04B/05/06 through temporary integration PRs #97/#98/#99 without moving `dev`. Fresh exact-head integrated validation is required after PVR-07 hardening edits; prior per-slice evidence is supporting evidence only.

## PVR-00 — Baseline audit

Audit basis: current PRE_REAL screenshots plus canonical shared styles/components and representative primary/secondary page styles (`AppShell`, `Metric`, `tokens`, `design-system`, `primitives`, Overview, Find best setup, Campaign, Run Detail and secondary/library surfaces).

### Findings

| Area | Finding | Owner / action |
| --- | --- | --- |
| Color | saturated cyan was navigation, selection, progress, links and CTA at once; semantic meaning was diluted | `brand-kit.json` -> PVR-01, executable tokens -> PVR-02 |
| Surfaces | hierarchy relied heavily on `1px border + elevated background` | shared tokens/primitives -> PVR-02 |
| Navigation | admin-like sidebar and repeated secondary groups competed with the workspace | `AppShell` -> PVR-03 |
| Typography | heavy weights/uppercase support text created visual noise | PVR-01/02 |
| Controls | large/bright controls made actions louder than evidence | PVR-02 |
| Metrics | Q/P/R semantics were correct but vertically expensive | shared metric treatment -> PVR-02, composition -> PVR-04/05 |
| Wizard | Find best setup repeated card grammar across hierarchy levels | PVR-04A |
| Campaign | completed state did not foreground the policy-backed decision | PVR-04A |
| Run detail | identity/status/metrics/evidence were split into equally weighted blocks | PVR-04B |
| Secondary UI | Library/Settings competed visually with primary decision surfaces | PVR-06 |
| Copy | contextual/technical explanation stayed visible too often | PVR-04..07 |
| Polish | wrapping/status alignment, disabled states, dividers and long identities needed regression coverage | PVR-07 |

The debt was primarily shared-system debt rather than a new product-architecture problem. PVR-02 established the v0.6 foundation; later slices reuse it rather than creating competing page design systems.

## PVR-01 — Design contract v0.6

The v0.6 contract is implemented in `design/brand-kit.json` and synchronized semantic TypeScript/CSS tokens. Dark-only remains canonical. The contract defines neutral surface depth, border strength, restrained accent, Q/P/R semantics, compact controls, tabular metric typography, functional motion and constraints against invented normalized evidence or decorative core-workflow effects.

## PVR-02/03 — Shared foundation and shell

PVR-02 owns the canonical shared visual system (`tokens.css`, `design-system.css`, `primitives.css`, `foundation.css` and shared semantic components). PVR-03 owns `AppShell`: primary navigation stays persistent, while Library and Settings use native progressive disclosure, collapse on primary workflows and auto-open on their own routes. Unimplemented destinations remain semantically unavailable without repeated visual `Pending` noise.

Routes, skip navigation, SPA focus restoration, secondary IA and backend-owned semantics remain unchanged.

## PVR-04A — Decision surfaces

Overview makes tested-model evidence primary and Recent runs secondary. Completed Campaigns now use task/reading order:

`status -> Results / best fit -> completed progress -> candidate Runs`.

Running Campaigns remain progress-first. Recommendation emphasis is policy-backed only; compatibility and the versioned decision policy remain before recommendation, and no aggregate score/hidden weight is introduced. Browser J0 locks the terminal reading order and the Campaign Results accessible region has an explicit valid label.

## PVR-04B — Run surfaces

Test a model uses denser, quieter step/scenario/connection treatment without changing discovery, parameter, freeze or launch semantics. Live Run foregrounds server-owned active progress while identity/diagnostics remain inspectable but secondary. Run Detail composes identity/status followed by one compact Q/P/R instrument panel, retaining separate MetricGroups, availability and exact values, then samples/evidence/reproducibility.

## PVR-05 — Evidence surfaces

Runs is a compact technical evidence register. Compare preserves exact compatibility and metric deltas as the dominant content while reducing selector/container chrome. Invalid accessible references found during the refactor were removed; exact tables, `CompatibilitySummary`, `Delta` and `IdentityDiff` remain canonical rather than introducing normalized decoration.

## PVR-06 — Secondary surfaces

Library and Settings remain useful but visually subordinate: bounded workspace width, neutral table treatment and flatter Advanced settings context. Settings descriptions are contextual to Model connections / Devices & targets / Advanced while preserving external-runtime ownership and backend-owned target capability semantics.

## Evidence language

A reusable evidence treatment may encode availability, trustworthy ranges, confidence or relative position only when backend evidence supports that encoding. Unknown/unavailable/not-comparable never render as zero or as a shorter "bad" bar. Numeric comparison remains explicit. No current slice invents a normalized cross-dimension score.

## PVR-07 — Integrated premium-quality hardening

PVR-07 is the single owner after parallel page integration. It must reconcile cross-surface patterns and block completion on defects that affect perceived quality or usability: accidental wrapping, inconsistent baselines, oversized actions, weak disabled/focus states, noisy dividers, long-ID overflow, inconsistent disclosures, error/recovery, reduced motion and desktop adaptation.

Current hardening additions include a deterministic browser regression that, at the minimum 1024px desktop width, traverses canonical primary/Library/Settings routes and fails on horizontal document overflow or unresolved `aria-labelledby` / `aria-describedby` references. This generalizes two concrete invalid-ARIA defects found and fixed during Campaign/Compare work.

PVR-07 is complete only after the **integrated exact head** passes Repository Validation, functional Browser Acceptance apart from the deliberately stale v0.5 pixel baseline, Built Product/PRE_REAL J0-J9 and packaged J0/J1/J8/J9. Per-slice green evidence cannot substitute for this integrated run.

## PVR-08/09 — Acceptance

Do not incrementally bless intermediate screenshots as final goldens. Flow:

`v0.5 before baseline -> integrated v0.6 implementation -> implementation review -> approved v0.6 target -> accepted implementation golden`.

PVR-08 is the first stage allowed to replace accepted pixel goldens. Keep the golden set bounded to high-value stable surfaces; PRE_REAL J0-J9 retains broader screenshot/trace evidence. Final acceptance requires current exact-head repository/browser/built-product gates, screenshot+trace evidence, packaged-product coverage, 1024/1280/1600 accessibility/adaptive checks and representative-user review. Human/reference-grade claims remain PENDING until actually executed.

## Integration strategy

1. PVR-00 is merged and owns the completed audit.
2. PVR-01/02/03 are technically complete foundation slices in the draft visual-refactor stack.
3. PVR-04A/04B/05/06 were developed and validated in parallel with disjoint ownership and shared primitives frozen.
4. PVR-07 integrates those four slices on `agent/pvr-07-integrated-polish` without moving `dev`, then owns all cross-surface reconciliation/hardening and fresh exact-head evidence.
5. PVR-08 reviews the integrated implementation, records approved v0.6 targets and replaces only the bounded pixel goldens proven obsolete.
6. Before publication readiness, run repository-owned `preflight-change` and every locally reproducible deterministic gate on the exact integrated head. Environment-unavailable local evidence must remain N/A rather than being inferred from CI.
7. PVR-09 reruns final PRE_REAL and human/reference-grade acceptance, transfers durable truth to `design/` / current-state docs and deletes this workstream by default when complete.

## Durable destinations

- `design/ux-contract.json`: settled task model, IA, hierarchy, states and journeys.
- `design/brand-kit.json`: visual identity/design-system v0.6.
- `frontend/src/design/` + canonical components: executable visual system.
- `.engineering/e2e.json` / PRE_REAL contract: journey/fidelity evidence.
- accepted target/golden manifests: bounded visual provenance.

## Completion

DONE only when the product still answers the same evidence-backed decision correctly, the v0.6 visual system is consistently implemented, no page owns a competing design system, integrated J0-J9 and packaged-product evidence remain green, accessibility/adaptive behavior agrees with the contract, and the final human review supports the premium/reference-grade claim.
