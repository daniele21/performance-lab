import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { BenchmarkDetailReadModel, SampleEvidenceDetailReadModel } from "../api";
import { BenchmarkDetailView } from "./benchmark-detail";
import { SampleEvidenceView } from "./sample-evidence";

const API_IDENTITY = { api_version: "v1", read_model_version: 1 } as const;
const dataset = {
  ...API_IDENTITY,
  dataset_id: "dataset-a",
  dataset_version: "snapshot-1",
  source: "fixture",
  split: "test",
  sample_count: 1,
  selection_policy: "frozen",
  content_sha256: "a".repeat(64),
};
const evaluator = {
  ...API_IDENTITY,
  evaluator_id: "exact-match",
  version: "1",
  evaluator_type: "exact_match",
  deterministic: true,
  explanation_supported: false,
  rule_summary: "Normalize text and compare exact equality.",
  configuration: {},
};

const benchmark: BenchmarkDetailReadModel = {
  ...API_IDENTITY,
  summary: {
    ...API_IDENTITY,
    suite_id: "starter",
    suite_version: "1",
    task_count: 1,
    task_ids: ["task-a"],
  },
  generation: { temperature: 0 },
  tasks: [
    {
      ...API_IDENTITY,
      task_id: "task-a",
      dataset_snapshot_id: "dataset-a:snapshot-1",
      dataset,
      evaluator,
      metric_names: ["accuracy"],
      sample_limit: null,
      case_count: 1,
      case_content_available: true,
    },
  ],
  cases: [
    {
      ...API_IDENTITY,
      case_id: "case-a",
      task_id: "task-a",
      sample_id: "sample-a",
      dataset_id: "dataset-a",
      dataset_version: "snapshot-1",
      input: "Question?",
      expected: "Expected answer",
      evaluator_id: "exact-match",
      evaluator_version: "1",
      metric_names: ["accuracy"],
    },
  ],
  definition_issues: [],
};

const sampleDetail: SampleEvidenceDetailReadModel = {
  ...API_IDENTITY,
  run: {
    ...API_IDENTITY,
    run_id: "run-a",
    status: "succeeded",
    created_at: "2026-08-30T10:00:00Z",
    completed_at: "2026-08-30T10:00:01Z",
    suite_id: "starter",
    suite_version: "1",
    fingerprint_id: "fingerprint-a",
    identity: {
      ...API_IDENTITY,
      model_id: "model-a",
      revision: "r1",
      quantization: "Q4_K_M",
      artifact_digest: null,
      target_id: "local",
      endpoint_identity: "loopback",
      runtime_name: "llama.cpp",
      runtime_version: "1",
      hardware_device_id: "device-a",
      hardware_device_class: "cpu",
    },
    metrics: [],
  },
  fingerprint: { fingerprint_id: "fingerprint-a", target_id: "local" },
  sample: {
    ...API_IDENTITY,
    run_id: "run-a",
    task_id: "task-a",
    sample_id: "sample-a",
    attempt: 1,
    status: "succeeded",
    started_at: "2026-08-30T10:00:00Z",
    completed_at: "2026-08-30T10:00:01Z",
    elapsed_ms: 1000,
    elapsed_provenance: "sample_execution_timestamps",
    input_tokens: 4,
    output_tokens: 2,
    score_count: 1,
    measurement_count: 1,
    error: null,
  },
  benchmark_case: benchmark.cases[0],
  prompt: {
    ...API_IDENTITY,
    state: "not_retained",
    content: null,
    reason: "content_not_retained",
  },
  response: {
    ...API_IDENTITY,
    state: "not_retained",
    content: null,
    reason: "content_not_retained",
  },
  quality: {
    ...API_IDENTITY,
    verdict: "correct",
    metric: "accuracy",
    value: 1,
    percentage: 100,
  },
  scores: [
    {
      ...API_IDENTITY,
      metric: "accuracy",
      value: 1,
      evaluator_id: "exact-match",
      evaluator_version: "1",
      higher_is_better: true,
      numerator: 1,
      denominator: 1,
      evaluator_rule_summary: evaluator.rule_summary,
      explanation_state: "unavailable",
      explanation: null,
    },
  ],
  measurements: [
    {
      ...API_IDENTITY,
      name: "latency_ms",
      value: 1000,
      unit: "ms",
      scope: "sample",
      provenance: "client",
      protocol_version: "latency-v1",
      observed_at: null,
    },
  ],
  definition_issues: [],
};

const retainedSampleDetail: SampleEvidenceDetailReadModel = {
  ...sampleDetail,
  prompt: {
    ...API_IDENTITY,
    state: "retained",
    content: "Rendered prompt actually sent to the model",
    reason: null,
  },
  response: {
    ...API_IDENTITY,
    state: "retained",
    content: "Expected answer",
    reason: null,
  },
};

describe("evidence drilldown views", () => {
  it("keeps benchmark definition separate from execution results", () => {
    const markup = renderToStaticMarkup(<BenchmarkDetailView benchmark={benchmark} />);

    expect(markup).toContain("Benchmark definition");
    expect(markup).toContain("Question?");
    expect(markup).toContain("Expected answer");
    expect(markup).toContain("Normalize text and compare exact equality.");
    expect(markup).not.toContain("model-a");
  });

  it("renders explicit retention and correctness without confusing benchmark input with prompt", () => {
    const markup = renderToStaticMarkup(<SampleEvidenceView detail={sampleDetail} />);

    expect(markup).toContain("model-a");
    expect(markup).toContain("Q4_K_M");
    expect(markup).toContain("Quality");
    expect(markup).toContain("Correct");
    expect(markup).toContain("accuracy · 1 · 100%");
    expect(markup).toContain("Execution");
    expect(markup).toContain("Prompt sent to model");
    expect(markup).toContain("Model output");
    expect(markup).toContain("Expected output");
    expect(markup).toContain("Expected answer");
    expect(markup).toContain("Original benchmark input");
    expect(markup).toContain("It is not automatically the prompt sent to the model.");
    expect(markup.match(/Content not retained/g)?.length).toBe(2);
    expect(markup).toContain("Evaluation explanation unavailable");
    expect(markup).toContain("client · sample · latency-v1");
  });

  it("puts the executed prompt before model output and expected output when content is retained", () => {
    const markup = renderToStaticMarkup(<SampleEvidenceView detail={retainedSampleDetail} />);

    const promptLabel = markup.indexOf("Prompt sent to model");
    const modelOutputLabel = markup.indexOf("Model output");
    const expectedOutputLabel = markup.indexOf("Expected output");

    expect(promptLabel).toBeGreaterThanOrEqual(0);
    expect(modelOutputLabel).toBeGreaterThan(promptLabel);
    expect(expectedOutputLabel).toBeGreaterThan(modelOutputLabel);
    expect(markup).toContain("Rendered prompt actually sent to the model");
    expect(markup).toContain("Expected answer");
    expect(markup).toContain("Evidence-rich local content");
    expect(markup).toContain("excluded from aggregate-safe portable bundles");
  });
});
