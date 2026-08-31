# Architecture

Status: active
Document type: architecture
Owner: repository
Canonical scope: architecture.repository
Read when: changing dependency boundaries, adding a domain/application/adapter/storage boundary, or deciding where new behavior belongs
Last reviewed: 2026-08-31

## 1. Architectural objective

Performance Lab is an evaluation control plane around externally served AI models. It owns **evaluation orchestration, measurement, scoring, evidence, comparison and regression**. It does not own model loading/serving-runtime lifecycle in the core product.

The same engine can evaluate a local llama.cpp-compatible service, LM Studio, Ollama, a device-exposed endpoint, Local LLM Server or a remote API when an adapter can normalize the required request/response behavior.

Primary product question:

> For this workload and device, which tested model/configuration provides the best evidence-backed trade-off, and why?

## 2. System context

```text
Browser UI / CLI / CI
        |
        v
application / orchestration
        |
        v
canonical domain + evaluation semantics
   /        |          |          \
adapters  datasets   telemetry   persistence
   |                                |
served model/runtime             run evidence
```

Inference and optional instrumentation are distinct channels:

```text
Performance Lab ---- inference requests ----> endpoint/runtime
      |
      +---- optional telemetry -------------> collector/device API
```

A black-box evaluation remains valid when telemetry is unavailable. Resource/device claims require the corresponding evidence channel.

## 3. Dependency and ownership rules

- `domain/` owns immutable identities, execution/evidence contracts, compatibility types and shared error semantics.
- `engine/` owns evaluation orchestration and run execution against interfaces.
- `adapters/` owns provider/transport-specific inference behavior; provider differences do not leak into orchestration.
- `datasets/` owns source/snapshot/loading/sampling semantics.
- `evaluation/` owns parsers/evaluators and score semantics.
- `performance/` owns runtime measurement protocols/statistics.
- `telemetry/` owns metric collection/provenance, not benchmark pass/fail policy.
- `storage/` owns run persistence, immutable completed evidence, bounded Campaign lifecycle persistence, import/export and migrations.
- `regression/` and comparison owners consume canonical fingerprints/metrics; persistence/UI do not redefine comparability.
- `application/` exposes task-oriented read models, preflight/frozen configuration, bounded server-owned run/campaign jobs and versioned decision policy to presentation layers.
- `ui_api.py` and `ui_server.py` are transport/composition boundaries, not domain-policy owners.
- `frontend/` consumes versioned application/API contracts and semantic design contracts; it never reads SQLite directly or reimplements canonical benchmark/comparability truth.
- CLI/CI/automation are presentation/automation entry points over the same canonical engine/evidence semantics.

Dependency direction is therefore:

```text
presentation / transport
          |
          v
application / orchestration
          |
          v
canonical domain contracts
     /       |        \
adapters  evaluators  stores/collectors
     |                   |
 external IO          persistence / instrumentation
```

## 4. Current package shape

The implementation is intentionally capability-oriented rather than a mirror of backend technology:

```text
src/performance_lab/
  domain/          immutable benchmark/evidence contracts
  engine/          run orchestration
  adapters/        inference-provider boundaries
  datasets/        dataset registry/loading/snapshots
  evaluation/      parsers/evaluators and score semantics
  performance/     latency/throughput/load/statistics
  telemetry/       collectors and provenance
  storage/         SQLite/artifact persistence
  regression/      baseline/policy/verdict logic
  integrations/    external product/framework integration
  plugins/         extension discovery/contracts
  application/     UI read/preflight/run/campaign application layer
  cli.py            command-line surface
  ci.py             CI regression surface
  automation.py     automation-facing helpers
  ui_api.py         versioned local HTTP API
  ui_server.py      loopback composition root
frontend/           React/TypeScript browser product
```

Create a new module/interface only when it owns an autonomous domain responsibility, external/platform boundary, reusable multi-consumer behavior or distinct test/release boundary. Do not create empty architectural layers speculatively.

## 5. Inference adapter contract

Adapters normalize transport/provider behavior conceptually as:

```text
probe(target) -> EndpointCapabilities
invoke(request, cancellation) -> InferenceResult
stream(request, cancellation) -> stream<InferenceEvent>
```

A normalized request contains task/messages input, requested generation configuration, optional response-format intent, timeout/deadline and correlation identity.

A normalized result/event exposes only facts actually known: output, finish reason, safe model/request identity, trustworthy token counts, normalized errors, lab-boundary timestamps and separately namespaced endpoint-reported timing.

### Effective configuration

Requested parameters are not evidence that they were honored. Each parameter must resolve to one of:

1. supported with effective value known;
2. unsupported and rejected;
3. unsupported but explicitly ignored under an approved compatibility policy;
4. effective value unknown.

Silent parameter loss is invalid benchmark evidence.

## 6. Execution fingerprint and compatibility

`ExecutionFingerprint` is the reproducibility identity. It covers the material execution inputs needed to distinguish evidence, including:

- target/adapter/safe endpoint identity;
- model identity, revision/artifact/quantization when known;
- runtime identity/version when known;
- effective generation/load configuration;
- prompt/template identity;
- dataset snapshot/split/sample policy;
- evaluator versions;
- benchmark protocol/warmup/repetitions/concurrency;
- device/environment identity when known;
- telemetry collectors/versions.

Serialization is canonical before hashing. Unknown values remain explicit rather than inferred.

Compatibility is **dimension-specific**, not one global boolean. Examples:

- same quality protocol on different hardware may permit quality comparison while preventing hardware-neutral latency regression;
- different dataset snapshots invalidate dataset-derived quality deltas even if runtime evidence remains comparable under an equivalent load profile;
- different quantization is an explicit configuration comparison, not a same-configuration regression.

Comparison always evaluates identity/compatibility before deltas.

## 7. Run and sample lifecycle

Canonical run semantics distinguish validation, execution, interruption and immutable publication. Conceptually:

```text
DRAFT -> VALIDATING -> READY -> RUNNING
                              |-> CANCELLING -> CANCELLED
                              |-> FAILED
                              `-> AGGREGATING -> COMPLETED
```

Completed evidence is immutable. Working/checkpoint state may exist, but it cannot be mistaken for completed evidence and publication must be atomic enough to preserve that invariant.

Per-sample outcomes remain typed:

```text
PENDING -> RUNNING -> SUCCESS
                   |-> MODEL_ERROR
                   |-> ADAPTER_ERROR
                   |-> TIMEOUT
                   |-> CANCELLED
                   `-> EVALUATOR_ERROR
```

Evaluator infrastructure failure is not model failure; transport timeout is not an incorrect answer. Aggregation preserves those distinctions.

The UI application layer additionally owns bounded server-side Run and Campaign jobs, progress, reconnect/cancellation state and restart/interruption recovery without changing the immutable run-evidence contract. A Campaign groups immutable Runs; it does not become an alternate Run identity or portable replacement for Run evidence.

## 8. Reproducibility rules

### Dataset and configuration freeze

Before measured execution, freeze dataset source/split/filter/deterministic sample selection into a snapshot identity and freeze endpoint profile references, effective generation settings, suite/evaluator versions and benchmark protocol. A run must not observe mutable configuration or dataset content underneath it.

### Randomness and time

Use deterministic seeds where supported and meaningful; record when the backend cannot provide deterministic seeding. Repeated stochastic evaluation is an explicit benchmark policy. Use monotonic clocks for elapsed measurements; wall-clock timestamps are audit/order metadata only.

## 9. Runtime measurement protocols

Performance Lab measures what it owns at the client boundary:

```text
request start
  -> first observable streamed output = lab TTFT
  -> final output
  -> response completion = total latency
```

Endpoint-provided prefill/decode/load timing remains `endpoint_reported` and is never conflated with lab-observed timing.

Tokens/sec requires trustworthy token counts: prefer endpoint counts when reliable; use a configured tokenizer only when tokenizer/model compatibility is known; otherwise mark token throughput unavailable rather than fabricate it.

Cold/warm/load state is explicit:

- `UNCONTROLLED_INITIAL` — first observed request, cold state not proven;
- `CONTROLLED_COLD` — adapter/external hook proves the cold precondition;
- `WARMUP` — excluded from measured aggregates;
- `WARM_MEASURED` — post-warmup measured samples;
- `LOAD_TEST` — concurrent/throughput profile.

A third-party runtime that cannot be forced cold must never be reported as controlled cold.

## 10. Telemetry architecture

Telemetry has three evidence levels:

- **Level 0 — endpoint-only:** client-observed latency/TTFT, success/failure/timeout and endpoint token usage when present.
- **Level 1 — lab-host:** system/process metrics from the machine running Performance Lab; attribution limitations must be explicit.
- **Level 2 — instrumented inference host/device:** cooperating runtime/device identity, residency, memory, CPU/GPU, thermal, energy and runtime-native timing where supported.

Every telemetry sample carries time basis, collector identity/version, metric/unit, scope, provenance and optional run/request correlation. Precise remote request-level correlation requires an adequate clock relationship; otherwise telemetry is correlated to a run window.

Telemetry failure is normally independent from inference unless the suite explicitly requires the metric.

## 11. Dataset and evaluator pipeline

```text
Dataset sample
  -> input renderer
  -> inference request
  -> response parser
  -> evaluator(s)
  -> typed score(s)
```

Dataset identity and evaluator identity are independent because changing normalization/scoring semantics changes results even when raw dataset content is unchanged.

External benchmark frameworks integrate through an explicit bridge:

```text
Performance Lab config -> framework config/execution -> normalized imported evidence
```

Imported evidence preserves framework/task/version/config provenance and is never presented as native evaluator output. Native evaluation remains necessary for custom workloads, runtime/resource evidence and regression orchestration.

## 12. Persistence and privacy

Current persistence uses a queryable run store plus portable evidence artifacts. Technology remains replaceable as long as migration, immutability and atomic-publication contracts hold.

Queryable metadata includes run headers/fingerprints, aggregate quality/runtime/resource evidence, baselines and comparison/regression state. Campaign lifecycle is persisted separately as bounded orchestration state that references immutable Run IDs; terminal Campaign snapshots are immutable, while Run records remain the authoritative benchmark evidence. Larger artifacts may include per-sample evidence, telemetry series and imported benchmark output.

Privacy modes are conceptually:

- **aggregate-safe (default):** metrics, hashes/IDs and typed failures; prompt/output content is not retained unless the evaluator contract requires it;
- **evidence-rich (explicit):** debugging inputs/outputs may be retained and must be treated as potentially sensitive with retention/delete behavior.

Credentials, authorization headers and signed secrets are never portable run evidence.

## 13. Comparison and regression

Canonical comparison order:

1. load immutable fingerprints/evidence;
2. compute identity differences;
3. determine comparability per metric dimension;
4. align tasks/samples where applicable;
5. calculate only valid deltas/statistics;
6. apply versioned regression thresholds/policies;
7. emit typed result and limitations.

`PASS`, `FAIL`, `NOT_COMPARABLE` and `NOT_EVALUATED` remain distinct. Missing evidence cannot silently pass and incompatible deltas are absent, not cosmetically disabled into apparent validity.

Campaign recommendation follows the same compatibility-first rule. The current `strict-quality-dominance@1.0.0` application policy recommends only a unique candidate that is no worse on every comparable quality metric and strictly better on at least one metric against every alternative. It introduces no metric weights, cross-dimension normalization or hidden tie-break. Runtime and resource evidence remain separate read-model dimensions rather than inputs to an opaque universal score.

## 14. Local UI application boundary

`UIQueryService` and related application models translate canonical run/evidence semantics into task-oriented browser read models. Preflight resolves/validates a user selection and produces a frozen execution preview before launch. Campaign planning similarly resolves use-case, candidate, configuration-search and benchmark semantics in Python and produces a deterministic frozen plan digest.

`RunJobManager` owns bounded single-Run job state, progress, cancellation/reconnect and interruption recovery. `CampaignJobManager` owns bounded multi-Run Campaign orchestration over that same native runner. A shared `EvaluationCapacity` prevents manual Runs and Campaigns from concurrently claiming the same local evaluation slot. Both managers release ownership across success, failure, cancellation and shutdown/restart paths.

Campaign launch never trusts the browser preview as executable truth: the server rebuilds the requested plan from current backend-owned semantics and requires its digest to match the reviewed digest before capacity is acquired. Each Campaign matrix entry then receives one explicit Run ID and executes through the canonical runner. `SQLiteCampaignStore` retains lifecycle/reconnect state separately from `SQLiteRunStore`; completed Run truth remains immutable Run evidence.

Campaign result projection joins persisted Campaign entries to completed Runs, evaluates dimension-specific compatibility and applies an explicit versioned decision policy. The frontend only renders that projection; it does not rank candidates, assign benchmark relevance or combine quality/runtime/resource metrics itself.

`ui_server.py` composes the local graph from one versioned starter execution config and binds the API to `127.0.0.1` by default. During development Vite proxies `/api` to this loopback service. Built static-product ownership, build identity/artifact promotion and final smoke/cleanup remain release concerns rather than campaign-lifecycle ownership.

Frontend information architecture and interaction rules belong in `design/ux-contract.json`; brand/component/motion semantics belong in `design/brand-kit.json` and `frontend/src/design/`. Architecture does not duplicate those UX contracts.

## 15. Failure, resources and security

Prefer typed `unknown`, `unavailable`, `partial` and `not-comparable` states over invented defaults. Examples: no stream -> TTFT unavailable; no trustworthy token count -> token throughput unavailable; collector permission failure -> typed telemetry unavailable; unknown model revision stays unknown.

Every significant process/listener/job/queue/cache/temp file/workspace has an owner, bounded lifetime/cardinality, timeout/cancellation behavior and cleanup across success, failure, timeout, cancellation, interrupt and partial initialization.

Trust boundaries include endpoint credentials, imported datasets, prompts/outputs, SQLite/evidence bundles, device telemetry and loopback browser/API traffic. No secret persistence, content logging or silent cloud fallback is introduced outside an explicit reviewed contract. See `SECURITY.md` for repository-wide policy.

## 16. Durable extension decisions

Keep domain policy out of transport/UI/persistence adapters unless that layer genuinely owns it. Search for the existing owner before adding a constant/status/configuration/lifecycle rule.

Material durable ownership changes belong here or in an ADR. Current accepted product ownership is documented in `docs/adr/0004-performance-lab-owns-evaluation-product.md`: Performance Lab owns evaluation/product history; Local LLM Server remains the serving/runtime control plane.

Open implementation work does **not** belong in architecture. Current execution state and remaining dependencies are routed through `docs/current-state.md` and the active bounded workstream only.
