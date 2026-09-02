# Real-runtime acceptance smoke

This directory contains opt-in automation for a **real** Local LLM Server, model and device.
It is separate from the mandatory deterministic PR gate because hosted CI cannot truthfully provide
the target runtime/hardware evidence.

## Required inference boundary

Any test that makes a claim about **actual model inference** must execute the model through
`daniele21/local-llm-server`. Do not use a raw `llama.cpp`/`llama-server`, LM Studio, Android harness
or another direct model endpoint as the representative Performance Lab inference test target.

Deterministic OpenAI-compatible fixtures remain correct for PR/CI workflow, protocol, persistence and
regression coverage. They are not real model-inference evidence and must not be presented as such.

## VALUE-01 bounded real run

Before entering the real environment, produce a current exact-head PRE_REAL manifest through the
repository-owned Built Product / pre-real workflow. The real-run entrypoint rejects stale or failed
PRE_REAL evidence.

Start Local LLM Server on the representative target machine, then run:

```bash
python tests/real_runtime/smoke_local_llm_server.py \
  --base-url http://127.0.0.1:1235 \
  --model <runtime-key-or-model-id> \
  --output-dir .performance-lab/value01-real \
  --pre-real-manifest build/pre-real-e2e/manifest.json
```

The command records the current Performance Lab source revision, validates that the PRE_REAL manifest
belongs to that exact revision, probes `/v1/models`, writes the frozen run config, requires
`local-llm-identity-v1`, samples `/status`, enables `evidence_rich` local sample retention and executes
the current `general-diagnostic-starter` suite through Local LLM Server.

The output directory retains:

- the exact generated run config;
- the SQLite run/evidence store;
- the normal `.plab.zip` portable bundle;
- a bounded VALUE-01 manifest with source revision, run id, fingerprint id, evidence paths and each
  preflight/run step marked PASS/FAIL.

The manifest contains no credentials or raw prompt/output content. Evidence-rich prompt/output content
remains in the local SQLite sidecar and is deliberately excluded from the portable bundle.

This command closes only the single-model execution part of VALUE-01. It does not prove repeatability,
thermal behavior, multi-model ranking, configuration optimization or regression quality merely because
one run succeeds. Those claims remain in later VALUE slices and the representative-device evidence
workstream.
