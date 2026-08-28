# Performance Lab product design

Status: canonical product-design source of truth
Owner: Performance Lab product UI
Last reviewed: 2026-08-28

This directory specializes `repo-template-sw`'s `product-ui` profile for Performance Lab. It owns the UX contract and durable brand/design decisions. Executable frontend components become the implementation source of truth once they exist, but they must remain compatible with these product contracts.

## Product task model

The default UI is organized around what the user is trying to learn, not around backend domain modules.

```text
Connect a model
  -> choose what you want to learn
  -> run the test
  -> understand results
  -> compare when evidence is compatible
  -> decide
```

Primary navigation:

- **Overview** — tested models, recent evidence and workload-scoped recommendations.
- **Test a model** — guided model -> scenario -> test -> review flow. The Model step may connect a loopback inference server, discover its available models/capabilities through the Performance Lab backend, or use an existing configured target.
- **Runs** — immutable run history and drill-down.
- **Compare** — compatibility-first model/run comparison.

Secondary capability is deliberately disclosed under **Library** and **Settings** instead of competing with the primary workflow. Suites, datasets, baselines, regression policies, endpoints and device/target details remain available without dominating normal use.

## Reference views

[`reference/ux-reference-board.svg`](reference/ux-reference-board.svg) is the canonical multi-surface UX reference board. It covers:

1. Overview / tested models
2. Test a model / scenario selection
3. Live run
4. Run detail / results
5. Compare, including an explicit not-comparable decision state
6. Failure / recovery

[`reference/model-connection.svg`](reference/model-connection.svg) is the canonical desktop reference for the first step of `Test a model`: loopback connection setup, backend-owned discovery, model selection, capability disclosure and read-only runtime configuration evidence.

The references are product guidance, not evidence that the UI is shipped. Every displayed metric/control remains conditional on trustworthy backend evidence and supported application contracts.

## Contracts

- [`ux-contract.json`](ux-contract.json) — information architecture, progressive disclosure, states, accessibility, critical journeys and evidence expectations.
- [`brand-kit.json`](brand-kit.json) — semantic color/typography/spacing/radius/motion/microcopy contract.

## Non-negotiable product rules

- No universal opaque model score. Quality, runtime and resources remain separate dimensions.
- `NOT_COMPARABLE`, `NOT_EVALUATED`, unknown, unavailable and partial evidence are first-class states.
- A run is the immutable evidence unit in the backend; it does not have to be the user's primary mental model.
- Advanced dataset/evaluator/protocol/telemetry controls use progressive disclosure.
- Model/runtime discovery is backend-owned; the browser does not call inference runtimes directly.
- Runtime-load configuration remains observational unless the connected runtime publishes an explicit mutable configuration contract and Performance Lab deliberately adopts that control responsibility.
- Raw logs, JSON and low-level diagnostics stay out of the default workflow unless the user explicitly opens expert/diagnostic surfaces.
- Color never carries critical meaning alone.
- Normal use must have strong defaults.
