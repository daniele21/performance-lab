# Product UX/UI convergence

Status: active — final human evidence pending
Owner: product experience / browser UI
Read when: coordinating final UX/UI acceptance

## Goal

Keep Performance Lab a calm precision instrument around the product question:

> For this use case on this device, which available model + quantization + configuration is the best evidence-backed fit, and why?

`design/ux-contract.json` owns product semantics, `design/brand-kit.json` owns visual identity, and the frontend implements them. This workstream now exists only to close the final representative-human acceptance gate; the implementation/refactor slices are complete.

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
| PVR-08 | Approved v0.6 targets + bounded goldens | DONE |
| PVR-09A | Final browser/PRE_REAL/packaged media evidence | DONE |
| PVR-09B | Agent inspection of retained final media | DONE |
| PVR-09C | Representative human accessibility/usability acceptance | PENDING |

## Settled product experience

- **Foundation/shell:** graphite neutral hierarchy, restrained accent, compact controls, tabular metrics and persistent primary workspace navigation. Library/Settings use progressive disclosure and remain visually subordinate.
- **Overview:** tested-model evidence is primary; recent runs are secondary.
- **Campaign:** progress-first while running. Terminal reading order is `status -> Results/best fit -> completed progress -> candidate Runs`; compatibility and explicit decision policy precede recommendation.
- **Test / Live Run:** compact discovery, preflight, freeze, lifecycle and recovery without exposing runtime ownership as browser-owned configuration.
- **Run Detail:** `identity/status -> separate Q/P/R panel -> samples/evidence -> reproducibility`.
- **Runs / Compare:** compact technical register; compatibility and exact metric deltas dominate decoration.
- **Library / Settings:** quieter secondary surfaces preserve backend/runtime ownership boundaries.

## PVR-08 visual baseline

Five stable surfaces are provenance-bound v0.6 targets and automated goldens: Overview, Test a model frozen review, Benchmark Detail, Sample Evidence Detail and Campaign Results. The target capture was reviewed first; a separate CI capture reproduced all five PNGs byte-for-byte before golden promotion. `human_reference_grade_claim` deliberately remains `false`.

## PVR-09 automated evidence

The final validated PR merge tree is file-identical to integrated `dev`; no product file changed between the validated merge ref and the merge commit.

- Browser Acceptance run `33446780589`, artifact `9778340564`: **20/20 PASS**. Every executed browser test retained screenshot, video and Playwright trace; the required-media verifier passed.
- Built Product run `33446780596`, PRE_REAL artifact `9778368175`: browser J0-J9 **PASS**, with screenshot/video/trace retained for every required journey.
- The same Built Product run, packaged artifact `9778368537`: packaged J0/J9 and J1/J8 **2/2 PASS**, each with screenshot/video/trace.
- PRE_REAL finalizer: browser layer **PASS**, packaged layer **PASS**, `READY_FOR_REAL_ENVIRONMENT: YES`.
- Residual real-environment gaps remain explicit: external model/runtime is a deterministic fixture, hosted CI hardware is not representative target hardware, and thermal/device telemetry is not established.

The retained media were also inspected directly after CI. The review confirmed the expected complete transitions for campaign planning/results, model connection/run, failure recovery, cancellation/restart, progressive secondary navigation, minimum/wide desktop containment and packaged-product loading-to-evidence flow. No blocking visual, hierarchy, overflow or journey regression was found in that inspection.

This closes automated and agent-inspected evidence only. It is not a representative-human acceptance claim.

## PVR-09 representative human gate

Before this workstream can be finalized, a representative human reviewer must exercise the integrated desktop product at the supported contexts (minimum, standard and wide desktop; keyboard-only where applicable; reduced motion enabled for the motion check) and record PASS/FAIL for these acceptance questions:

1. Is the primary task/decision obvious on Overview, Campaign Results and Run Detail without needing internal architecture knowledge?
2. Are primary actions visually distinct from secondary diagnostics, Library and Settings?
3. Do 1024, standard and wide layouts keep critical evidence/actions legible, reachable and free from disruptive clipping/overflow/wrapping?
4. Is keyboard focus visible and predictable, with skip navigation and route-change focus behavior understandable in real use?
5. Are loading, empty, failure, retry, cancellation and unavailable/not-comparable states understandable and recoverable without misleading zeroes or hidden evidence gaps?
6. Does reduced motion preserve orientation and feedback without depending on animation?
7. Do Quality, Performance and Resources remain clearly distinct, and does compatibility/decision-policy language appear before any recommendation or delta that depends on it?

A PASS may include non-blocking polish notes. Any issue that changes task comprehension, evidence truthfulness, accessibility, recovery or supported-layout operability reopens the owning implementation slice before acceptance.

Until this evidence exists, `human_reference_grade_claim` stays `false` and PVR-09 remains active.

Physical/model/runtime device evidence is a separate `REAL_ENVIRONMENT` / `RUNTIME-1` concern and must not be inferred from browser acceptance.

## Completion

After representative-human PASS:

1. record the accepted state in the appropriate durable design/current-state owner without copying transient run history;
2. verify no UX/UI evidence gap remains;
3. delete this completed workstream by default;
4. keep RUNTIME-1 and other hardware evidence in their separate workstream.

## Durable destinations

- `design/ux-contract.json`: task model, IA, hierarchy, states and journeys.
- `design/brand-kit.json`: v0.6 visual identity/system.
- `frontend/src/design/` + canonical components: executable visual system.
- `.engineering/e2e.json` / PRE_REAL: journey/fidelity/media evidence contract.
- `design/reference/visual-targets/desktop-standard-v0.6`: approved bounded v0.6 target provenance.
- `design/reference/visual-goldens/desktop-standard`: accepted implementation regression baseline.
