---
name: plan-workstream
description: Plan substantial Performance Lab work as observable vertical outcomes with parallel technical subtasks and early convergence rather than stacked publication ceremony.
---

# Plan Workstream

Use a durable workstream only when dependency or parallel coordination genuinely adds value. Prefer slices that unlock an observable user/system outcome; Python layers, adapters, frontend pieces and test harness changes are subtasks unless independently valuable/mergeable/reviewable.

Parallel branches may own non-conflicting subtasks but should converge early onto a shared feature/integration branch. Stacked PRs are exceptional; sync-only parent/child PRs are a coordination smell.

For each slice record goal/non-goals, owning paths/contracts, dependencies, `READY|ACTIVE|BLOCKED|DONE`, convergence point, fast iteration checks and integration/release gates. Keep `docs/current-state.md` for integrated/blocked/next repository truth, not temporary branch activity. Delete completed workstreams after durable truth moves to canonical docs.
