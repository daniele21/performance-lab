# Deterministic product E2E

Performance Lab deliberately uses several E2E environments because they prove different claims. Executor location (agent-local vs GitHub vs real environment) is separate from environment fidelity; see [`.engineering/e2e.json`](../../.engineering/e2e.json).

## Python product fixture — `representative_virtual`

`test_product_workflow.py` exercises Performance Lab as a product rather than as isolated Python components. A real local HTTP fixture exposes the minimum OpenAI-compatible inference contract plus Local LLM Server identity/status, and the test drives the actual CLI in subprocesses.

The mandatory product flow covers:

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

It also verifies that a required first-party identity failure stops the run before evaluation instead of silently degrading identity quality.

This is real CLI/application/HTTP/persistence/regression evidence with a deterministic external inference fixture. It does **not** prove a real model/runtime/device claim.

Run it with:

```bash
python -m pytest tests/e2e -v --tb=short
```

## Browser built + mocked API — `host_or_fake`

`frontend/e2e/critical-journeys.spec.ts` runs the built React product in Chromium and proves J1-J6 browser interaction, recovery, adaptive and reduced-motion behavior. Its `/api/v1/**` responses are mocked, so it must not be presented as assembled Python-product evidence.

## Packaged full product — `representative_virtual`

`python scripts/package_release.py --require-full-product-e2e` builds the real package candidate, runs package smoke, then executes J1 through:

```text
Chromium
-> packaged built frontend
-> packaged Python wheel / real UI API
-> real RunJobManager/orchestrator
-> real SQLite evidence store
-> deterministic external inference HTTP fixture
-> persisted run reopened after browser reload
```

The artifact is promoted into the immutable successful artifact lineage only after this selected packaged validation passes. Failure traces/screenshots live under `frontend/test-results-full-product` and CI retains them for a bounded period.

## Real runtime/device — `target_environment`

For real Local LLM Server/model/device evidence, use [`../real_runtime/README.md`](../real_runtime/README.md) and the representative-device workstream. Real model/runtime identity, physical memory/resources, telemetry sensors, thermals and repeated-load behavior remain residual `RUNTIME-1` evidence. A hosted CI or fixture run never satisfies those claims.
