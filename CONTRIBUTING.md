# Contributing

AI Performance Lab is contract-first. Changes should preserve the separation between endpoint inference, evaluation, telemetry, storage and presentation.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python scripts/validate.py
```

Python 3.12+ is required. CI currently validates Python 3.12 and 3.13.

## Change discipline

- Start ordinary work from the latest green integration branch defined in [`BRANCHING.md`](BRANCHING.md).
- Keep domain contracts independent from HTTP clients, databases, CLI/UI code and model runtimes.
- Add tests at the lowest useful layer.
- Never persist raw API keys, bearer tokens, private prompts or generated content merely for diagnostics.
- Do not report an unavailable metric as zero or infer hidden runtime/device identity.
- When a task changes state, update `docs/current-state.md` in the same change.
- When scope/dependencies/acceptance criteria change, update the canonical plan and append the rationale to `docs/plan-changelog.md`.
- Durable architecture changes require an ADR.

## Validation

Before pushing:

```bash
python scripts/validate.py
```

The command runs formatting checks, lint, strict typing and tests; CI executes the same gate from a clean checkout.
