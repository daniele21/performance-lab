# Real-runtime inference test guidance

This subtree owns opt-in target-environment tests that make claims about **actual model inference**.

## Required runtime boundary

- Every test in this subtree that executes a real model must send inference through `daniele21/local-llm-server`.
- Do not point real-model acceptance tests directly at `llama.cpp`, `llama-server`, LM Studio, an Android harness, or another raw model endpoint.
- Local LLM Server remains the serving/runtime owner; Performance Lab remains the benchmark/evaluation/evidence owner.
- Require the first-party `local-llm-identity-v1` contract for representative runs so model/runtime/device identity is frozen before evaluation.
- Sample Local LLM Server `/status` when runtime/resource evidence is part of the claim.

## What fixtures may prove

Deterministic OpenAI-compatible fixtures remain valid for PR/CI product, protocol, persistence and regression tests. They are **not** real model-inference evidence and must not be described as such.

## Evidence and fidelity

A real-model test is `REAL_ENVIRONMENT` / `target_environment` evidence. Preserve the exact run config, Performance Lab store/run identity, `.plab.zip` bundle, Local LLM Server identity and applicable telemetry. Do not upgrade a hosted fixture result into a model/runtime/device claim.

Use `smoke_local_llm_server.py` for the bounded acceptance path. Broader performance, repeated-load, thermal or resource claims require the representative-device evidence workflow and its retained evidence.
