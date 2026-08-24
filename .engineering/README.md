# Engineering contract

Performance Lab targets the `daniele21/repo-template-sw` **0.5.0** L2 operating model with the `product-ui` profile.

Canonical machine-readable contracts:

- `baseline.json` — adopted template version, target level/profile and skill lineage;
- `commands.json` — native setup/check/test/E2E/build/runtime/cleanup intents;
- `documentation-policy.json` — repository documentation and agent-context budgets.

Use the native Python/npm commands declared in `commands.json` rather than inventing parallel wrappers. `frontend/package-lock.json` is the frozen browser dependency source and `requirements/ci-constraints.txt` is the constrained Python CI source.

## Current adoption boundary

The repository now truthfully enforces the repo-local product and operating contracts adopted in the 0.5 baseline:

- bounded documentation and agent context;
- deterministic Python/frontend checks and Product E2E;
- Playwright Chromium browser acceptance for the declared J1-J6 journeys;
- executable product-experience, adaptive and reduced-motion contracts;
- unique build/source identity and comparable build history;
- immutable successful artifact publication after validation;
- build manifest and SHA-256 checksum metadata;
- bounded local/CI artifact retention;
- built-product smoke, stop/clean and strict operations verification.

`.engineering/commands.json` must remain the truthful source for these guarantees and `scripts/verify_operations.py` is a blocking check.

Repository-local compliance does not prove representative hardware/model performance. Real device/runtime/telemetry claims require the separate representative-evidence workstream. Branch protection/required-check settings are repository administration and remain outside the executable source-tree contract.
