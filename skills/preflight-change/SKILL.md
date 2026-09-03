---
name: preflight-change
description: Establish exact-head readiness for a Performance Lab integration or release candidate, reusing equivalent evidence before running only missing gates.
---

# Preflight Change

Use this Skill when a coherent observable outcome moves to `INTEGRATION` or `RELEASE`. Do not require full publication ceremony for ordinary `ITERATION` edits, temporary pushes or draft collaboration updates; those belong to `validate-change`.

1. Record stage, exact head and target/base. `RELEASE` requires FULL; `INTEGRATION` uses the narrowest sufficient risk profile.
2. Resolve material ambiguity, review the complete diff and make affected durable documentation current.
3. Run `scripts/select_validation_profile.py` and record risk dimensions, concrete required gates and the profile shorthand.
4. When E2E is needed, select the smallest affected journey, cheapest sufficient declared environment and `ASSERTIONS|SCREENSHOTS|FULL_MEDIA` mode. `RUNTIME-1` real runtime/device/resource claims remain `REAL_ENVIRONMENT`.
5. Classify required gates as `AGENT_LOCAL`, `REMOTE_AUTOMATED` or `REAL_ENVIRONMENT`.
6. Before triggering remote work, reuse successful evidence only when head/source tree, target/base, required gates/profile and relevant E2E identity remain equivalent. Collaboration metadata alone does not invalidate proof.
7. For a content-preserving squash/rebase merge into `dev`, repository automation may reuse trusted integration evidence only when the post-merge Git tree equals the validated source tree and the merge parent is the same target/base revision. Direct pushes without equivalent evidence must validate normally.
8. Run or route only missing, stale or insufficient deterministic gates. Do not delegate automatable work to the user.
9. Classify failures as change regression, baseline, environment, flaky, base drift or assumption; fix the owning invariant rather than weakening a gate.

Performance Lab automatic PR validation is owned by `.github/workflows/validate.yml`. When `built-product` is required it satisfies the overlapping frontend/product/browser integration cone instead of forcing duplicate workflows. Dedicated browser/built-product workflows are diagnostic/manual or tag/release surfaces, not parallel automatic PR owners.

Report `STAGE`, `HEAD`, `TARGET`, `RISKS`, `REQUIRED_GATES`, `VALIDATION_PROFILE`, `REUSED_EVIDENCE`, deterministic gate status, E2E environment/mode, residual `REAL_ENVIRONMENT` gaps and final readiness.