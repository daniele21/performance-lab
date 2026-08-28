## What changed

<!-- Small, concrete summary. -->

## Why

<!-- User/system outcome and important trade-offs. -->

## Invariants / risk

<!-- Domain contracts, evidence identity, data/resource lifecycle, failure, security or migration implications. Write N/A when truly not applicable. -->

## Product experience

<!-- For user-facing changes: task model / IA / progressive disclosure, critical states and recovery, accessibility/adaptive behavior, design-system/motion/graphics implications and affected J1-J6 journeys. Otherwise N/A. -->

## Build / runtime / artifact lifecycle

<!-- Canonical command intents affected; listener/process/temp cleanup; build identity / manifest / checksum / build delta / retention when applicable. Otherwise N/A. -->

## Pre-publication readiness

<!-- Exact HEAD and target/base revision; material ambiguity, base freshness and full-diff review. State READY_FOR_CI, READY_FOR_REMOTE_PREFLIGHT, AUTOMATED_PREFLIGHT_CONFIRMED or blocked reason truthfully. -->

## Validation profile

<!-- AUTO resolution: LEAN / SCOPED / STRONG / FULL, why it was selected and affected scope/jobs. Stronger is allowed; weaker-than-auto requires explicit justification. -->

## Agent-local validation

<!-- Selected gates the current coding agent could execute directly. Use PASS/FAIL/N/A. -->

## Remote automated validation

<!-- Deterministic gates unavailable agent-local but executed by repository-owned automation. Record exact head/run and PASS/FAIL/PENDING/N/A. Do not delegate these to the user. -->

## E2E environment / fidelity evidence

<!-- For each affected journey: .engineering/e2e.json journey id, execution-environment id, fidelity class, built/package surface, PASS/FAIL/PENDING/N/A and residual target gaps. -->

## Real-environment evidence

<!-- RUNTIME-1 or other physical/runtime/device/telemetry/usability evidence automation cannot truthfully replace. State PASS/PENDING/N/A and why. -->

## Product-experience evidence

<!-- Accessibility/adaptive/visual/usability evidence for stable high-risk UI changes. Otherwise N/A. -->

## Evidence lifecycle

<!-- Cleanup verification plus trace/screenshot/log identity, privacy and bounded retention when applicable. -->

## Documentation / design lifecycle

<!-- Canonical docs/design/E2E contracts updated, or why none are required. Finalize/delete completed workstreams by default. -->
