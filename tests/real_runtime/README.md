# Real-runtime acceptance smoke

This directory contains opt-in automation for a **real** Local LLM Server, model and device.
It is separate from the mandatory deterministic PR gate because hosted CI cannot truthfully provide
the target runtime/hardware evidence.

Start Local LLM Server on the target machine, then run:

```bash
python tests/real_runtime/smoke_local_llm_server.py \
  --base-url http://127.0.0.1:1235 \
  --model <runtime-key-or-model-id> \
  --output-dir .performance-lab/real-smoke
```

The script performs a real `performance-lab probe`, writes the exact run config, requires
`local-llm-identity-v1`, samples `/status`, executes the current frozen
`general-diagnostic-starter` suite and preserves the normal SQLite evidence plus `.plab.zip` bundle.

This is a bounded acceptance preflight, not the full representative evidence campaign. Use the
normal run/regression workflow for repeated baselines, load/concurrency evidence, structured-document
workloads and release claims. Do not call the smoke representative merely because it completes.
