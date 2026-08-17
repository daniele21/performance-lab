# Performance Lab visual references

Status: durable design reference
Owner: Performance Lab product UI
Last reviewed: 2026-08-17

These assets preserve the approved visual direction for the Performance Lab productization workstream. They are **design references, not screenshots of shipped functionality**. Executable behavior, metrics and ownership remain defined by domain/API contracts and tests.

## Reference assets

- [`../brand/mark.svg`](../brand/mark.svg) — canonical lightweight vector mark for implementation.
- [`../brand/logo-lockup.svg`](../brand/logo-lockup.svg) — canonical lightweight wordmark + tagline lockup.
- [`../brand/app-icon.webp`](../brand/app-icon.webp) — generated app-icon reference.
- [`brand-system.webp`](brand-system.webp) — extracted high-resolution-enough brand/design-system direction.
- [`overview.webp`](overview.webp) — extracted Overview/Tested Models product anchor.
- [`ui-reference-board.webp`](ui-reference-board.webp) — compressed master board containing the full generated direction:
  - Brand System;
  - Overview / Tested Models;
  - New Evaluation;
  - Live Run;
  - Compare;
  - Run Detail;
  - app icon;
  - logo lockup;
  - simplified mark;
  - repository/product hero.

The master board consolidates the remaining generated screen concepts instead of committing every full-resolution raster separately. This keeps durable visual material small while preserving the complete product direction; executable implementation will replace mockup pixels with tested components.

## Brand direction

Primary principles:

- **Precise** — evidence and metric identity before decorative scoring.
- **Comparable** — quality, runtime and resources stay visually distinct.
- **Evidence-driven** — unknown and unavailable states remain visible.
- **Device-aware** — hardware/runtime identity is part of product context.
- **Reproducible** — run fingerprint, suite/evaluator versions and evidence are first-class.

Core palette:

| Token | Value | Intent |
| --- | --- | --- |
| `brand-cyan` | `#00E5FF` | primary technical accent |
| `brand-violet` | `#7B5CFF` | comparison / secondary accent |
| `success` | `#22C55E` | successful evidence / positive state |
| `warning` | `#F59E0B` | warning / partial evidence |
| `graphite-900` | `#0B0F14` | dark shell / high-contrast text |
| `white` | `#FFFFFF` | primary light surface |

Implementation must convert these into semantic design tokens rather than scattering literal values through components.

## Implementation boundary

The generated mockups are aspirational. In particular:

- a displayed metric may exist only when the backend exposes trustworthy evidence;
- a "best" label must be scoped to a declared compatible cohort and metric, never inferred as a universal model ranking;
- `NOT_COMPARABLE`, `NOT_EVALUATED`, unavailable telemetry and partial identity must be visible product states;
- sample/output retention must follow the actual persistence/privacy contract, not mockup copy;
- UI controls must map to supported backend protocol fields; unsupported controls must not be silently ignored.

Once the UI is implemented, executable design-system tokens/components and tested accessibility behavior become the implementation source of truth. This directory remains a compact visual reference, not a parallel behavioral specification.
