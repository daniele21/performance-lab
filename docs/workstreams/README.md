# Active workstreams

This directory contains only bounded implementation/evidence plans that need explicit dependency/state coordination.

Current active workstreams:

- [`incremental-value-delivery.md`](incremental-value-delivery.md) — owns the operational order of end-to-end VALUE slices; M1-M9 remain coverage/maturity labels rather than the development sequence.
- [`product-ux-ui-convergence.md`](product-ux-ui-convergence.md) — close the remaining representative-human accessibility/usability acceptance for the integrated decision-first, Light-first desktop product.
- [`representative-device-evidence.md`](representative-device-evidence.md) — owns real model/runtime/device protocol, retained artifacts, telemetry, repeatability and representative comparison/regression evidence consumed incrementally by VALUE slices.
- [`local-llm-migration.md`](local-llm-migration.md) — owns Local LLM Server replacement/deprecation/removal semantics and evidence; its cutover becomes VALUE-07 only after the replacement loop has already demonstrated user value.

The earlier UI productization workstream was deleted after Compare, Library/Settings, browser acceptance and the built-product lifecycle were integrated. The current product-experience workstream remains only for its final human acceptance gate; it does not own the next product-development sequence.

## Coordination rule

Do not duplicate one status across multiple plans:

- `incremental-value-delivery.md` owns **which user-value slice executes next** and its end-to-end acceptance;
- `representative-device-evidence.md` owns **how real-device evidence is captured and bounded**;
- `local-llm-migration.md` owns **how the cross-repository LLS cutover is performed safely**;
- `product-ux-ui-convergence.md` owns only the remaining **human UX/accessibility acceptance** for the integrated experience.

If a VALUE slice needs evidence/cutover behavior from a specialized workstream, reference that owner instead of copying its protocol.

Lifecycle rules:

1. Create a workstream only when the change is too coordinated for local code/tests plus `current-state.md`.
2. Keep scope, dependencies, remaining gates and durable destinations explicit.
3. Do not duplicate architecture, design, feature or operational-reference truth.
4. Keep the plan within `.engineering/documentation-policy.json` budgets.
5. When complete, transfer durable behavior/decisions to their canonical owners and delete the workstream by default.
6. Archive only when an independent audit, regulatory, release or historical requirement justifies it; Git history is the normal archive.