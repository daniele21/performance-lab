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
| PVR-00 | Visual/component baseline audit | UXUI-10 | ACTIVE |
| PVR-01 | Visual direction + `brand-kit` v0.6 contract | UXUI-10 | ACTIVE |
| PVR-02 | Tokens/primitives/foundation refactor | PVR-00/01 | BLOCKED |
| PVR-03 | App shell + navigation visual refactor | PVR-02 | BLOCKED |
| PVR-04A | Overview + Find best setup + Campaign decision surfaces | PVR-02/03 | BLOCKED |
| PVR-04B | Test a model + Live Run + Run Detail | PVR-02/03 | BLOCKED |
| PVR-05 | Runs + Compare + benchmark/sample/case evidence surfaces | PVR-02/03 | BLOCKED |
| PVR-06 | Library + Settings secondary surfaces | PVR-02/03 | BLOCKED |
| PVR-07 | States, responsive polish, copy disclosure, accessibility hardening | PVR-04A/04B/05/06 | BLOCKED |
| PVR-08 | New approved targets + bounded implementation goldens | PVR-07 | BLOCKED |
| PVR-09 | PRE_REAL E2E + final human accessibility/usability acceptance | PVR-08 | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

## PVR-00 — Baseline audit

Audit the current real implementation and PRE_REAL screenshots, not mockups. Produce implementation ownership and concrete refactor findings inside this workstream rather than a parallel permanent audit document.

Required checks:

- shell/navigation prominence and workspace focus;
- typography scale/weights and excessive bold usage;
- surface nesting, borders, elevation and visual depth;
- color/chroma usage and whether accent is semantic or decorative;
- CTA hierarchy and control sizing;
- metric composition and Quality/Performance/Resources density;
- copy visible by default versus contextual/advanced disclosure;
- table/data-row rhythm, long identifiers and status wrapping;
- loading/empty/error/partial/incompatible/disabled states;
- 1024/1280/1600 layout behavior;
- shared owners versus page-specific CSS duplication.

Current known issues to confirm systematically: cyan is over-prominent; surfaces have nearly equal visual weight; sidebar behaves like an admin dashboard; explanatory copy competes with decisions; completed progress remains too prominent; large vertical metric cards dilute evidence density; status/labels can wrap awkwardly; borders do too much of the hierarchy work.

## PVR-01 — Design contract v0.6

Update `design/brand-kit.json` before implementation CSS. Preserve dark-only unless a separate product decision changes theme scope.

Contract must define:

- neutral canvas/surface/elevated/overlay hierarchy;
- subtle/strong border tokens rather than one universal border;
- restrained accent plus semantic quality/performance/resources/status colors;
- typography roles and weights, with tabular numerals for metrics;
- compact control heights, radii and spacing rhythm;
- restrained multi-layer elevation for raised surfaces/overlays only;
- hover/focus/pressed/selected/disabled treatment;
- evidence-rail visual rules that never imply an invented normalized score;
- motion remains functional and reduced-motion safe;
- no decorative gradients/glass/stock imagery in core workflows.

PVR-01 may proceed in parallel with PVR-00 because it changes the durable visual contract while PVR-00 inventories implementation ownership. PVR-02 does not start until both agree.

## PVR-02/03 — Shared foundation and shell

Primary owners: `frontend/src/design/tokens.css`, `design-system.css`, `primitives.css`, `foundation.css`, and canonical shared components (`Button`, `Metric`, `PageHeader`, `AppShell`, `Disclosure`, `DataTable`, status/feedback components).

Do not create page-specific replacements for semantic primitives already owned here. Shell refactor keeps routes and focus semantics unchanged while reducing sidebar prominence, removing repeated visual noise such as disabled `Pending` badges where a lower-noise treatment suffices, and making the workspace visually dominant.

## PVR-04..06 — Surface slices

After PVR-02/03 integrate, these slices can proceed in parallel with non-overlapping page ownership.

- **PVR-04A:** Overview, Find best setup, Campaign. Completed Campaign Results lead with the decision/best-fit evidence; progress dominates only while running.
- **PVR-04B:** Test a model, Live Run, Run Detail. Run Detail becomes an instrument panel: identity/status -> compact Q/P/R evidence -> evidence/configuration -> advanced detail.
- **PVR-05:** Runs, Compare, Benchmark Detail, Sample Evidence, Case Comparison. Exact evidence and compatibility remain stronger than decoration; tables win where exact comparison is the task.
- **PVR-06:** Library and Settings. Preserve secondary visual priority and progressive disclosure.

## Evidence language

Introduce a reusable visual treatment for evidence without changing semantics. A rail/marker may encode availability, trustworthy ranges, confidence or relative position only when the backend evidence supports that encoding. Unknown/unavailable/not-comparable never render as zero or as a shorter "bad" bar. Numeric comparison remains explicit.

## PVR-07 — Premium-quality hardening

Block completion on micro-polish that affects perceived quality and usability: accidental wrapping, inconsistent baselines, oversized CTAs, weak disabled states, noisy dividers, long-ID overflow, inconsistent disclosures, focus visibility, dense-table alignment, error/recovery, reduced motion and desktop adaptation. Add deterministic regression assertions when a defect is machine-checkable.

## PVR-08/09 — Acceptance

Do not incrementally bless intermediate screenshots as final goldens. Flow:

`current implementation -> before baseline -> approved v0.6 target -> implementation review -> accepted implementation golden`.

Keep the golden set bounded to high-value stable surfaces; J0-J9 PRE_REAL retains broader screenshot/trace coverage. Final acceptance requires current exact-head repository/browser/built-product gates, J0-J9 screenshot+trace evidence, packaged-product coverage, 1024/1280/1600 accessibility checks and representative-user review. Human/reference-grade claims remain pending until actually executed.

## Integration strategy

1. PVR-00 and PVR-01 start from current green `dev` and may run in parallel because they own different artifacts.
2. Merge the agreed v0.6 contract/audit before PVR-02 changes shared design primitives.
3. Merge PVR-02 then PVR-03 before page slices.
4. Run PVR-04A, PVR-04B, PVR-05 and PVR-06 in parallel with disjoint page ownership and shared primitives frozen unless a coordinated follow-up is required.
5. PVR-07 reconciles cross-surface polish and accessibility.
6. PVR-08 regenerates approved targets/goldens only from the final visual system.
7. PVR-09 reruns PRE_REAL and human acceptance, then transfers durable truth to `design/` and deletes this workstream by default.

## Durable destinations

- `design/ux-contract.json`: settled task model, IA, hierarchy, states and journeys.
- `design/brand-kit.json`: visual identity/design-system v0.6.
- `frontend/src/design/` + canonical components: executable visual system.
- `.engineering/e2e.json` / PRE_REAL contract: journey/fidelity evidence.
- accepted target/golden manifests: bounded visual provenance.

## Completion

DONE only when the product still answers the same evidence-backed decision correctly, the v0.6 visual system is consistently implemented, no page owns a competing design system, J0-J9 and packaged-product evidence remain green, accessibility/adaptive behavior agrees with the contract, and the final human review supports the premium/reference-grade claim.