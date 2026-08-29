# Performance Lab product design

Status: canonical product-design source of truth
Owner: Performance Lab product UI
Last reviewed: 2026-08-29

This directory specializes `repo-template-sw`'s `product-ui` profile for Performance Lab. It owns the UX contract and durable brand/design decisions. Executable frontend components become the implementation source of truth once they exist, but they must remain compatible with these product contracts.

## Product task model

The default UI is organized around the deployment decision the user is trying to make, not around backend domain modules.

Primary journey:

```text
Choose a use case
  -> select available model candidates
  -> define configuration search depth
  -> review the benchmark campaign
  -> evaluate model × quantization × configuration candidates
  -> understand quality + performance + resource trade-offs
  -> choose the best-fit model and configuration for this device
```

A model candidate is an evidence identity, not only a family name. The same base LLM with a different quantization is treated as a different model candidate. Each tested configuration produces immutable run evidence; an automatic campaign groups those runs without replacing their individual identity.

Direct/manual journey:

```text
Connect a model
  -> choose one scenario
  -> configure one evaluation
  -> run the test
  -> understand the immutable result
```

Primary navigation:

- **Overview** — tested models, recent evidence and decision entry points.
- **Find best setup** — use-case-first model/configuration decision journey. The UX is integrated now; automatic multi-model/configuration campaign execution remains unavailable until the backend owns campaign scheduling and configuration search.
- **Test a model** — direct/manual single-model evaluation. The Model step may connect a loopback inference server, discover its available models/capabilities through the Performance Lab backend, or use an existing configured target.
- **Runs** — immutable run history and drill-down.
- **Compare** — compatibility-first model/run comparison.

Secondary capability is deliberately disclosed under **Library** and **Settings** instead of competing with the primary workflow. Suites, datasets, baselines, regression policies, endpoints and device/target details remain available without dominating normal use.

## Automatic campaign UX contract

`Find best setup` starts from the use case because the use case determines benchmark relevance and decision evidence.

The product flow is:

1. **Use case** — application-owned mapping to versioned benchmark suites, dataset snapshots, evaluators and decision evidence.
2. **Models** — candidates are discovered from connected inference endpoints; model artifact + quantization are distinct candidates.
3. **Configuration search** — request-level parameters may be swept when supported. Runtime/model-load parameters participate only when the serving runtime publishes an explicit mutable configuration contract; Performance Lab must not assume ownership of model loading.
4. **Campaign** — a bounded campaign schedules candidate configurations as immutable runs, exposes progress/failure/cancellation and preserves run-level evidence identity.
5. **Results** — recommend the best-fit model + quantization + configuration for the selected use case while keeping quality, runtime performance and resources separate. Also expose meaningful alternatives such as highest quality, fastest and lowest-resource candidates when evidence supports those labels.

No automatic winner may be shown unless the relevant evidence is comparable and the decision policy is explicit/versioned. A universal opaque model score remains forbidden.

## Reference views

[`reference/ux-reference-board.svg`](reference/ux-reference-board.svg) is the canonical multi-surface UX reference board for the existing manual/run evidence product. It covers:

1. Overview / tested models
2. Test a model / scenario selection
3. Live run
4. Run detail / results
5. Compare, including an explicit not-comparable decision state
6. Failure / recovery

[`reference/model-connection.svg`](reference/model-connection.svg) is the canonical desktop reference for the first step of `Test a model`: loopback connection setup, backend-owned discovery, model selection, capability disclosure and read-only runtime configuration evidence.

[`reference/find-best-setup.svg`](reference/find-best-setup.svg) defines the desktop UX for the use-case-first automatic decision journey: use case, candidate models, configuration search, campaign matrix and evidence-backed best-fit result.

The references are product guidance, not evidence that the full workflow is shipped. Every displayed metric/control remains conditional on trustworthy backend evidence and supported application contracts.

## Contracts

- [`ux-contract.json`](ux-contract.json) — information architecture, progressive disclosure, states, accessibility, critical journeys and evidence expectations.
- [`brand-kit.json`](brand-kit.json) — semantic color/typography/spacing/radius/motion/microcopy contract.

## Non-negotiable product rules

- No universal opaque model score. Quality, runtime and resources remain separate dimensions.
- `NOT_COMPARABLE`, `NOT_EVALUATED`, unknown, unavailable and partial evidence are first-class states.
- A run is the immutable evidence unit in the backend; a campaign groups runs but does not replace run identity.
- Model family name alone does not identify a candidate; quantization remains part of the model/evidence identity when known.
- Advanced dataset/evaluator/protocol/telemetry/search controls use progressive disclosure.
- Model/runtime discovery is backend-owned; the browser does not call inference runtimes directly.
- Runtime-load configuration remains observational unless the connected runtime publishes an explicit mutable configuration contract and Performance Lab deliberately adopts that control responsibility.
- Automatic campaign recommendations require compatible evidence and an explicit/versioned use-case decision policy.
- Raw logs, JSON and low-level diagnostics stay out of the default workflow unless the user explicitly opens expert/diagnostic surfaces.
- Color never carries critical meaning alone.
- Normal use must have strong defaults.
