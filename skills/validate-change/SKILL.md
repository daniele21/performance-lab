---
name: validate-change
description: Select the cheapest sufficient Performance Lab validation by delivery stage and risk, escalating only when changed invariants require stronger product/browser/package or real-runtime evidence.
---

# Validate Change

Optimize for sufficient confidence per feedback time. `.engineering/commands.json` owns stage/gate routing; `.engineering/e2e.json` owns journey/fidelity/evidence mode.

## ITERATION
Run focused owner-local Python/frontend checks that can falsify the current edit. Do not require exact-head, durable-doc freshness, product E2E, browser E2E, built-product packaging or real-device evidence merely because those gates exist.

## INTEGRATION
For a coherent observable outcome, use the selector's **risk dimensions -> required gates -> profile** mapping. Performance Lab may require Python, frontend, product E2E, browser E2E or built-product. When built-product is selected it satisfies the overlapping integrated frontend/product/browser cone rather than requiring duplicate workflows.

## RELEASE
Use FULL plus release-critical artifact/E2E gates and residual real-runtime evidence.

UI evidence modes are `ASSERTIONS`, `SCREENSHOTS`, `FULL_MEDIA`. Use FULL_MEDIA for campaign/evaluation progression, retry and cancellation lifecycle; screenshots for stable comparison/inspection semantics. `RUNTIME-1` remains `REAL_ENVIRONMENT` for real model/runtime/device/telemetry/thermal claims.

Classify failures before editing: change regression, baseline, environment, flaky, base drift or assumption. Fix the owning invariant; never suppress a legitimate gate. Hand exact-head integration/release readiness to `preflight-change`.
