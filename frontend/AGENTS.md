# Frontend contributor contract

Read [`../design/README.md`](../design/README.md), [`../design/ux-contract.json`](../design/ux-contract.json) and the relevant active UI workstream when one exists before changing product interaction. Read [`../.engineering/e2e.json`](../.engineering/e2e.json) when the change affects a critical journey or assembled browser/product claim.

## Invariants

- Organize the default UI around user tasks, not Python package/domain names.
- Python application/domain contracts own benchmark semantics, comparability, regression and immutable evidence.
- The frontend consumes versioned application/read models; it never reads SQLite directly.
- Keep quality, runtime and resource evidence separate.
- Foreground `NOT_COMPARABLE`, unavailable and partial evidence instead of repairing or hiding it.
- Keep advanced benchmark controls and diagnostics progressively disclosed.
- Reuse canonical semantic components before introducing a new pattern.
- Preserve keyboard/focus semantics and do not communicate critical state by color alone.
- Development/preview listeners bind to loopback and run in the foreground.
- Playwright with mocked `/api` proves browser behavior, not the assembled Python product.

## Validation

While iterating, use the applicable native scripts:

```text
pnpm --dir frontend run check
pnpm --dir frontend run test
pnpm --dir frontend run build
```

For affected J1-J6 browser behavior, use `pnpm --dir frontend run test:e2e` when selected by blast radius. For package/assembled-product J1, the stronger `packaged-product-fixture` path is `uv run --extra dev --locked python scripts/package_release.py --require-full-product-e2e` (or the Built Product CI job), which exercises the packaged wheel, built frontend, real loopback API/SQLite and Chromium against the deterministic inference fixture.

Use repository-level `.engineering/commands.json`, the validation-profile selector and preflight for assembled validation. Real runtime/model/device claims remain outside browser E2E and require the declared `RUNTIME-1` real-environment evidence.
