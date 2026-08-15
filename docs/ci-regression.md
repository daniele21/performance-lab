# CI regression gate

Status: active
Document type: focused-specification
Owner: REG-003
Last reviewed: 2026-08-15

Performance Lab exposes the same compatibility and threshold semantics to CI without inventing stronger hardware evidence than the runner provides.

## Command

```bash
performance-lab regress-ci \
  --store .performance-lab/runs.sqlite3 \
  --baseline-run baseline-2026-08-15 \
  --candidate-run candidate \
  --policy regression-policy.json \
  --artifact performance-lab-regression.json
```

Exit codes remain aligned with CLI-003:

| Code | Meaning |
| --- | --- |
| `0` | `PASS` |
| `1` | `FAIL` |
| `2` | configuration/execution `ERROR` |
| `3` | `NOT_COMPARABLE` |
| `4` | `NOT_EVALUATED` |

The command writes a versioned JSON artifact before returning the gate exit code. When `GITHUB_STEP_SUMMARY` is available it also appends a concise Markdown summary.

## Hardware safety rule

CI runner hardware is considered **uncontrolled by default**. Therefore any regression-policy rule targeting the `resource` dimension is forced to `NOT_COMPARABLE` even if two stored fingerprints happen to contain equal or incomplete hardware values.

Use `--runner-identity-controlled` only when the CI topology guarantees that baseline and candidate resource evidence comes from a controlled comparable runner identity. This flag does not bypass the normal fingerprint compatibility rules; it only allows already-compatible resource rules to retain their policy result.

## Local composite action

The repository includes:

```text
.github/actions/performance-lab-regression/action.yml
```

The caller must set up Python and install Performance Lab before invoking it. Example:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: "3.12"

- run: python -m pip install -e .

- name: Performance regression gate
  id: performance_gate
  uses: ./.github/actions/performance-lab-regression
  with:
    store: .performance-lab/runs.sqlite3
    baseline-run: baseline-2026-08-15
    candidate-run: candidate
    policy: regression-policy.json
    artifact-path: performance-lab-regression.json
    runner-identity-controlled: "false"

- name: Upload regression evidence
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: performance-lab-regression
    path: performance-lab-regression.json
```

Use `if: always()` for the upload because a valid regression `FAIL`, `NOT_COMPARABLE` or `NOT_EVALUATED` intentionally produces a non-zero gate exit code.

## Evidence semantics

The CI artifact contains:

- explicit baseline/candidate run and fingerprint identity;
- regression policy ID/version;
- original comparison and policy evaluation;
- CI-effective rule states;
- whether resource/hardware comparability was trusted;
- per-rule reason strings.

The Markdown summary is presentation only. The JSON artifact and exit code are the automation contract; CI consumers should not parse terminal text or ANSI output.
