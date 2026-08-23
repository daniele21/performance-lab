# Engineering contract

Performance Lab targets the `daniele21/repo-template-sw` **0.5.0** L2 operating model with the `product-ui` profile.

Canonical machine-readable contracts:

- `baseline.json` — adopted template version, target level/profile and skill lineage;
- `commands.json` — native setup/check/test/E2E/build/runtime/cleanup intents;
- `documentation-policy.json` — repository documentation and agent-context budgets.

Use the native Python/npm commands declared in `commands.json` rather than inventing parallel wrappers. `frontend/package-lock.json` is the frozen browser dependency source and `requirements/ci-constraints.txt` is the constrained Python CI source.

## Current adoption boundary

The repository can already truthfully enforce product-experience contracts, bounded docs/agent context, deterministic Python/frontend tests and product E2E.

The template's full built-product guarantees are **not yet complete**. `REL-UI-001` owns:

- unique build ID plus source revision and dirty-state identity;
- immutable successful artifact publication;
- build manifest + SHA-256 checksums;
- comparable-build delta output;
- bounded artifact retention and release promotion;
- built-artifact smoke/stop/clean and zero-residue verification.

Until `REL-UI-001` lands, `commands.json` intentionally reports those guarantees as deferred/false. Do not flip the contract to green merely to satisfy a verifier; implement the lifecycle first, then enable the strict operations/repository-health checks in the same change.
