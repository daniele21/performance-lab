# Active workstreams

This directory contains only bounded implementation/evidence plans that need explicit dependency/state coordination.

Current active workstreams:

- [`representative-device-evidence.md`](representative-device-evidence.md) — validate real model/runtime/device identity, telemetry, repeatability and representative comparison/regression evidence.
- [`local-llm-migration.md`](local-llm-migration.md) — migrate or deliberately retain/remove overlapping Local LLM Server evaluation workflows after parity and consumer evidence.

The completed UI productization workstream was deleted after Compare, Library/Settings, browser J1-J6 acceptance and the built-product lifecycle were integrated; Git history owns that completed plan.

Lifecycle rules:

1. Create a workstream only when the change is too coordinated for local code/tests plus `current-state.md`.
2. Keep scope, dependencies, remaining gates and durable destinations explicit.
3. Do not duplicate architecture, design, feature or operational-reference truth.
4. Keep the plan within `.engineering/documentation-policy.json` budgets.
5. When complete, transfer durable behavior/decisions to their canonical owners and delete the workstream by default.
6. Archive only when an independent audit, regulatory, release or historical requirement justifies it; Git history is the normal archive.
