# Active workstreams

This directory contains only bounded implementation plans that need explicit dependency/state coordination.

Current active workstream:

- [`ui-productization.md`](ui-productization.md) — complete the local visual product, browser acceptance, migration gates and built-product lifecycle.

Lifecycle rules:

1. Create a workstream only when the change is too coordinated for local code/tests plus `current-state.md`.
2. Keep scope, dependencies, remaining gates and durable destinations explicit.
3. Do not duplicate architecture, design, feature or operational-reference truth.
4. Keep the plan within `.engineering/documentation-policy.json` budgets.
5. When complete, transfer durable behavior/decisions to their canonical owners and delete the workstream by default.
6. Archive only when an independent audit, regulatory, release or historical requirement justifies it; Git history is the normal archive.
