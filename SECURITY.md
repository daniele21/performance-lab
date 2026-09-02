# Security policy

## Reporting

Please report suspected vulnerabilities privately through GitHub's security-advisory flow for this repository when available. Do not publish exploitable details, credentials, private prompts/outputs or endpoint configuration in a public issue before a remediation path is agreed.

## Trust boundaries

Performance Lab is a local evaluation product that calls externally served inference endpoints. The lab does not own the model-runtime lifecycle and must not silently move inference or user evidence to a remote service.

Treat these as security-sensitive boundaries:

- endpoint credentials and authorization metadata;
- imported datasets and workload examples;
- prompts, generated outputs and per-sample evidence;
- SQLite run stores and exported `.plab.zip` bundles;
- Local LLM Server identity/status/telemetry integration;
- the loopback UI/API listener and browser-to-local-process traffic.

## Repository baseline

- Secrets, API keys, signed URLs, tokens and credentials are never committed or serialized into portable evidence.
- Authentication is referenced indirectly; persisted endpoint identity must remain safe to export.
- Aggregate-safe modes must not retain prompt/output content unless evidence-rich persistence is explicitly selected.
- Sensitive payloads and private paths stay out of normal logs, telemetry and CI artifacts by default.
- Local UI/API processes bind to loopback unless a separately reviewed feature intentionally changes that trust boundary.
- Local-only behavior must never silently fall back to cloud processing.
- Temporary files, working runs, browser/E2E evidence and other ephemeral resources need bounded retention and deterministic cleanup.
- Imported files and portable bundles are untrusted input and must be validated before use.
- Dependency and security scanning should match the current Python/browser threat surface and become a release gate before broad distribution.

## Supported development line

Security fixes should be developed against the current `dev` integration line and promoted deliberately to `main` after the applicable validation and release evidence are green.
