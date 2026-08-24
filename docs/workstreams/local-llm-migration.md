# Local LLM Server evaluation migration

Status: active
Owner: Performance Lab / Local LLM Server integration
Canonical scope: migration.lls-evaluation
Last reviewed: 2026-08-24

## Goal

Move overlapping benchmark/evaluation responsibilities from Local LLM Server to Performance Lab without breaking required workflows, losing retained evidence or moving model-serving ownership into Performance Lab.

Performance Lab is the evaluation product. Local LLM Server remains an inference/runtime provider where that role is useful.

## Durable owners

- [`../adr/0004-performance-lab-owns-evaluation-product.md`](../adr/0004-performance-lab-owns-evaluation-product.md) — long-term ownership decision;
- [`../local-llm-server-integration.md`](../local-llm-server-integration.md) — integration boundary;
- [`../architecture.md`](../architecture.md) — Performance Lab ownership/dependency rules;
- [`../../design/ux-contract.json`](../../design/ux-contract.json) — shipped evaluation task model.

## Remaining gates

| Task | State | Depends on | Acceptance |
| --- | --- | --- | --- |
| MIG-001 parity map | READY | integrated Performance Lab product | classify every LLS evaluation workflow as migrate, retain-operational or intentionally drop; identify data/history/consumer dependencies |
| MIG-002 replacement + deprecation | PLANNED | MIG-001 + representative real-runtime evidence | required migrated workflows are usable in Performance Lab; users/consumers have a documented replacement path; retained history policy is explicit |
| MIG-003 remove redundant evaluation paths | PLANNED | MIG-002 | no required consumer depends on removed LLS evaluation behavior; cross-repo E2E and real-runtime smoke are green; serving/runtime responsibilities remain intact |

## Migration rules

- Do not delete before parity/consumer evidence exists.
- Do not copy serving/runtime ownership into Performance Lab to make migration easier.
- Preserve or explicitly retire durable evidence/history; never silently orphan it.
- Keep compatibility adapters explicit and bounded if temporary coexistence is required.
- Deprecation messaging must point users to the supported Performance Lab path before removal.
- Cross-repository claims require evidence from both sides of the integration, not only unit tests in Performance Lab.

## Completion gate

Complete when redundant LLS evaluation behavior is either migrated, deliberately retained for a documented non-overlapping reason, or intentionally removed with consumer/history evidence; the final integration smoke is green on a real runtime path.

After completion, transfer durable migration outcomes to the integration/ADR docs, update `current-state.md`, and delete this workstream by default.
