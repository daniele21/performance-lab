# Product UX/UI convergence

Status: active
Owner: product experience / browser UI
Read when: coordinating final UX/UI acceptance

## Goal

Make Performance Lab a mature precision instrument while preserving the product question:

> For this use case on this device, which available model + quantization + configuration is the best evidence-backed fit, and why?

`design/ux-contract.json` owns product semantics, `design/brand-kit.json` owns visual identity, and the frontend implements them. This workstream does not create a new product architecture.

## Blocking invariants

- Keep `Overview -> Find best setup -> Test a model -> Runs -> Compare`; Library/Settings remain secondary.
- Preserve immutable Run/Campaign identity, compatibility-before-ranking and separate Quality/Performance/Resources evidence.
- TypeScript must not invent scores, benchmark semantics, parameter ranges, evaluator rationale or runtime capabilities.
- Preserve `essential -> contextual -> advanced -> expert/diagnostics` disclosure.
- Keyboard/focus, reduced motion and supported desktop adaptation remain blocking.
- Automated visual acceptance never substitutes for PRE_REAL or human usability/accessibility evidence.

## Work graph

| ID | Work | State |
| --- | --- | --- |
| UXUI-00..10 | Existing UX/UI + before baseline | DONE |
| PVR-00 | Visual/component audit | DONE |
| PVR-01 | `brand-kit` v0.6 contract | DONE |
| PVR-02 | Tokens/primitives/foundation | DONE |
| PVR-03 | Workspace-first shell/navigation | DONE |
| PVR-04A | Overview / Find best setup / Campaign | DONE |
| PVR-04B | Test a model / Live Run / Run Detail | DONE |
| PVR-05 | Runs / Compare / evidence drilldowns | DONE |
| PVR-06 | Library / Settings | DONE |
| PVR-07 | Integrated polish/accessibility/adaptation | DONE |
| PVR-08 | Approved v0.6 targets + bounded goldens | DONE |
| PVR-09 | Final PRE_REAL + human acceptance | READY |

## Implemented product experience

- **Foundation/shell:** graphite neutral hierarchy, restrained accent, compact controls, tabular metrics and persistent primary workspace navigation. Library/Settings use progressive disclosure and remain visually subordinate.
- **Overview:** tested-model evidence is primary; recent runs are secondary.
- **Campaign:** running state is progress-first. Terminal reading order is `status -> Results/best fit -> completed progress -> candidate Runs`. Compatibility and explicit decision policy precede recommendation; there is no hidden aggregate score.
- **Test / Live Run:** denser, quieter chrome preserves discovery, preflight, freeze, lifecycle and recovery semantics.
- **Run Detail:** `identity/status -> separate compact Q/P/R panel -> samples/evidence -> reproducibility`.
- **Runs / Compare:** compact technical register; compatibility and exact metric deltas dominate decoration.
- **Library / Settings:** quieter secondary surfaces preserve backend/runtime ownership boundaries.

## PVR-07 evidence

PR #100 integrated the parallel page slices without moving `dev`. Exact head `3850349f5642116c67fc843cd4413ade56fbc9a7` established:

- Repository Health: PASS;
- Repository Validation: PASS;
- Built Product/PRE_REAL J0-J9: PASS;
- packaged J0/J1/J8/J9: PASS;
- functional Browser acceptance: 19/20 PASS, with the only failure the deliberately obsolete v0.5 `overview.png` golden.

`cross-surface-integrity.spec.ts` also traverses canonical routes at the 1024px minimum desktop width and fails on horizontal document overflow or unresolved `aria-labelledby` / `aria-describedby` references.

## PVR-08 visual acceptance

PVR-08 replaced only the five stable visual-regression surfaces:

- Overview;
- Test a model / frozen review;
- Benchmark detail;
- Sample evidence detail;
- Campaign results.

The acceptance was deliberately two-stage:

1. CI capture #1 produced exactly five changed PNGs. The exact artifact was manually reviewed against the v0.6 UX/brand contracts and promoted to `design/reference/visual-targets/desktop-standard-v0.6` with source head, workflow run, artifact digest and per-file SHA256 provenance.
2. A separate CI capture #2 reproduced all five PNGs byte-for-byte. Promotion refused any mismatch against the approved target manifest, then replaced only the corresponding files under `design/reference/visual-goldens/desktop-standard` and updated its provenance manifest.

The first target artifact came from run `33445346076`; the independent golden capture came from run `33445799989`. The one-off capture/promotion workflows and promotion marker were removed after promotion; durable evidence lives in the target and golden manifests.

The v0.6 golden manifest explicitly keeps `human_reference_grade_claim: false`. PVR-08 therefore proves bounded deterministic visual regression, not representative-user quality.

## PVR-09 — final acceptance

PVR-09 is ready after the PVR-08 exact-head deterministic/browser/built-product gates confirm the current stack. It owns:

- final PRE_REAL J0-J9 screenshot/trace evidence and packaged-product confirmation;
- final representative accessibility/usability review at the supported desktop contexts;
- truthful recording of any environment-only or human evidence that cannot be automated;
- transfer of settled durable truth to design/current-state documentation and default removal of this workstream when complete.

Physical/model/runtime device evidence remains a separate REAL_ENVIRONMENT / RUNTIME-1 concern and must not be inferred from browser acceptance.

## Durable destinations

- `design/ux-contract.json`: task model, IA, hierarchy, states and journeys.
- `design/brand-kit.json`: v0.6 visual identity/system.
- `frontend/src/design/` + canonical components: executable visual system.
- `.engineering/e2e.json` / PRE_REAL: journey and fidelity evidence.
- `design/reference/visual-targets/desktop-standard-v0.6`: approved bounded v0.6 visual target provenance.
- `design/reference/visual-goldens/desktop-standard`: accepted implementation regression baseline.
