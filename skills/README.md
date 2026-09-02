# Core project-local Skills

These Skills are copied from the adopted `repo-template-sw` baseline and versioned with Performance Lab. They encode recurring procedures that should not inflate the root `AGENTS.md`.

Core set:

- `plan-workstream` — create a bounded dependency-aware active plan only when coordination is justified;
- `structured-change` — preserve ownership, ambiguity, simplicity, resource/failure/data and operating invariants during meaningful changes;
- `design-product-experience` — reason through meaningful UX/UI work in the correct order, with proportional depth, before implementation/polish;
- `validate-change` — choose the narrowest sufficient iterative validation and the cheapest sufficient declared E2E fidelity;
- `preflight-change` — establish exact-head/base readiness, select LEAN/SCOPED/STRONG/FULL and classify local/remote/real-environment evidence;
- `remote-preflight` — use repository-owned GitHub automation for required deterministic gates unavailable to the current agent;
- `finalize-workstream` — transfer durable knowledge and delete completed plans by default;
- `review-reference-quality` — perform an L0/L1/L2 gap review before important milestones.

Specialize a local copy only when Performance Lab needs a durable project-specific procedure, and mark that Skill as customized in `.engineering/baseline.json` so future migrations merge rather than overwrite it.

`design-product-experience` is active because this repository adopts `product-ui`. `python` and `typescript` profiles map onto the existing Python core/API and React/Vite/Playwright surfaces rather than introducing alternate toolchains.
