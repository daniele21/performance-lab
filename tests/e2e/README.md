# Deterministic product E2E

Performance Lab deliberately uses several E2E environments because they prove different claims. Executor location (agent-local vs GitHub vs real environment) is separate from environment fidelity; see [`.engineering/e2e.json`](../../.engineering/e2e.json). The automated gate that must pass before `RUNTIME-1` is declared ready is [`.engineering/pre-real-e2e.json`](../../.engineering/pre-real-e2e.json).

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

The frontend Playwright suite runs the built React product in Chromium and proves J0-J9 browser interaction, recovery, evidence drill-down, comparison, adaptive behavior and reduced-motion behavior. Its `/api/v1/**` responses are mocked, so it must not be presented as assembled Python-product evidence.

The pre-real browser pass runs the same declared journeys in a deterministic 1280x900 desktop browser context and retains a final screenshot plus full Playwright trace for every J0-J9 test:

```bash
python scripts/pre_real_e2e.py --output-root build/pre-real-e2e
```

The output contains the raw Playwright JSON, attachments, `browser-manifest.json` and `browser-summary.md`. This is browser/device-context emulation evidence; the environment keeps the canonical `host_or_fake` fidelity because the Python API/persistence layer is mocked.

## Packaged full product — `representative_virtual`

`python scripts/package_release.py --require-full-product-e2e` builds the real package candidate, runs package smoke, then executes the current assembled-product journeys J0/J1/J8/J9 through:

```text
Chromium
-> packaged built frontend
-> packaged Python wheel / real UI API
-> real RunJobManager/orchestrator
-> real SQLite evidence store
-> deterministic external inference HTTP fixture
-> persisted run/campaign evidence reopened after browser reload
```

Packaged Playwright runs retain JSON, final screenshots and traces on success as well as failure under `frontend/test-results-full-product`. The artifact is promoted into the immutable successful artifact lineage only after the selected packaged validation passes.

## Pre-real readiness gate

`PRE_REAL_E2E` is PASS only when:

- every browser journey J0-J9 passes and has a retained final screenshot and trace;
- packaged J0/J1/J8/J9 pass with the same evidence requirements;
- the built/package gate itself succeeds.

Built Product CI combines those layers with:

```bash
python scripts/finalize_pre_real_e2e.py \
  --browser-manifest build/pre-real-e2e/browser-manifest.json \
  --packaged-report frontend/test-results-full-product/report.json \
  --output-root build/pre-real-e2e
```

Only a final `READY_FOR_REAL_ENVIRONMENT: YES` makes `RUNTIME-1` the next acceptance step. Missing automated evidence is a blocker, not something delegated to the real device run.

## Real runtime/device — `target_environment`

For real Local LLM Server/model/device evidence, use [`../real_runtime/README.md`](../real_runtime/README.md) and the representative-device workstream. Real model/runtime identity, physical memory/resources, telemetry sensors, thermals and repeated-load behavior remain residual `RUNTIME-1` evidence. A hosted CI or fixture run never satisfies those claims.
