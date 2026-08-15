# CLI reference

Status: active
Document type: operational-reference
Owner: CLI
Canonical scope: operations.cli
Read when: running Performance Lab manually, scripting it, or integrating it into CI
Last reviewed: 2026-08-15

The `performance-lab` CLI is the supported developer control plane for endpoint probing, execution, inspection and regression automation.

## Command overview

```text
performance-lab probe
performance-lab inspect
performance-lab run
performance-lab regress
performance-lab regress-ci
```

Prefer `--json` whenever another process consumes command output. Human-readable terminal text is presentation, not a machine contract.

## `probe`

Probe an OpenAI-compatible endpoint and report health, discovered models and capability evidence.

```bash
performance-lab probe \
  --base-url http://127.0.0.1:1235/v1/ \
  --model my-model
```

Options:

| Option | Required | Meaning |
| --- | --- | --- |
| `--base-url` | yes | OpenAI-compatible API root |
| `--model` | no | selected model for probe behavior |
| `--bearer-env` | no | environment variable containing bearer token |
| `--api-key-env` | no | environment variable containing API key |
| `--json` | no | emit normalized JSON only |

`--bearer-env` and `--api-key-env` are mutually exclusive. Secrets are resolved from the named environment variable and are not persisted in the endpoint identity.

Human output includes endpoint health, adapter ID, model list and capability states. Exit code is `0` when healthy and `2` when unhealthy.

## `inspect`

Inspect a serialized `Run` or `ExecutionFingerprint` JSON:

```bash
performance-lab inspect run.json
performance-lab inspect fingerprint.json --json
```

The command detects a Run by the presence of run/fingerprint structure; otherwise it validates the payload as an ExecutionFingerprint. Invalid JSON/schema returns exit code `2`.

A `.plab.zip` is not passed directly to `inspect`. Extract its `run.json` first:

```bash
unzip -p result.plab.zip run.json > /tmp/run.json
performance-lab inspect /tmp/run.json
```

## `run`

Execute the bundled diagnostic suite from a strict versioned JSON config:

```bash
performance-lab run --config run.json
```

Options:

| Option | Required | Meaning |
| --- | --- | --- |
| `--config` | yes | version-1 run configuration JSON |
| `--json` | no | emit compact result-pointer JSON |

Human mode reports progress without emitting prompt/output content. On completion it prints status, fingerprint ID, run store and portable bundle.

`--json` emits, for example with the current `general-diagnostic-starter` v1 suite:

```json
{
  "run_id": "run-...",
  "status": "succeeded",
  "fingerprint_id": "...",
  "store_path": ".performance-lab/runs.sqlite3",
  "bundle_path": ".performance-lab/artifacts/run-....plab.zip",
  "sample_count": 23
}
```

`sample_count` is the number of `SampleExecution` records, not necessarily the number of unique authored source records. In the current starter suite, the 20 unique source records yield 23 executions because the structured dataset is evaluated by two tasks.

Exit code is `0` for a succeeded run, `1` for a terminal non-succeeded run, and `2` for configuration/execution errors handled by the CLI.

Read [`run-config-reference.md`](run-config-reference.md) and [`output-and-evidence-reference.md`](output-and-evidence-reference.md).

## `regress`

Evaluate one explicit baseline/candidate pair against a versioned regression policy:

```bash
performance-lab regress \
  --store .performance-lab/runs.sqlite3 \
  --baseline-run baseline-run-id \
  --candidate-run candidate-run-id \
  --policy regression-policy.json
```

Shared regression arguments:

| Option | Required | Meaning |
| --- | --- | --- |
| `--store` | yes | SQLite evidence store |
| `--baseline-run` | yes | immutable completed baseline run ID |
| `--candidate-run` | yes | immutable completed candidate run ID |
| `--policy` | yes | versioned threshold policy JSON |
| `--baseline-id` | no | optional explicit baseline metadata/selection ID |
| `--json` | no | full machine-readable regression report |

Human output shows the overall decision, baseline/candidate fingerprint IDs, policy identity and one line per rule.

Regression decisions map to stable automation exit codes:

| Exit | Decision |
| --- | --- |
| `0` | `PASS` |
| `1` | `FAIL` |
| `2` | configuration/execution `ERROR` |
| `3` | `NOT_COMPARABLE` |
| `4` | `NOT_EVALUATED` |

`NOT_COMPARABLE` is not a hidden failure. It means fingerprint/evidence differences make the requested comparison invalid for at least the gated semantics.

## `regress-ci`

Use the same regression engine with conservative CI runner semantics and a durable JSON artifact:

```bash
performance-lab regress-ci \
  --store .performance-lab/runs.sqlite3 \
  --baseline-run baseline-run-id \
  --candidate-run candidate-run-id \
  --policy regression-policy.json \
  --artifact performance-lab-regression.json
```

Additional options:

| Option | Default | Meaning |
| --- | --- | --- |
| `--artifact` | `performance-lab-regression.json` | JSON artifact destination |
| `--runner-identity-controlled` | false | allow already-compatible resource rules to retain their result when runner identity is genuinely controlled |
| `--json` | false | emit CI report JSON to stdout as well |

When `GITHUB_STEP_SUMMARY` exists, the command appends a concise Markdown summary. The JSON artifact is written before returning the gate exit code, including for valid non-zero outcomes.

If an execution/configuration error occurs, an error JSON artifact is still written when possible.

Read [`ci-regression.md`](ci-regression.md) for GitHub Actions integration and resource-comparison safety.

## Automation contract

For scripts and CI:

- use `--json`;
- rely on documented exit codes;
- retain JSON artifacts/bundles rather than parsing terminal prose;
- never treat `NOT_COMPARABLE` as `PASS`;
- never bypass hardware comparability merely because two string labels look equal;
- keep baseline selection explicit.

## Common command sequence

```bash
# 1. Endpoint readiness
performance-lab probe --base-url http://127.0.0.1:1235/v1/ --model my-model

# 2. Baseline
performance-lab run --config baseline.json --json

# 3. Candidate
performance-lab run --config candidate.json --json

# 4. Local comparison/gate
performance-lab regress \
  --store .performance-lab/runs.sqlite3 \
  --baseline-run <baseline-id> \
  --candidate-run <candidate-id> \
  --policy regression-policy.json \
  --json

# 5. CI-safe gate artifact
performance-lab regress-ci \
  --store .performance-lab/runs.sqlite3 \
  --baseline-run <baseline-id> \
  --candidate-run <candidate-id> \
  --policy regression-policy.json \
  --artifact performance-lab-regression.json
```

If a command behaves unexpectedly, use [`troubleshooting.md`](troubleshooting.md).