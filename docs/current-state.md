# Current repository state

Status: active
Document type: current-state
Owner: repository
Canonical scope: state.repository
Last reviewed: 2026-08-17

This is the short operational ledger for Performance Lab. Durable behavior belongs in architecture/feature/ADR docs; active implementation detail belongs in bounded workstreams.

## Current phase

The benchmark/evidence core is integrated on `dev`; the next product phase is **UI productization plus representative real-device evidence**.

Performance Lab can already execute reproducible endpoint evaluations, capture quality/runtime/optional resource evidence, freeze execution identity, persist immutable runs, export `.plab.zip`, compare compatible evidence and enforce regression policies through CLI/CI. Deterministic product E2E is integrated.

The major product gap is no longer the engine: it is the local visual product that makes run history, tested models, evidence and comparison usable without CLI-only workflows.

## Ownership direction

ADR 0004 is accepted:

- **Performance Lab** is the long-term owner of benchmark/evaluation, run history, comparison, baselines/regression and their UX.
- **Local LLM Server** remains the serving/runtime control plane: inference, residency, scheduling/resources, identity and dynamic status.
- Local LLM Server's current evaluation surface is transitional and is removed only after Performance Lab replacement parity, migration policy and cross-product evidence are complete.

## Integrated baseline

The current `dev` line includes:

- versioned immutable domain/fingerprint contracts;
- OpenAI-compatible endpoint adapter and capability probing;
- bundled/custom datasets and workload packs;
- deterministic evaluators plus optional rubric judge;
- latency/TTFT/throughput, repeatability and bounded load protocols;
- host/runtime telemetry with explicit provenance;
- Local LLM Server `/v1/runtime/identity` and `/status` integration;
- immutable SQLite run evidence, portable bundles and retention;
- compatible comparison, explicit baselines and versioned regression policies;
- CLI `probe`, `inspect`, `run`, `regress`, `regress-ci`;
- constrained Python 3.12/3.13 CI dependencies;
- deterministic Product E2E across CLI + HTTP + persistence + regression.

Passing deterministic CI is implementation evidence, not representative model/device benchmark evidence.

## Active work

| Workstream | State | Next gate |
| --- | --- | --- |
| [UI productization](workstreams/ui-productization.md) | ACTIVE | `UIF-001` engineering/frontend foundation |
| Representative model/device evidence | READY | first real Local LLM Server smoke + retained run bundle |

Completed E2E hardening is documented in [`e2e-product-acceptance.md`](e2e-product-acceptance.md); it does not replace real-runtime or human acceptance.

## Immediate next block

1. **UIF-001** — establish the pinned frontend toolchain and extend the repo-template operating command contract without weakening the existing Python core.
2. **UIA-001 + UIK-001 in parallel** — versioned local application/read API and semantic design-system primitives.
3. Build **Overview/Tested Models** and **Run Detail** first because they expose existing stored evidence without requiring new execution semantics.
4. Then build **New Evaluation**, **Live Run/cancellation**, and **Compare/regression**.
5. In parallel, execute the first real Local LLM Server smoke/evidence run so UI assumptions are checked against real identity/telemetry rather than fixtures only.
6. Start Local LLM Server evaluation deprecation only after Performance Lab UI parity is product-tested.

## Integration lines

- `dev` is the canonical implementation/integration line.
- `main` is stable/release-oriented and is promoted deliberately after evidence.
- Feature branches start from current green `dev`, remain focused and merge through CI-green PRs.

## Evidence still required

Before broad product/release claims:

- real resident-model starter/workload run with retained fingerprint and bundle;
- repeated/load evidence on controlled hardware;
- real Local LLM Server identity + telemetry usefulness check;
- real baseline/candidate regression evidence;
- built UI Playwright journeys plus cancellation/recovery/zero-residue evidence;
- human/manual acceptance of the shipped local product surface.
