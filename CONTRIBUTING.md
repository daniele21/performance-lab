# Contributing

Performance Lab is contract-first and evidence-first. Changes should preserve the separation between endpoint inference, evaluation semantics, telemetry, persistence, application/API projections and presentation.

## Start here

1. Read [`AGENTS.md`](AGENTS.md) and the closest scoped `AGENTS.md` for the area you will change.
2. Use [`.engineering/commands.json`](.engineering/commands.json) as the canonical setup/check/test/E2E/build/cleanup map.
3. Read [`.engineering/e2e.json`](.engineering/e2e.json) for whole-product or browser/runtime/device/environment-dependent claims.
4. Read [`docs/current-state.md`](docs/current-state.md) only when the work depends on live integrated/blocked/next state.
5. Read the relevant bounded [`docs/workstreams/`](docs/workstreams/) plan only for coordinated work.
6. For meaningful UI/UX changes, read [`design/ux-contract.json`](design/ux-contract.json) and [`design/brand-kit.json`](design/brand-kit.json) before editing components.

Python 3.12+ is required. Frontend development uses the exact Node/pnpm/dependency versions declared under `frontend/` and the operating contract.

## Change discipline

- Start ordinary work from the latest green integration branch defined in [`BRANCHING.md`](BRANCHING.md).
- Find and extend the existing owner before introducing new state, policy, configuration or semantic UI components.
- Keep domain contracts independent from HTTP clients, databases, CLI/UI code and model runtimes.
- Add tests at the lowest layer that can deterministically prove the invariant; add broader E2E only when the claim crosses that boundary.
- Never persist raw API keys, bearer tokens or other authorization secrets in run evidence or portable bundles.
- Do not report unavailable evidence as zero or infer hidden runtime/device identity.
- UI/application code must preserve typed unknown/partial/not-comparable states and must not recreate canonical comparability semantics in TypeScript.
- When integrated/blocked/next repository state changes, update `docs/current-state.md` in the same change.
- Durable architecture/ownership decisions require the existing architecture owner or an ADR as appropriate.
- Completed workstreams are finalized into durable owners and deleted by default; Git history owns implementation history.

## Validation and preflight

While iterating, run the narrowest useful gate. Before publication, use `skills/preflight-change/SKILL.md` and the automatic selector rather than choosing full CI by habit:

```text
uv run --extra dev --locked python scripts/select_validation_profile.py --base <base-sha> --head <head-sha>
```

The selector resolves `LEAN`, `SCOPED`, `STRONG` or `FULL`, reports why, and fails safe to stronger validation for unknown executable scope. Engineering/CI/dependency/toolchain/selector changes and `dev -> main` promotion require `FULL`.

If a required deterministic gate is unavailable in the current coding-agent environment, route it to repository-owned GitHub automation as `REMOTE_AUTOMATED`; do not ask the repository owner to become the runner. Real external runtime/model/device/telemetry evidence is separate `REAL_ENVIRONMENT` evidence.

E2E environment fidelity is also explicit:

- browser Playwright with mocked Performance Lab API is `host_or_fake` browser evidence;
- the Python product fixture is `representative_virtual` system-boundary evidence;
- packaged J1 is `representative_virtual` assembled-product evidence;
- real Local LLM Server/model/device evidence is `target_environment` only for the claims it actually establishes.

At minimum, code changes satisfy the selected Python/frontend check/test scope. Cross-boundary/user-facing/release changes add the relevant product E2E, browser E2E, build/package/smoke and packaged full-product E2E. `RUNTIME-1` performance/resource/telemetry/thermal claims remain pending until real representative evidence exists.

Repository-health CI blocks drift in the adopted repo-template-sw structural, operating, E2E-fidelity, product-experience, documentation and agent-context contracts. Built-product changes preserve unique build/source identity, immutable publication only after required validation, manifest/checksum, comparable-build delta, bounded retention and zero-residue cleanup.

Use the pull-request template to record exact head/base, selected profile, local/remote gates, E2E environment/fidelity and residual real-environment evidence. Never upgrade an unexecuted hardware/accessibility/usability claim to PASS.
