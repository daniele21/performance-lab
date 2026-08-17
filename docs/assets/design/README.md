# Performance Lab visual references

Status: durable design reference
Owner: Performance Lab product UI
Last reviewed: 2026-08-17

These assets preserve the approved visual direction for the Performance Lab productization workstream. They are **design references, not screenshots of shipped functionality**. Executable behavior, metrics and ownership remain defined by the domain/API contracts and tests.

## Reference assets

- [`../brand/mark.svg`](../brand/mark.svg) — canonical lightweight vector mark for implementation.
- [`../brand/logo-lockup.svg`](../brand/logo-lockup.svg) — canonical lightweight wordmark + tagline lockup.
- [`../brand/app-icon.webp`](../brand/app-icon.webp) — generated app-icon reference.
- [`ui-reference-board.webp`](ui-reference-board.webp) — compressed visual board containing the complete generated direction:
  - brand system;
  - Overview / tested-models dashboard;
  - New Evaluation;
  - Live Run;
  - Compare;
  - Run Detail;
  - app icon;
  - logo lockup;
  - simplified mark;
  - repository/product hero.

The board is intentionally the durable raster source kept in Git rather than committing every full-resolution generated image separately. This keeps the repository small while retaining the complete design intent.

## Brand direction

Primary principles:

- **Precise** — evidence and metric identity before decorative scoring.
- **Comparable** — quality, runtime and resources stay visually distinct.
- **Evidence-driven** — unknown and unavailable states remain visible.
- **Device-aware** — hardware/runtime identity is part of the product context.
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

The implementation must convert these into semantic design tokens rather than scattering literal values through components.

## Implementation boundary

The generated mockups are intentionally aspirational. In particular:

- a displayed metric may exist only when the backend exposes trustworthy evidence;
- a "best" label must be scoped to a declared compatible cohort and metric, never inferred as a universal model ranking;
- `NOT_COMPARABLE`, `NOT_EVALUATED`, unavailable telemetry and partial identity must be visible product states;
- sample/output retention must follow the actual persistence/privacy contract, not the mockup copy;
- UI controls must map to supported backend protocol fields; unsupported controls must not be silently ignored.

Once the UI is implemented, the executable design-system tokens/components and tested accessibility behavior become the implementation source of truth. This directory remains a compact visual reference, not a parallel behavioral specification.
