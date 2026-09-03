---
name: structured-change
description: Guard meaningful Performance Lab changes against duplicate ownership, unresolved assumptions, excess complexity, unsafe resource/data lifecycle, failure gaps, UX drift and cross-layer contract breakage without making every edit publication-ready.
---

# Structured Change

Find the canonical owner and inspect direct consumers/fakes/tests before changing shared semantics. Preserve immutable fingerprint/evidence ownership, compatibility-before-deltas, provenance, external runtime ownership, bounded local resources and the Python-to-TypeScript semantic boundary.

Prefer observable vertical outcomes; technical layers are subtasks unless independently useful. Spend abstractions/dependencies/workers/UI patterns only for a concrete need. Treat cancellation, failure, recovery and cleanup as normal behavior. Keep secrets and sensitive inference data out of unintended persistence/log/evidence paths.

For product UI, resolve task/journey/hierarchy/states/accessibility before polish and reuse canonical design owners.

During `ITERATION`, keep validation focused and documentation/publication ceremony proportional. Exact-head, complete-diff and durable-documentation readiness begin when the coherent outcome moves to `INTEGRATION` or `RELEASE` through `preflight-change`.
