# General diagnostic starter suite

Status: active
Document type: benchmark-protocol
Owner: DAT/EVAL
Last reviewed: 2026-08-15

The bundled `general-diagnostic-starter` suite is a **small diagnostic sample for local-device iteration**. It is not a universal model leaderboard and its aggregate result must not be presented as a general intelligence score.

## Purpose

Use the starter suite to detect obvious capability regressions, compare configurations during local iteration, and decide which model/runtime combination deserves deeper workload-specific testing.

All current samples are authored directly in this repository. Every bundled dataset has a version, exact record-set SHA-256 digest, fixed test split, and deterministic selection policy. Changing sample content requires a suite-version change.

## Current categories

| Task | Evaluator | Intent |
| --- | --- | --- |
| instruction following | normalized exact match | strict closed-form response |
| factual QA | normalized exact match | basic stable facts |
| reasoning | normalized exact match | simple logical reasoning |
| basic mathematics | numeric tolerance | arithmetic/numeric output |
| classification | label accuracy | clear sentiment/intent labels |
| structured JSON adherence | JSON Schema | syntax/schema compliance |
| structured JSON fields | field extraction | expected field-value correctness |

The authored source contains 20 unique records. Structured JSON records are evaluated twice because schema adherence and field correctness are separate failure modes.

## Generation and interpretation

Version 1 uses temperature `0`, seed `7` where supported, and maximum output tokens `64`. Capability evidence must still record when seed or structured-output controls are unsupported or unknown.

Do not collapse these task results into one authoritative model score. Prefer category-level results paired with runtime/resource evidence.

## Coding exclusion

Executable coding tasks are intentionally excluded until Performance Lab has a hardened execution sandbox. Adding generated-code execution must be a separate safety boundary rather than a generic evaluator side effect.
