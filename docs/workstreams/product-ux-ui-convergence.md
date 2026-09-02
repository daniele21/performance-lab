# Product UX/UI convergence

Status: active — refreshed implementation automated evidence passed; representative-human acceptance pending
Owner: product experience / browser UI
Read when: coordinating final UX/UI acceptance

## Goal

Keep Performance Lab a calm precision instrument around the product question:

> For this use case on this device, which available model + quantization + configuration is the best evidence-backed fit, and why?

`design/ux-contract.json` owns product semantics, `design/brand-kit.json` owns visual identity, and the frontend implements them.

## Blocking invariants

- Keep `Overview -> Find best setup -> Test a model -> Runs -> Compare`; Library/Settings remain secondary.
- Preserve immutable Run/Campaign identity, compatibility-before-ranking and separate Quality/Performance/Resources evidence.
- TypeScript must not invent scores, benchmark semantics, parameter ranges, evaluator rationale or runtime capabilities.
- Preserve `essential -> contextual -> advanced -> expert/diagnostics` disclosure.
- Keyboard/focus, reduced motion and supported desktop adaptation remain blocking.
- Automated visual/PRE_REAL evidence never substitutes for representative human usability/accessibility evidence.

## Work graph

| ID | Work | State |
| --- | --- | --- |
| UXUI-00..10 | Existing UX/UI + baseline | DONE |
| PVR-00..07 | Audit, v0.6 system, surfaces and integrated polish | DONE |
| PVR-08 | v0.6 targets + bounded goldens | SUPERSEDED for Overview/Campaign Results by PVR-10 |
| PVR-09A | Prior browser/PRE_REAL/packaged media evidence | HISTORICAL — invalidated for changed surfaces |
| PVR-09B | Prior agent inspection of retained final media | HISTORICAL — invalidated for changed surfaces |
| PVR-09C | Representative human accessibility/usability acceptance | FAIL — hierarchy/progressive disclosure feedback |
| PVR-10 | Four-stage decision hierarchy + desktop implementation refresh | DONE |
| PVR-11 | Fresh browser/PRE_REAL/visual + representative-human acceptance | AUTOMATED PRODUCT/VISUAL PASS — final exact-head confirmation + representative-human acceptance pending |

## Representative-human feedback that reopened the slice

The integrated v0.6 implementation was exercised by the product owner and rejected as the reference UX because the information/action hierarchy remained too flat and progressive disclosure was applied locally without governing the page composition. The seven-stage `Find best setup` representation exposed implementation/lifecycle concepts (`Benchmark plan`, `Campaign`, `Results`) as peer setup steps and gave contextual/technical information excessive default weight.

This is a blocking product-comprehension issue under the PVR-09 acceptance contract, not non-blocking visual polish. Prior automated and agent-inspected evidence remains useful historical evidence for unchanged behavior, but it does not validate the new hierarchy.

## PVR-10 settled structural correction

The approved desktop direction is now implemented as follows:

- **Overview:** decision-first. `Find best setup` and the product question dominate; Recent evaluations follow; Tested models/evidence inventory is quieter and later.
- **Find best setup setup flow:** exactly four user-decision stages: `Goal -> Models -> Optimization -> Review`.
  - **Goal** combines use case + device/target.
  - **Models** defaults to all backend-scoped eligible candidates selected; the user may narrow.
  - **Optimization** foregrounds Quick/Standard/Thorough only when supported by evidence-backed ranges. Standard is preferred when available; authored fixed configuration is the safe fallback when ranges are unavailable. Custom/fixed/range detail is progressive disclosure.
  - **Review** foregrounds candidate count, configurations/model, immutable run count, estimate and launch action. Benchmark/evaluator detail is contextual; fingerprints, decision-policy identifiers, endpoint/provenance and plan digest are advanced/technical.
- **Context pane:** standard/wide desktop may keep a compact `Your setup` summary beside the active decision; compact desktop moves it out of side-by-side mode rather than squeezing the task.
- **Campaign:** progress-first while running; overall progress precedes per-candidate Runs. Leaving the screen does not imply cancellation when server-owned progress persists.
- **Campaign Results:** `compatibility + explicit decision policy -> recommended setup -> backend-owned rationale -> separate Quality/Performance/Resources comparison -> exact-case evidence drill-down`. No trophies, opaque overall score or frontend-authored “best balance” rationale.
- **Test / Live Run:** compact discovery, preflight, freeze, lifecycle and recovery without exposing runtime ownership as browser-owned configuration.
- **Run Detail:** `identity/status -> separate Q/P/R panel -> samples/evidence -> reproducibility`.
- **Runs / Compare:** compact technical register; compatibility and exact metric deltas dominate decoration.
- **Library / Settings:** quieter secondary surfaces preserve backend/runtime ownership boundaries.

## Prior evidence status

The previous validation runs remain historical evidence only:

- Browser Acceptance run `33446780589`, artifact `9778340564`: 20/20 PASS for the superseded v0.6 implementation.
- Built Product run `33446780596`, PRE_REAL artifact `9778368175`: browser J0-J9 PASS for the superseded v0.6 implementation.
- Packaged artifact `9778368537`: packaged J0/J9 and J1/J8 2/2 PASS for the superseded v0.6 implementation.

Because PVR-10 materially changes Overview, Find best setup, Campaign and Campaign Results, affected previous visual/readiness evidence is invalidated by design. Unchanged product/runtime invariants are not invalidated merely by the UX rewrite.

## Refreshed automated evidence

The PVR-10 product tree has passed the repository-owned deterministic frontend gates, the packaged-product workflow and the complete browser journey suite. The only initial Browser Acceptance failure was the intentionally stale Overview visual baseline; no functional journey failed.

Overview and Campaign Results were then recaptured from the real Playwright implementation with a bounded guard that allowed only those two intended golden files to change. The resulting candidate images were inspected and an independent Browser Acceptance run reproduced the committed baseline without snapshot updates while passing all browser journeys and required media verification.

`design/reference/visual-goldens/desktop-standard/manifest.json` owns the exact capture and independent-acceptance provenance. The approved automated baseline deliberately keeps `human_reference_grade_claim` false.

A final exact-head deterministic confirmation is still required after the documentation/provenance edits in this workstream. That confirmation does not replace representative-human accessibility/usability review.

## PVR-11 acceptance gate

Fresh automated evidence is now available. Representative-human review must still answer:

1. Is the primary decision obvious on Overview without internal architecture knowledge?
2. Does Find best setup read as four user decisions rather than backend lifecycle objects?
3. Are current decision, accumulated context and primary next action visually distinct?
4. Are advanced configuration, benchmark protocol, provenance and fingerprints discoverable without dominating normal use?
5. At 1024, standard and wide desktop, does the contextual setup pane preserve rather than squeeze the task?
6. While a Campaign runs, is progress/status/recovery obvious and truthful?
7. In Results, are compatibility and decision policy understood before recommendation, and is the recommendation rationale clearly backend/evidence-owned?
8. Do Quality, Performance and Resources remain separate with unknown/unavailable/not-comparable states truthful?
9. Is keyboard focus visible/predictable and does reduced motion preserve orientation?
10. Are loading, empty, failure, retry, cancellation and partial-evidence states understandable and recoverable?

A PASS may include non-blocking polish notes. Any issue that changes task comprehension, evidence truthfulness, accessibility, recovery or supported-layout operability reopens the owning implementation slice.

Until this representative-human evidence exists, `human_reference_grade_claim` stays `false`.

Physical/model/runtime device evidence is a separate `REAL_ENVIRONMENT` / `RUNTIME-1` concern and must not be inferred from browser acceptance.

## Completion

After final exact-head automated confirmation and representative-human PASS:

1. record accepted durable state in the appropriate design/current-state owner without copying transient run history;
2. verify no UX/UI evidence gap remains;
3. delete this completed workstream by default;
4. keep RUNTIME-1 and other hardware evidence in their separate workstream.

## Durable destinations

- `design/ux-contract.json`: task model, IA, hierarchy, states and journeys.
- `design/brand-kit.json`: visual identity/system.
- `frontend/src/design/` + canonical components: executable visual system.
- `.engineering/e2e.json` / PRE_REAL: journey/fidelity/media evidence contract.
- `design/reference/visual-targets/`: approved design intent references.
- `design/reference/visual-goldens/desktop-standard`: accepted implementation regression baseline after refreshed validation.
