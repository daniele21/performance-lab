# Frontend contributor contract

Read [`../design/README.md`](../design/README.md), [`../design/ux-contract.json`](../design/ux-contract.json) and the active [`../docs/workstreams/ui-productization.md`](../docs/workstreams/ui-productization.md) before changing product interaction.

## Invariants

- Organize the default UI around user tasks, not Python package/domain names.
- Python application/domain contracts own benchmark semantics, comparability, regression and immutable evidence.
- The frontend consumes versioned application/read models; it never reads SQLite directly.
- Keep quality, runtime and resource evidence separate.
- Foreground `NOT_COMPARABLE`, unavailable and partial evidence instead of repairing or hiding it.
- Keep advanced benchmark controls and diagnostics progressively disclosed.
- Reuse canonical semantic components once `UIK-001` establishes them.
- Preserve keyboard/focus semantics and do not communicate critical state by color alone.
- Development/preview listeners bind to loopback and run in the foreground.

## Validation

Before considering a frontend change complete, run the applicable native scripts:

```text
npm --prefix frontend run check
npm --prefix frontend run test
npm --prefix frontend run build
```

Use the repository-level operations in `.engineering/commands.json` for assembled validation.
