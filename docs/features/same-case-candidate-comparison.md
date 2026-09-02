# Same-case candidate comparison

Status: active
Document type: feature
Owner: product-evidence
Canonical scope: feature.same-case-candidate-comparison
Read when: changing Campaign case discovery, same-case compatibility or cross-candidate sample evidence semantics
Last reviewed: 2026-08-31

## Purpose

Same-case comparison answers a narrower question than aggregate Campaign Results: for one exact benchmark case, what evidence did each Campaign candidate produce, and is that evidence valid to place side by side?

The feature starts from a persisted Campaign and reuses immutable Run/sample identities. It does not create a second benchmark, comparison or retention owner.

## Contract

- Campaign Results lists retained `(task_id, sample_id)` case identities from candidate Runs.
- Opening one case keeps the Campaign, task and sample identity explicit in the route.
- Python projects candidate model identity, quantization when known, frozen configuration digest, immutable Run id and exact sample attempt evidence.
- Capability comparability is established through the canonical fingerprint compatibility rules before candidate evidence is treated as comparable.
- Dataset snapshot, evaluator version, benchmark protocol and prompt-template mismatches remain explicit reasons for non-comparability.
- If an exact Run contains zero matching sample attempts, evidence is unavailable for that candidate.
- If more than one retained attempt exists for the task/sample identity, Performance Lab does not choose silently; the candidate remains unavailable until an exact attempt is selected by a future explicit contract.
- Retained response content is displayed only when the evidence retention contract supplies it. `not_retained` and `unavailable` remain distinct visible states.
- Evaluator score identity and rule provenance remain attached to the immutable sample attempt.
- Sample measurements are shown only when the sample evidence projection supplies trustworthy scoped measurements.
- The case surface never invents a winner, aggregate score or cross-case delta.

## API read paths

- `GET /api/v1/campaigns/{campaign_id}/cases`
- `GET /api/v1/campaigns/{campaign_id}/cases/{task_id}/{sample_id}`

The first path discovers retained case identities. The second returns the Python-owned same-case projection with compatibility and candidate-level evidence.

## UX states

- **Comparable**: every Campaign candidate retains the exact case and all candidates are capability-compatible with the reference Run.
- **Partially comparable**: at least two candidates are comparable; missing or incompatible candidates stay visible but are excluded from conclusions.
- **Not comparable**: fewer than two compatible candidate Runs retain the exact case.

The first available retained Run is a compatibility reference only. It is not a benchmark baseline, winner or ranking preference.
