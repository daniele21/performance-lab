# Engineering contract

Performance Lab targets the `daniele21/repo-template-sw` **0.8.0** L2 operating model with the `python`, `typescript` and `product-ui` profiles.

Canonical machine-readable contracts:

- `baseline.json` — adopted template version, target level/profiles and Skill lineage;
- `commands.json` — native setup/check/test/E2E/build/runtime/cleanup intents plus publication, execution-capability and validation-profile routing;
- `e2e.json` — critical journeys, target/execution environments, environment fidelity and residual real-environment gaps;
- `documentation-policy.json` — repository documentation and agent-context budgets.

Use the native Python/npm commands declared in `commands.json` rather than inventing parallel wrappers. `frontend/package-lock.json` is the frozen browser dependency source and `requirements/ci-constraints.txt` is the constrained Python CI source.

## Current adoption boundary

The repository truthfully enforces:

- bounded documentation and agent context;
- deterministic Python/frontend checks and Product E2E;
- Playwright Chromium browser acceptance for J1-J6;
- packaged full-product E2E for the J1 golden path;
- explicit separation of executor capability from environment fidelity;
- automatic LEAN/SCOPED/STRONG/FULL validation selection with fail-safe escalation;
- repository-owned remote validation rather than user-as-runner fallback;
- executable product-experience, adaptive and reduced-motion contracts;
- unique build/source identity, immutable artifact publication, manifest/checksum/build delta and bounded retention;
- built-product smoke, stop/clean and strict operations/E2E-contract verification.

`.engineering/commands.json` and `.engineering/e2e.json` must remain truthful owners. `scripts/verify_operations.py`, `scripts/verify_e2e.py` and `scripts/select_validation_profile.py --self-test` are blocking repository-health checks.

Repository-local automation does not prove representative hardware/model performance. Real runtime/model/device/telemetry/thermal claims remain explicit `REAL_ENVIRONMENT` evidence under `RUNTIME-1`; hosted CI or deterministic fixtures must never be promoted into those claims.
