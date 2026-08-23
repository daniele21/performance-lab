# Core project-local Skills

These Skills are copied from the adopted `repo-template-sw` baseline and versioned with Performance Lab. They encode recurring procedures that should not inflate the root `AGENTS.md`.

Core set:

- `plan-workstream` — create a bounded dependency-aware active plan only when coordination is justified;
- `structured-change` — preserve ownership, simplicity, resource/failure/data invariants during meaningful changes;
- `design-product-experience` — reason through meaningful UX/UI work in the correct order, with proportional depth, before implementation/polish;
- `validate-change` — choose the narrowest sufficient validation while iterating and the correct final gate;
- `finalize-workstream` — transfer durable knowledge and delete completed plans by default;
- `review-reference-quality` — perform an L0/L1/L2 gap review before important milestones.

Specialize a local copy only when Performance Lab needs a durable project-specific procedure, and mark that skill as customized in `.engineering/baseline.json` so future baseline migrations merge rather than overwrite it.

`design-product-experience` is active because this repository adopts the `product-ui` profile. Visual-only token/style edits should remain proportional rather than expanding into unnecessary structural UX work.
