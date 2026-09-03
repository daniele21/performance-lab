# Engineering contract

Performance Lab targets the `daniele21/repo-template-sw` **0.9.1** L2 operating model with the `python`, `typescript` and `product-ui` profiles.

Canonical machine-readable contracts:

- `baseline.json` — adopted standard/version, target level/profiles and Skill lineage;
- `commands.json` — native commands plus delivery stages, risk/gate routing and reusable validation evidence;
- `e2e.json` — critical journeys, target/execution environments, risk-based UI evidence modes and residual real-environment gaps;
- `documentation-policy.json` — repository documentation and agent-context budgets.

Use the canonical `uv`/`pnpm` commands rather than inventing parallel wrappers. `uv.lock` and `frontend/pnpm-lock.yaml` are the frozen dependency sources.

## Current adoption boundary

Performance Lab separates delivery stage from validation depth:

- `ITERATION` keeps feedback focused and does not run browser/product/package gates merely because they exist;
- `INTEGRATION` selects concrete required gates from changed risk dimensions and requires exact-head/documentation readiness;
- `RELEASE` forces FULL plus release-critical evidence.

`LEAN | SCOPED | STRONG | FULL` are summaries. `scripts/select_validation_profile.py` owns the concrete `repository-guards`, Python, frontend, product-E2E, browser-E2E and built-product gate selection.

Repository PR automation is consolidated in `.github/workflows/validate.yml`. When `built-product` is required it satisfies the overlapping frontend/product/browser acceptance cone rather than re-running those workflows independently. Dedicated browser/built-product workflows remain manual/tag surfaces.

Successful integration evidence is reusable. Exact-head identity is used before merge; a content-preserving merge to `dev` may reuse the same evidence only when Git tree, prior target/base and required gates/profile are equivalent. Direct pushes without trusted evidence validate normally; release does not silently inherit integration proof.

E2E UI evidence is risk-based: `ASSERTIONS`, `SCREENSHOTS`, `FULL_MEDIA`. Timing/progress/retry/cancel journeys retain FULL_MEDIA; stable inspection/comparison journeys use screenshots. `RUNTIME-1` retains real runtime/model/device/telemetry/thermal evidence as `REAL_ENVIRONMENT`; hosted CI never upgrades those claims.
