---
name: remote-preflight
description: Satisfy Performance Lab integration/release deterministic gates through repository-owned automation, reusing equivalent successful evidence before executing only missing work.
---

# Remote Preflight

Use this Skill only after `preflight-change` reaches `INTEGRATION` or `RELEASE` and required deterministic gates need `REMOTE_AUTOMATED` execution.

Read `.engineering/commands.json` and record exact head/source tree, target/base, stage, risks, required gates, profile and applicable E2E identity. Search successful evidence before triggering new CI.

Reuse exact-head evidence when the candidate head/base/gates/profile/E2E claim are still sufficient. Performance Lab also allows content-preserving post-merge reuse on `dev` only when repository-owned automation proves the merge commit tree equals the validated source tree and the merge parent equals the validated target/base. A different commit SHA is acceptable only for that tree-equivalent merge transformation; a direct push, moved base, changed tree, broadened gates or expired evidence requires normal validation.

If evidence is sufficient, return confirmed without rerunning expensive gates. Otherwise run only missing/stale/insufficient gates through the repository-owned automatic PR workflow. Do not request FULL merely because it is operationally simpler.

The automatic PR owner is `.github/workflows/validate.yml`. Built-product subsumes its overlapping frontend/product/browser cone when selected. Dedicated browser/built-product workflows are not additional mandatory automatic PR runs.

On failure inspect the owning job/log, classify `CHANGE_REGRESSION|BASELINE_FAILURE|ENVIRONMENT|FLAKY|BASE_DRIFT|ASSUMPTION`, repair the owner, reselect risks/gates and rerun only invalidated evidence. Keep change-branch execution read-only, same-repository by default, without production secrets and with bounded evidence retention.

Report stage/head/tree/target, risks/profile/gates, reused evidence, newly executed gates, E2E environment/mode, failure class and residual real-runtime evidence.