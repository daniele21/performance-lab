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
| PVR-04A | Overview + Find best setup + Campaign decision surfaces | PVR-02/03 | ACTIVE |
| PVR-04B | Test a model + Live Run + Run Detail | PVR-02/03 | ACTIVE |
| PVR-05 | Runs + Compare + benchmark/sample/case evidence surfaces | PVR-02/03 | ACTIVE |
| PVR-06 | Library + Settings secondary surfaces | PVR-02/03 | ACTIVE |
| PVR-07 | States, responsive polish, copy disclosure, accessibility hardening | PVR-04A/04B/05/06 | BLOCKED |
| PVR-08 | New approved targets + bounded implementation goldens | PVR-07 | BLOCKED |
| PVR-09 | PRE_REAL E2E + final human accessibility/usability acceptance | PVR-08 | BLOCKED |

Allowed states: `READY`, `ACTIVE`, `BLOCKED`, `DONE`.

`DONE` for PVR-01..03 means the owned technical slice is complete and has current validation evidence inside the visual-refactor stack. It does **not** mean those draft PRs are independently merge/publication-ready: the accepted v0.5 pixel goldens intentionally remain the before-baseline until PVR-08. The stack remains not ready for publication while that deliberate visual mismatch exists.

### Current stack evidence

- PVR-01: `brand-kit` v0.6 contract + verifier ownership are implemented in draft PR #89 and passed repository-owned deterministic gates before the foundation changed.
- PVR-02: shared graphite foundation is in draft PR #90. Format/lint/typecheck/unit/build, Product E2E and Built Product/PRE_REAL J0-J9 passed; Browser Acceptance failed only the intentionally obsolete v0.5 Overview pixel golden.
- PVR-03: workspace-first shell is in draft PR #91 at exact head `d3bc4199c5047ba79c011052d48c2dbb5a67d898`. Repository Health, Repository Validation and Built Product/PRE_REAL are PASS. Browser Acceptance is 18/19 PASS with only the v0.5 Overview golden mismatch.
- PVR-04A/04B/05/06 started in parallel from that same validated PVR-03 head as draft PRs #92/#93/#94/#95. Shared tokens/primitives/AppShell are frozen across these branches.

## PVR-00 — Baseline audit

Audit basis: current PRE_REAL screenshots plus canonical shared styles/components and representative primary/secondary page styles (`AppShell`, `Metric`, `tokens`, `design-system`, `primitives`, Overview, Find best setup, Campaign, Run Detail and secondary/library surfaces).

### Findings

| Area | Finding | Owner / action |
| --- | --- | --- |
| Color | saturated cyan is navigation, selection, progress, links and CTA at once; semantic meaning is diluted | `brand-kit.json` -> PVR-01, executable tokens -> PVR-02 |
| Surfaces | most hierarchy is `1px border + elevated background`; canvas/cards/actions/tables feel equally weighted | shared tokens/primitives -> PVR-02 |
| Navigation | 15rem admin-like sidebar, repeated secondary groups and `Pending` badges compete with workspace | `AppShell` + shared shell CSS -> PVR-03 |
| Typography | system is readable but relies heavily on 700/750 weights, uppercase eyebrows and similarly sized support copy | brand typography roles -> PVR-01/02 |
| Controls | 2.5–2.65rem controls plus bright primary treatment make actions visually louder than needed | Button/Field/IconButton primitives -> PVR-02 |
| Metrics | Q/P/R semantics are correct but large card/grid treatment uses vertical space without increasing evidence clarity | `Metric`/`MetricGroup` -> PVR-02, page composition -> PVR-04/05 |
| Wizard | Find best setup repeats the same bordered-card grammar across steps, choices, status, actions and summaries | shared foundation first, then PVR-04A |
| Campaign | progress/actions/cards/policy/recommendation share near-equal visual weight; completed state does not foreground the decision enough | PVR-04A |
| Run detail | identity/status/metrics/evidence are correct but separated into many equally weighted bordered blocks | PVR-04B |
| Secondary UI | Library/Settings use the same large card treatment as primary decision surfaces, weakening task hierarchy | PVR-06 |
| Copy | contextual/technical explanation frequently remains visible instead of using existing disclosure hierarchy | page composition PVR-04..06, reconciled in PVR-07 |
| Polish | wrapping/status alignment, disabled opacity, dividers and long technical identities need explicit regression treatment | PVR-07 |

### Ownership conclusion

The visual debt is primarily shared-system debt, not independent page debt. PVR-02 replaced the universal `surface_elevated + border + cyan` grammar with explicit surface depth, border strength, interaction and metric roles. Page slices must reuse that system rather than create local premium-looking cards. No new architecture or backend/read-model change is required by the audit.

Responsive behavior is structurally sound: compact breakpoints already collapse grids/navigation and long-content hardening exists. The refactor preserves those behaviors and changes content priority/composition rather than introducing a new mobile model.

PVR-00 is complete. Current screenshots/goldens remain the intentional `before` reference and PRE_REAL remains the behavioral screenshot/trace owner during implementation.

## PVR-01 — Design contract v0.6

The v0.6 contract is implemented in `design/brand-kit.json` and synchronized semantic TypeScript tokens. Dark-only remains canonical.

The contract defines:

- neutral canvas/surface/elevated/raised hierarchy;
- subtle/default/strong border roles;
- restrained accent plus semantic quality/performance/resources/status colors;
- typography roles and weights, with tabular numerals for metrics;
- compact control heights, radii and spacing rhythm;
- restrained elevation for raised surfaces/overlays only;
- interaction state rules;
- evidence visual-language constraints that forbid invented normalized scores;
- functional reduced-motion-safe motion;
- no decorative gradients/glass/stock imagery in core workflows.

## PVR-02/03 — Shared foundation and shell

PVR-02 owns `frontend/src/design/tokens.css`, `design-system.css`, `primitives.css`, `foundation.css` and canonical shared primitives. The v0.6 system now uses a neutral graphite canvas, quieter border hierarchy, compact controls, restrained accents and denser metric/table treatments.

PVR-03 owns `AppShell` and shell/navigation composition. Primary navigation remains always visible. Library and Settings use native progressive disclosure, are collapsed on primary workflows and auto-open on their active routes. Unimplemented secondary destinations remain visible and `aria-disabled`, but repeated visual `Pending` badges no longer compete with the workspace; unavailable reasons remain accessible.

Routes, skip navigation, route-focus behavior, secondary IA and domain semantics are unchanged. PVR-03 passed PRE_REAL J0-J9 and packaged J0/J1/J8/J9 before page slices started.

## PVR-04..06 — Parallel surface slices

These branches all start from the same validated PVR-03 exact head and have disjoint page ownership. Shared design-system and shell owners are frozen unless a coordinated follow-up is explicitly required.

- **PVR-04A / PR #92:** Overview, Find best setup, Campaign. Overview now gives tested-model evidence primary weight and recent runs secondary weight. Next: completed Campaign Results lead with decision/best-fit evidence; progress dominates only while running.
- **PVR-04B / PR #93:** Test a model, Live Run, Run Detail. Run Detail is being composed as an instrument panel: identity/status -> compact but separate Q/P/R evidence -> samples/evidence/configuration -> advanced reproducibility.
- **PVR-05 / PR #94:** Runs, Compare, Benchmark Detail, Sample Evidence, Case Comparison. Runs is becoming a compact technical evidence register. Exact evidence and compatibility stay stronger than decoration; tables win where exact comparison is the task.
- **PVR-06 / PR #95:** Library and Settings. Secondary pages use quieter canvas/table treatment and flatter advanced context while preserving secondary visual priority and progressive disclosure.

## Evidence language

A reusable evidence treatment may encode availability, trustworthy ranges, confidence or relative position only when backend evidence supports that encoding. Unknown/unavailable/not-comparable never render as zero or as a shorter "bad" bar. Numeric comparison remains explicit. No current page slice may invent a normalized cross-dimension score.

## PVR-07 — Premium-quality hardening

Block completion on micro-polish that affects perceived quality and usability: accidental wrapping, inconsistent baselines, oversized CTAs, weak disabled states, noisy dividers, long-ID overflow, inconsistent disclosures, focus visibility, dense-table alignment, error/recovery, reduced motion and desktop adaptation. Add deterministic regression assertions when a defect is machine-checkable.

PVR-07 is also the reconciliation point for any page-specific visual pattern that appears in more than one parallel slice; shared ownership should be consolidated there rather than duplicated retroactively across active branches.

## PVR-08/09 — Acceptance

Do not incrementally bless intermediate screenshots as final goldens. Flow:

`v0.5 before baseline -> v0.6 implementation stack -> implementation review -> approved v0.6 target -> accepted implementation golden`.

Keep the golden set bounded to high-value stable surfaces; J0-J9 PRE_REAL retains broader screenshot/trace coverage. PVR-08 is the first stage allowed to replace the accepted pixel goldens after the full v0.6 surface stack has been reviewed.

Final acceptance requires current exact-head repository/browser/built-product gates, J0-J9 screenshot+trace evidence, packaged-product coverage, 1024/1280/1600 accessibility checks and representative-user review. Human/reference-grade claims remain pending until actually executed.

## Integration strategy

1. PVR-00 is merged and owns the completed audit.
2. PVR-01, PVR-02 and PVR-03 are technically complete slices in one draft visual-refactor stack. They are not separately published while the accepted v0.5 pixel baseline intentionally disagrees with the v0.6 implementation.
3. PVR-04A, PVR-04B, PVR-05 and PVR-06 run in parallel from the same validated PVR-03 head with disjoint page ownership and shared primitives frozen.
4. PVR-07 reconciles the four page slices, owns cross-surface polish/accessibility and produces one coherent candidate implementation.
5. PVR-08 reviews that integrated implementation, records the approved v0.6 targets and replaces only the bounded pixel goldens that are intentionally obsolete.
6. Run `preflight-change` and all locally reproducible deterministic gates on the exact integrated head before making the stack publication-ready; CI confirms that evidence rather than discovering basic failures.
7. PVR-09 reruns PRE_REAL and human/reference-grade acceptance, transfers durable truth to `design/` / current-state docs and deletes this workstream by default when complete.

## Durable destinations

- `design/ux-contract.json`: settled task model, IA, hierarchy, states and journeys.
- `design/brand-kit.json`: visual identity/design-system v0.6.
- `frontend/src/design/` + canonical components: executable visual system.
- `.engineering/e2e.json` / PRE_REAL contract: journey/fidelity evidence.
- accepted target/golden manifests: bounded visual provenance.

## Completion

DONE only when the product still answers the same evidence-backed decision correctly, the v0.6 visual system is consistently implemented, no page owns a competing design system, J0-J9 and packaged-product evidence remain green, accessibility/adaptive behavior agrees with the contract, and the final human review supports the premium/reference-grade claim.
