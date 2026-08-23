# Contributing

Performance Lab is contract-first and evidence-first. Changes should preserve the separation between endpoint inference, evaluation semantics, telemetry, persistence, application/API projections and presentation.

## Start here

1. Read [`AGENTS.md`](AGENTS.md) and the closest scoped `AGENTS.md` for the area you will change.
2. Use [`.engineering/commands.json`](.engineering/commands.json) as the canonical setup/check/test/E2E/build/cleanup command map.
3. Read [`docs/current-state.md`](docs/current-state.md) only when the work depends on live integrated/blocked/next state.
4. Read the relevant bounded [`docs/workstreams/`](docs/workstreams/) plan only for coordinated work.
5. For meaningful UI/UX changes, read [`design/ux-contract.json`](design/ux-contract.json) and [`design/brand-kit.json`](design/brand-kit.json) before editing components.

Python 3.12+ is required. Frontend development uses the exact Node/npm/dependency versions declared under `frontend/` and the operating contract.

## Change discipline

- Start ordinary work from the latest green integration branch defined in [`BRANCHING.md`](BRANCHING.md).
- Find and extend the existing owner before introducing new state, policy, configuration or semantic UI components.
- Keep domain contracts independent from HTTP clients, databases, CLI/UI code and model runtimes.
- Add tests at the lowest layer that can deterministically prove the invariant; add broader integration/E2E evidence only when the claim crosses that boundary.
- Never persist raw API keys, bearer tokens or other authorization secrets in run evidence or portable bundles.
- Do not report unavailable evidence as zero or infer hidden runtime/device identity.
- UI/application code must preserve typed unknown/partial/not-comparable states and must not recreate canonical comparability semantics in TypeScript.
- When integrated/blocked/next repository state changes, update `docs/current-state.md` in the same change.
- When substantial coordinated work changes scope/dependencies/acceptance, update the single owning active workstream. Do not create or append implementation-history changelogs.
- Durable architecture/ownership decisions require the existing architecture owner or an ADR as appropriate.
- Completed workstreams are finalized into durable owners and deleted by default; Git history owns implementation history.

## Validation

While iterating, run the narrowest useful gate. Before merge, expand according to blast radius using `.engineering/commands.json`.

At minimum, repository code changes should satisfy the applicable Python/frontend `check` and `test` gates. User-facing/build/runtime changes add the corresponding build, E2E, smoke, accessibility/adaptive or real-device evidence when the claim requires it.

Repository-health CI separately checks the adopted repo-template-sw structural, product-experience, documentation and agent-context contracts. The strict operating-contract verifier is intentionally deferred until `REL-UI-001` implements build identity and artifact lifecycle rather than claiming guarantees that do not yet exist.

Use the pull-request template to record exact validation executed and evidence still pending. A green host/fixture branch is not representative hardware or usability evidence.
