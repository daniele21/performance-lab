# Performance Lab product design

Status: canonical product-design source of truth
Owner: Performance Lab product UI
Last reviewed: 2026-09-02

This directory specializes `repo-template-sw`'s `product-ui` profile for Performance Lab. It owns the durable UX and brand/design contracts. Executable frontend components become the implementation source of truth once they exist, but they must remain compatible with these contracts.

## Product question

Performance Lab exists to answer:

> For this use case on this device, which available model + quantization + configuration gives me the best evidence-backed trade-off, and why?

The product is an evaluation and decision-support tool. It does not own model loading or the serving-runtime lifecycle unless a future explicit runtime contract deliberately transfers that responsibility.

## Task hierarchy

The product has two execution journeys and several inspection journeys.

Primary decision journey:

```text
Choose goal (use case + device)
  -> confirm/select model candidates
  -> choose optimization depth
  -> review scope, estimate and contextual benchmark detail
  -> run campaign
  -> establish compatibility + decision policy
  -> choose best-fit model + quantization + configuration from explainable evidence
```

The setup wizard contains four user decisions only: **Goal -> Models -> Optimization -> Review**. Campaign and Results are lifecycle/outcome states after setup; benchmark plan, evaluator identity, plan digest and provenance do not become standalone mandatory steps merely because the backend owns them.

Direct/manual journey:

```text
Choose/connect target
  -> discover/select one model candidate
  -> choose benchmark/scenario
  -> configure one frozen test
  -> run
  -> inspect immutable Run Detail
```

Evidence inspection journeys:

```text
Library -> Benchmarks -> Benchmark Detail -> test case
Runs -> Run Detail -> Samples -> Sample Evidence Detail
Campaign Results -> benchmark case -> Case Comparison Across Candidates
```

## Information architecture

Primary navigation stays focused on user outcomes:

1. **Overview** — the next decision first, then what has been tested and recent/relevant evidence.
2. **Find best setup** — use-case/device-first automatic model/configuration decision journey.
3. **Test a model** — manual evaluation of one served model candidate and one frozen configuration.
4. **Runs** — immutable run history and sample-level evidence drill-down.
5. **Compare** — compatibility-first comparison of evidence.

Technical objects remain reachable but do not compete with the primary task model.

**Library** contains:

- **Models** — discovered model candidates and evidence-relevant identity; quantizations are distinct candidates.
- **Benchmarks** — benchmark definitions, test cases, datasets and evaluator composition.
- **Datasets** — dataset definitions and versioned snapshots.
- **Evaluators** — evaluator definitions, scoring semantics and evidence requirements.
- **Evidence** — retained evidence/provenance audit surface.
- **Baselines** and **Regression policies**.

**Settings** contains only configuration that Performance Lab owns:

- **Model connections**
- **Devices / targets**
- **Appearance** — Light is the canonical default; Dark is optional; System follows the operating system. The preference is browser-local and does not change benchmark/runtime semantics.
- **Evidence retention**
- **Accessibility**
- **Advanced**

Do not place Models, Datasets, Evaluators or Evidence at the same visual priority as Find best setup, Test a model, Runs or Compare.

## Core UX invariants

### Evidence and comparison

- Quality, runtime performance and resources remain separate dimensions.
- Unknown, unavailable, not-evaluated and not-comparable evidence are first-class states and never render as zero.
- Compatibility is established before deltas, rankings, regression verdicts or best-fit recommendations.
- A universal opaque model score is forbidden.
- Recommendation logic is explicit and versioned; the frontend does not invent a winner or post-hoc trade-off explanation.

### Model identity and runtime ownership

- A model family name alone is not a candidate identity.
- Model artifact + quantization are distinct candidates; two quantizations of the same base model appear as separate candidates.
- Quantization is not a configuration-search sweep parameter.
- Request-level parameters may be searched only when the adapter/runtime declares support.
- Runtime/model-load parameters may be searched only when the serving runtime exposes an explicit mutable configuration lifecycle.
- The browser never calls inference runtimes directly; discovery is backend-owned.
- `Not comparable` is never a model status. Comparability belongs to evidence.

### Run and campaign identity

- A **Run** is one immutable evidence unit for one model candidate and one frozen configuration.
- Run Detail never mixes multiple models/configurations.
- A **Campaign** groups immutable runs and exposes bounded progress/failure/cancellation; it does not replace run identity.
- Cross-candidate sample inspection happens in a dedicated Case Comparison surface, not inside a single Run Detail.

### Benchmark inspection

Benchmark definition and benchmark execution results are different contexts.

`Benchmark Detail` answers:

- what does this benchmark measure?
- what datasets/snapshots does it use?
- what evaluators and scoring rules does it use?
- which individual test cases compose it?
- for a selected test case, what prompt/input, expected output and evaluation rules apply?

A benchmark-definition page does **not** show a model/run score unless the user deliberately enters a results context.

Evaluator weights shown in a benchmark belong to that suite/decision context; evaluators do not have one universal global weight.

### Sample evidence

Every aggregate result must be traceable, when retained evidence permits it, to the benchmark cases that produced it.

`Run Detail -> Samples -> Sample Evidence Detail` exposes, when available:

- sample + benchmark identity;
- model + quantization + frozen configuration;
- prompt/input/context;
- expected output/gold label;
- actual response;
- typed execution outcome;
- evaluator score breakdown;
- evaluator-owned rationale/rule evidence;
- latency/token provenance;
- expected-vs-actual diff when meaningful.

The frontend never invents a reason for a score. If the evaluator does not provide a rationale, show `Evaluation explanation unavailable`.

### Evidence retention and privacy

The default mode remains **aggregate-safe**.

- Prompt/output content is not assumed to be retained.
- When content is absent because of retention policy, show `Content not retained`; do not render an empty prompt/output panel as if data existed.
- **Evidence-rich** mode may retain prompt/output explicitly for debugging and must communicate sensitivity/retention consequences.
- Credentials and authorization material are never evidence.
- Dataset snapshot/evidence retention must not silently destroy information required to interpret a retained run.

## Surface-specific rules

### Overview

Primary CTA: **Find best setup**. Secondary CTA: **Test a model**.

The default reading order is decision-first: explain the goal/device decision Performance Lab can answer, expose the primary CTA, then show recent evaluations, then the quieter tested-model evidence inventory. Show trustworthy dimension summaries with enough workload/device context to interpret them. Do not show an unsupported cross-cohort winner, universal overall score or fake zeroes.

### Find best setup

Canonical setup flow:

```text
Goal
  use case + device
-> Models
  eligible candidates selected by default; user may narrow
-> Optimization
  Quick / Standard / Thorough when evidence-backed ranges exist
  custom/fixed/parameter detail progressively disclosed
-> Review
  candidates + configurations + immutable run count + estimate
  benchmark/evaluator detail contextual
  fingerprints/provenance/plan digest advanced
```

Then:

```text
Campaign
  progress-first lifecycle
-> Results
  compatibility + decision policy
  -> recommended setup
  -> backend-owned rationale
  -> separate Quality / Performance / Resources comparison
  -> exact-case evidence drill-down
```

The use case owns benchmark/dataset/evaluator relevance. Device selection scopes candidate discovery. Eligible candidates use an all-selected default when the backend already scoped them safely. **Standard** is the normal preferred optimization default when bounded ranges are available; the authored fixed configuration is the safe fallback when the runtime provides no evidence-backed sweep range. The browser never invents ranges to make the mockup richer.

### Test a model

Canonical flow:

```text
Choose/connect target
-> Discover/select model
-> Choose scenario/benchmark
-> Configure test
-> Review frozen configuration
-> Live Run
-> Run Detail
```

Connection details and advanced parameters use progressive disclosure.

### Campaign

Running campaigns are progress-first: overall progress precedes per-candidate rows. Leaving the page does not imply cancellation when the server persists the campaign; cancellation remains explicit. Terminal campaigns place Results before completed progress and candidate Runs.

### Campaign Results

Results answer the decision, not a leaderboard question. The reading order is:

```text
compatibility + explicit decision policy
-> recommended model + quantization + frozen configuration
-> why this setup (backend result rationale only)
-> candidate comparison with Quality / Performance / Resources separate
-> benchmark-case drill-down
```

Do not add trophies, medals, opaque overall scores or frontend-authored claims such as “best balance” unless an explicit backend decision policy/evidence contract provides that exact meaning.

### Models

This is an inventory/inspection surface, not a model manager owned by Performance Lab. Show candidate identity, quantization, endpoint/runtime source, reported capabilities and trustworthy availability/residency state. Do not imply that Performance Lab loads/unloads the model unless that ownership is explicitly adopted later.

### Datasets

Differentiate catalog definitions from immutable snapshots referenced by evidence. Sample preview is conditional on source/license/privacy policy.

### Evaluators

Show evaluator version, type, metric/output schema, evidence requirements, determinism/explanation capability and benchmark usages. Context-specific weights appear in the owning benchmark/suite, not as a global evaluator property.

### Evidence

This is an audit/provenance surface. It obeys aggregate-safe/evidence-rich retention semantics and never reveals secrets. Every artifact should link to the owning run/campaign, benchmark/sample and evaluator/source provenance where available.

### Settings

Only expose product-owned configuration. Appearance is a browser-local UI preference: Light is the canonical reference, Dark remains optional and System follows the OS. Theme choice must not alter benchmark semantics, evidence truthfulness or runtime ownership. Do not invent email notifications, telemetry controls, runtime lifecycle toggles or other settings merely because a mockup has space for them.

## Progressive disclosure

Default hierarchy:

```text
essential
  -> contextual
  -> advanced
  -> expert / diagnostics
```

Essential: current decision, model/quantization identity, use case + device, main evidence, typed status and next action.

Contextual: accumulated `Your setup` summary, candidate count, configuration summary, dataset/evaluator identity, compatibility reason and sample result summary.

Advanced: generation/search parameters, reported runtime configuration, benchmark protocol detail and retention/provenance detail.

Expert/diagnostics: plan/config fingerprints, raw evidence payloads, runtime/adapter diagnostics and retained safe logs.

On desktop-standard/wide Find best setup, a compact contextual `Your setup` pane may stay visible beside the active task. At desktop-compact it must move above/below the primary work rather than squeezing the decision surface.

## Desktop layout

Supported layouts remain desktop-only:

- **compact 1024-1279px** — preserve the primary task; condense secondary navigation and move optional contextual panes out of side-by-side mode when they would squeeze evidence.
- **standard 1280-1599px** — persistent task navigation, main work area and optional contextual detail pane.
- **wide >=1600px** — use extra width for useful side-by-side evidence inspection, not decorative density.

## Data visualization

Charts and graphics exist to answer a concrete question, not to decorate the dashboard.

- Unknown/unavailable/not-comparable are never plotted as zero.
- Quality, performance and resources retain distinct semantic encodings.
- Show confidence/uncertainty when available and decision-relevant.
- Prefer tables when exact candidate comparison is the task.
- Do not use trophy/medal gamification for scientific evidence.
- Recommendation emphasis never substitutes for explicit compatibility/decision-policy evidence.

## Reference views and final visual targets

Current SVG references remain conceptual guidance for already-defined flows:

- [`reference/ux-reference-board.svg`](reference/ux-reference-board.svg)
- [`reference/model-connection.svg`](reference/model-connection.svg)
- [`reference/find-best-setup.svg`](reference/find-best-setup.svg)

They are not pixel-regression goldens and may lag the consolidated surface contracts above. In particular, the four-stage Find best setup hierarchy in `ux-contract.json` and the executable frontend take precedence over older seven-stage conceptual references.

The approved UX-aligned desktop UI targets live under:

```text
design/reference/visual-targets/
```

Generated/hand-authored design targets express approved design intent. They must **not** be used directly as pixel-diff CI truth. Accepted browser screenshots from the real implementation live separately under:

```text
design/reference/visual-goldens/desktop-standard/
```

The golden manifest records the exact source/build/browser identity from which each baseline was reviewed. Only a limited set of stable, high-value, target-backed surfaces belongs there; visual regression does not replace semantic journeys, accessibility checks or representative-user review.

Canonical standard desktop visual-target and implementation-golden viewport: **1536 x 960**.

## Contracts

- [`ux-contract.json`](ux-contract.json) — canonical IA, surface semantics, hierarchy, states, accessibility, journeys and evidence expectations.
- [`brand-kit.json`](brand-kit.json) — canonical visual identity, semantic tokens, typography, spacing, radius, motion and microcopy.

## Validation principle

A screenshot does not prove UX correctness. Before accepting a final UI target or implementation, validate at the relevant layer:

1. user task / navigation / hierarchy;
2. surface-specific semantic rules;
3. progressive disclosure and recovery states;
4. accessibility and desktop adaptation;
5. design-system/brand consistency;
6. critical-journey E2E when executable;
7. visual review/regression only after the earlier layers are correct.
