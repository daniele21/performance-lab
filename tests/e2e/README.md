# Deterministic product E2E

These tests exercise Performance Lab as a product rather than as isolated Python components.
A real local HTTP fixture process exposes the minimum OpenAI-compatible inference contract plus
Local LLM Server identity and status surfaces. The test then drives the actual CLI in subprocesses.

The mandatory PR gate covers:

```text
probe
  -> baseline run
  -> immutable SQLite publication
  -> .plab.zip export
  -> inspect
  -> repeated compatible run
  -> PASS regression
  -> deliberately degraded candidate
  -> FAIL regress-ci artifact
```

It also verifies that a configured `required: true` first-party identity failure stops the run before
evaluation rather than silently degrading identity quality.

The fixture is deterministic and does not load a model. It is implementation/product-boundary
evidence, not representative model or device evidence.

Run only the product E2E suite:

```bash
python -m pytest tests/e2e -v --tb=short
```

The normal `python scripts/validate.py` gate intentionally excludes `tests/e2e`; GitHub Actions runs
the E2E suite once in its own Python 3.12 job so library validation and product-workflow failures stay
separate and the full starter workflow is not duplicated across the Python matrix.

For a real Local LLM Server/model/device smoke, use [`../real_runtime/README.md`](../real_runtime/README.md).
