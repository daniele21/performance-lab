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

Start Local LLM Server on the target machine, then run:

```bash
python tests/real_runtime/smoke_local_llm_server.py \
  --base-url http://127.0.0.1:1235 \
  --model <runtime-key-or-model-id> \
  --output-dir .performance-lab/real-smoke
```

The script performs a real `performance-lab probe`, writes the exact run config, requires
`local-llm-identity-v1`, samples `/status`, executes the current frozen
`general-diagnostic-starter` suite through Local LLM Server and preserves the normal SQLite evidence
plus `.plab.zip` bundle.

This is a bounded acceptance preflight, not the full representative evidence campaign. Use the
normal run/regression workflow for repeated baselines, load/concurrency evidence, structured-document
workloads and release claims. Do not call the smoke representative merely because it completes.
