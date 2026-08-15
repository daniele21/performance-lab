# Workload packs

Status: active
Document type: focused-specification
Owner: DAT-004
Last reviewed: 2026-08-15

Workload packs are versioned dataset/suite/evaluator bundles for practical scenarios. They live in the dataset/evaluation layer and do not add scenario-specific branches to the generic execution engine.

## Contract

Each pack exposes:

- stable `pack_id` and version;
- human-readable title/description;
- task-family metadata;
- a normal `EvaluationSuite`;
- frozen `MaterializedDataset` snapshots;
- evaluator implementations referenced by normal evaluator IDs/versions.

The engine consumes the resulting suite/datasets exactly as it consumes the general starter suite or a custom imported dataset.

## First pack: structured document extraction

ID: `structured-document-extraction`

The first authored diagnostic pack contains six short invoice-like documents and evaluates two objective dimensions:

1. JSON Schema adherence;
2. deterministic field correctness.

The target schema is deliberately compact: `document_id`, `vendor`, `total`, `currency`, `due_date`.

The pack uses deterministic evaluators because objective ground truth exists. The optional LLM judge is not part of this pack.

## Interpretation

A workload-pack score is scenario evidence, not a universal model ranking. Comparisons remain subject to the same dataset/evaluator/fingerprint compatibility rules as every other Performance Lab run.

Future packs should be added only when they represent a concrete reusable scenario. Candidate families include meeting intelligence, PII/entity extraction and domain classification.
