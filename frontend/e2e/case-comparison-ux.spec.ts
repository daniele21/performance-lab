import { expect, test } from "@playwright/test";

const API = { api_version: "v1", read_model_version: 1 } as const;
const unavailableResources = {
  ...API,
  state: "unavailable",
  measurements: [],
  note: "No policy-eligible model-resource evidence is retained for this fixture.",
} as const;

function identity(modelId: string) {
  return {
    ...API,
    model_id: modelId,
    revision: null,
    quantization: "Q4_K_M",
    artifact_digest: null,
    target_id: "local-target",
    endpoint_identity: "127.0.0.1:1234/v1",
    runtime_name: "llama.cpp",
    runtime_version: "b7000",
    hardware_device_id: "device-a",
    hardware_device_class: "laptop",
  };
}

function metric(value: number) {
  return {
    ...API,
    metric_id: "accuracy|exact@1",
    label: "accuracy",
    dimension: "quality",
    availability: "available",
    value,
    unit: null,
    higher_is_better: true,
    provenance: "exact@1",
    protocol_version: null,
  };
}

function entry(index: number, modelId: string, value: number) {
  return {
    ...API,
    entry_id: `entry-${index}`,
    candidate_id: `candidate-${index}`,
    configuration_id: "fixed-1",
    model_id: modelId,
    config_digest: String(index).repeat(64),
    status: "succeeded",
    run_id: `run-${index}`,
    completed_samples: 1,
    total_samples: 1,
    error_code: null,
    error_message: null,
    identity: identity(modelId),
    metrics: [metric(value)],
    resources: unavailableResources,
  };
}

const campaign = {
  ...API,
  campaign_id: "campaign-j9",
  plan_digest: "a".repeat(64),
  use_case_id: "general-capability",
  use_case_version: "1",
  target_id: "local-target",
  suite_id: "general-diagnostic-starter",
  suite_version: "2026-08-15-v1",
  status: "succeeded",
  revision: 4,
  created_at: "2026-08-31T06:00:00Z",
  updated_at: "2026-08-31T06:01:00Z",
  completed_at: "2026-08-31T06:01:00Z",
  entries: [entry(1, "model-a", 1), entry(2, "model-b", 0.9), entry(3, "model-c", 0.7)],
  results: {
    ...API,
    state: "ready",
    decision_policy: {
      ...API,
      policy_id: "strict-quality-dominance",
      policy_version: "1.0.0",
      title: "Strict quality dominance",
      method: "strict_quality_dominance",
      description: "Only a unique compatible dominance result may be recommended.",
      no_hidden_weights: true,
    },
    compatibility: [
      {
        ...API,
        dimension: "capability",
        comparable: false,
        evidence_available: true,
        reasons: [
          {
            ...API,
            baseline_run_id: "run-1",
            candidate_run_id: "run-3",
            code: "prompt_template_mismatch",
            field: "prompt_template_version",
            message: "prompt_template_version differs between baseline and candidate",
          },
        ],
      },
    ],
    recommendation: null,
    recommendation_reason: "Not every candidate is capability-compatible.",
  },
  error_code: null,
  error_message: null,
};

const caseSummary = {
  ...API,
  task_id: "reasoning",
  sample_id: "case-7",
  case_id: "reasoning:case-7",
  candidate_count: 3,
  available_candidate_count: 3,
};

function evidence(runId: string, modelId: string, score: number) {
  return {
    ...API,
    run: {
      ...API,
      run_id: runId,
      status: "succeeded",
      created_at: "2026-08-31T06:00:00Z",
      completed_at: "2026-08-31T06:00:01Z",
      suite_id: "general-diagnostic-starter",
      suite_version: "2026-08-15-v1",
      fingerprint_id: `${runId}-fingerprint`,
      identity: identity(modelId),
      metrics: [metric(score)],
    },
    fingerprint: { fingerprint_id: `${runId}-fingerprint` },
    sample: {
      ...API,
      run_id: runId,
      task_id: "reasoning",
      sample_id: "case-7",
      attempt: 1,
      status: "succeeded",
      started_at: "2026-08-31T06:00:00Z",
      completed_at: "2026-08-31T06:00:00.100Z",
      elapsed_ms: 100,
      elapsed_provenance: "sample_execution_timestamps",
      input_tokens: 8,
      output_tokens: 2,
      score_count: 1,
      measurement_count: 0,
      error: null,
    },
    benchmark_case: {
      ...API,
      case_id: "reasoning:case-7",
      task_id: "reasoning",
      sample_id: "case-7",
      dataset_id: "reasoning-set",
      dataset_version: "1",
      input: "A is above B. Is B above A?",
      expected: "no",
      evaluator_id: "exact",
      evaluator_version: "1",
      metric_names: ["accuracy"],
    },
    prompt: {
      ...API,
      state: "not_retained",
      content: null,
      reason: "Execution prompt content is not retained by the current evidence policy.",
    },
    response: {
      ...API,
      state: "not_retained",
      content: null,
      reason: "Model response content is not retained by the current evidence policy.",
    },
    scores: [
      {
        ...API,
        metric: "accuracy",
        value: score,
        evaluator_id: "exact",
        evaluator_version: "1",
        higher_is_better: true,
        numerator: null,
        denominator: null,
        evaluator_rule_summary: "Exact normalized match",
        explanation_state: "unavailable",
        explanation: null,
      },
    ],
    measurements: [],
    definition_issues: [],
  };
}

const comparison = {
  ...API,
  campaign_id: "campaign-j9",
  suite_id: "general-diagnostic-starter",
  suite_version: "2026-08-15-v1",
  task_id: "reasoning",
  sample_id: "case-7",
  state: "partial",
  reference_run_id: "run-1",
  benchmark_case: evidence("run-1", "model-a", 1).benchmark_case,
  candidates: [
    {
      ...API,
      entry_id: "entry-1",
      candidate_id: "candidate-1",
      configuration_id: "fixed-1",
      model_id: "model-a",
      config_digest: "1".repeat(64),
      entry_status: "succeeded",
      run_id: "run-1",
      identity: identity("model-a"),
      comparable_to_reference: true,
      compatibility_reasons: [],
      evidence: evidence("run-1", "model-a", 1),
      resources: unavailableResources,
      unavailable_reason: null,
    },
    {
      ...API,
      entry_id: "entry-2",
      candidate_id: "candidate-2",
      configuration_id: "fixed-1",
      model_id: "model-b",
      config_digest: "2".repeat(64),
      entry_status: "succeeded",
      run_id: "run-2",
      identity: identity("model-b"),
      comparable_to_reference: true,
      compatibility_reasons: [],
      evidence: evidence("run-2", "model-b", 0.9),
      resources: unavailableResources,
      unavailable_reason: null,
    },
    {
      ...API,
      entry_id: "entry-3",
      candidate_id: "candidate-3",
      configuration_id: "fixed-1",
      model_id: "model-c",
      config_digest: "3".repeat(64),
      entry_status: "succeeded",
      run_id: "run-3",
      identity: identity("model-c"),
      comparable_to_reference: false,
      compatibility_reasons: [
        {
          ...API,
          baseline_run_id: "run-1",
          candidate_run_id: "run-3",
          code: "prompt_template_mismatch",
          field: "prompt_template_version",
          message: "prompt_template_version differs between baseline and candidate",
        },
      ],
      evidence: evidence("run-3", "model-c", 0.7),
      resources: unavailableResources,
      unavailable_reason: null,
    },
  ],
  comparable_candidate_count: 2,
  summary:
    "At least two candidate Runs can be compared for this exact case. Missing or incompatible candidates remain explicit and are excluded from conclusions.",
};

test("J9: campaign results drill into one exact case and explain incompatible candidates", async ({
  page,
}) => {
  await page.route("**/api/v1/campaigns/campaign-j9", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(campaign),
    });
  });
  await page.route("**/api/v1/campaigns/campaign-j9/cases", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([caseSummary]),
    });
  });
  await page.route("**/api/v1/campaigns/campaign-j9/cases/reasoning/case-7", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(comparison),
    });
  });

  await page.goto("/#campaigns/campaign-j9");
  await expect(page.getByRole("heading", { name: "Results" })).toBeVisible();
  await expect(page.getByText("reasoning:case-7")).toBeVisible();
  await page.getByRole("button", { name: "Compare across candidates" }).click();

  await expect(page).toHaveURL("/#campaigns/campaign-j9/cases/reasoning/case-7");
  await expect(page.getByText("Partially comparable")).toBeVisible();
  await expect(page.getByText("model-a", { exact: true })).toBeVisible();
  await expect(page.getByText("model-b", { exact: true })).toBeVisible();
  await expect(page.getByText("model-c", { exact: true })).toBeVisible();
  await expect(
    page.getByText("prompt_template_version differs between baseline and candidate"),
  ).toBeVisible();
  await expect(page.getByText("Content not retained").first()).toBeVisible();
  await expect(page.getByText("accuracy · exact@1").first()).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Open exact sample evidence" }).first(),
  ).toHaveAttribute("href", "#runs/run-1/samples/reasoning/case-7/1");
});
