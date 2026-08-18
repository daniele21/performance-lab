# Performance Lab visual references

Status: legacy visual-reference archive
Owner: Performance Lab product UI
Last reviewed: 2026-08-17

The canonical product-design source of truth has moved to [`../../../design/README.md`](../../../design/README.md), with formal contracts in `design/ux-contract.json` and `design/brand-kit.json`.

The raster assets in this directory are retained only as earlier generated visual exploration. They are **not** the current information-architecture contract and must not override the canonical product task model.

Current canonical reference: [`../../../design/reference/ux-reference-board.svg`](../../../design/reference/ux-reference-board.svg).

The superseding direction organizes the product around:

```text
Overview
Test a model
Runs
Compare

Library
Settings
```

The guided evaluation flow is Model -> Scenario -> Test -> Review, with advanced protocol/dataset/evaluator/telemetry controls progressively disclosed. Comparison is compatibility-first, and failures always expose an actionable recovery path.

The active implementation DAG that realizes these views is [`../../workstreams/ui-productization.md`](../../workstreams/ui-productization.md).

Older generated assets remain useful for palette/logo inspiration only; executable metrics, state semantics and interaction hierarchy are governed by the canonical design contracts and backend/API evidence.
