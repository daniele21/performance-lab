import { expect, test } from "@playwright/test";

const API_IDENTITY = { api_version: "v1", read_model_version: 1 } as const;
const unavailableResources = {
  ...API_IDENTITY,
  state: "unavailable",
  measurements: [],
  note: "No policy-eligible model-resource evidence is retained for this fixture.",
} as const;
const PLAN_DIGEST = "a".repeat(64);
const POLICY = {
  ...API_IDENTITY,
  policy_id: "strict-quality-dominance",
  policy_version: "1.0.0",
  title: "Strict quality dominance",
  method: "strict_quality_dominance",
  description:
    "Recommend only when one candidate strictly dominates every alternative on comparable quality evidence.",
  no_hidden_weights: true,
} as const;

const target = {
  ...API_IDENTITY,
  target_id: "local-target",
  display_name: "Local device",
  adapter_type: "openai-compatible",
  endpoint_profile_id: "local-openai",
  endpoint_identity: "127.0.0.1:1234/v1",
  capabilities: ["text_generation"],
};

function candidate(candidateId: string, modelId: string) {
  return {
    ...API_IDENTITY,
    candidate_id: candidateId,
    target_id: "local-target",
    model_id: modelId,
    revision: null,
    artifact_digest: null,
    quantization: null,
    runtime_name: null,
    runtime_version: null,
    runtime_config_digest: null,
    source: "configured",
  };
}

const candidates = [candidate("candidate-a", "model-a"), candidate("candidate-b", "model-b")];

const useCase = {
  ...API_IDENTITY,
  use_case_id: "general-capability",
  version: "1",
  title: "General capability",
  description: "Balanced authored diagnostics across quality tasks.",
  task_family: "general_capability",
  suite_id: "general-diagnostic-starter",
  suite_version: "2026-08-15-v1",
  source: "starter",
};

const planning = {
  ...API_IDENTITY,
  use_cases: [
    useCase,
    {
      ...API_IDENTITY,
      use_case_id: "structured-document-extraction",
      version: "2026-08-15-v1",
      title: "Structured document extraction",
      description: "Extract a fixed schema from short documents.",
      task_family: "structured_extraction",
      suite_id: "workload-structured-document-extraction",
      suite_version: "2026-08-15-v1",
      source: "workload_pack",
    },
  ],
  targets: [
    {
      ...API_IDENTITY,
      target,
      hardware_device_id: "device-a",
      hardware_device_class: "laptop",
      candidates,
      supported_generation_parameters: ["temperature", "top_p"],
      bounded_generation_parameter_ranges: [],
      configuration_search_options: [
        {
          ...API_IDENTITY,
          strategy: "fixed",
          title: "Fixed",
          description: "Use the authored benchmark generation configuration without a sweep.",
          available: true,
          blocked_reason: null,
        },
        ...["quick", "standard", "thorough", "custom"].map((strategy) => ({
          ...API_IDENTITY,
          strategy,
          title: strategy.charAt(0).toUpperCase() + strategy.slice(1),
          description: "Search multiple request-level configurations within bounded domains.",
          available: false,
          blocked_reason:
            "The runtime reports parameter support but no bounded search ranges. Performance Lab will not invent sweep domains.",
        })),
      ],
    },
  ],
};

const preview = {
  ...API_IDENTITY,
  can_plan: true,
  issues: [],
  plan_digest: PLAN_DIGEST,
  use_case: useCase,
  target,
  candidates,
  configuration_search: {
    ...API_IDENTITY,
    strategy: "fixed",
    title: "Fixed benchmark configuration",
    configuration_count_per_candidate: 1,
    base_generation: { max_output_tokens: 64, temperature: 0, seed: 7 },
    bounded_parameter_ranges: [],
    note: "Uses the benchmark suite generation configuration exactly as authored.",
  },
  benchmark_plan: {
    ...API_IDENTITY,
    suite: {
      ...API_IDENTITY,
      suite_id: "general-diagnostic-starter",
      suite_version: "2026-08-15-v1",
      task_count: 7,
      task_ids: ["instruction_following", "factual_qa", "reasoning"],
    },
    datasets: [
      {
        ...API_IDENTITY,
        dataset_id: "starter-instruction",
        dataset_version: "2026-08-15-v1",
        source: "builtin:performance-lab-authored",
        split: "test",
        sample_count: 3,
        selection_policy: "all-authored-v1",
        content_sha256: "b".repeat(64),
      },
    ],
    evaluator_ids: ["normalized-exact-match@1", "json-schema@1"],
    case_count_per_run: 23,
  },
  estimate: {
    ...API_IDENTITY,
    candidate_count: 2,
    configuration_count_per_candidate: 1,
    planned_run_count: 2,
    benchmark_case_count_per_run: 23,
    estimated_request_count: 46,
    estimated_duration_seconds: null,
    duration_reason:
      "Duration unavailable: no evidence-backed timing model exists for this target and plan.",
  },
  decision_policy: POLICY,
  execution_available: true,
  execution_blocked_reason: null,
};

function identity(modelId: string) {
  return {
    ...API_IDENTITY,
    model_id: modelId,
    revision: null,
    quantization: null,
    artifact_digest: null,
    target_id: "local-target",
    endpoint_identity: "127.0.0.1:1234/v1",
    runtime_name: null,
    runtime_version: null,
    hardware_device_id: "device-a",
    hardware_device_class: "laptop",
  };
}

function qualityMetric(value: number) {
  return {
    ...API_IDENTITY,
    metric_id: "accuracy|normalized-exact-match@1",
    label: "accuracy",
    dimension: "quality",
    availability: "available",
    value,
    unit: null,
    higher_is_better: true,
    provenance: "normalized-exact-match@1",
    protocol_version: null,
  };
}

const campaign = {
  ...API_IDENTITY,
  campaign_id: "campaign-1",
  plan_digest: PLAN_DIGEST,
  use_case_id: "general-capability",
  use_case_version: "1",
  target_id: "local-target",
  suite_id: "general-diagnostic-starter",
  suite_version: "2026-08-15-v1",
  status: "succeeded",
  revision: 5,
  created_at: "2026-08-31T05:00:00Z",
  updated_at: "2026-08-31T05:01:00Z",
  completed_at: "2026-08-31T05:01:00Z",
  entries: [
    {
      ...API_IDENTITY,
      entry_id: "entry-1",
      candidate_id: "candidate-a",
      model_id: "model-a",
      config_digest: "c".repeat(64),
      status: "succeeded",
      run_id: "run-a",
      completed_samples: 23,
      total_samples: 23,
      error_code: null,
      error_message: null,
      identity: identity("model-a"),
      metrics: [qualityMetric(1)],
      resources: unavailableResources,
    },
    {
      ...API_IDENTITY,
      entry_id: "entry-2",
      candidate_id: "candidate-b",
      model_id: "model-b",
      config_digest: "d".repeat(64),
      status: "succeeded",
      run_id: "run-b",
      completed_samples: 23,
      total_samples: 23,
      error_code: null,
      error_message: null,
      identity: identity("model-b"),
      metrics: [qualityMetric(0.5)],
      resources: unavailableResources,
    },
  ],
  results: {
    ...API_IDENTITY,
    state: "ready",
    decision_policy: POLICY,
    compatibility: [
      {
        ...API_IDENTITY,
        dimension: "capability",
        comparable: true,
        evidence_available: true,
        reasons: [],
      },
      {
        ...API_IDENTITY,
        dimension: "runtime",
        comparable: true,
        evidence_available: false,
        reasons: [],
      },
      {
        ...API_IDENTITY,
        dimension: "resource",
        comparable: true,
        evidence_available: false,
        reasons: [],
      },
    ],
    recommendation: {
      ...API_IDENTITY,
      candidate_id: "candidate-a",
      run_id: "run-a",
      model_id: "model-a",
      rationale:
        "This candidate is no worse on every comparable quality metric and strictly better against every alternative.",
    },
    recommendation_reason:
      "This candidate is no worse on every comparable quality metric and strictly better against every alternative.",
  },
  error_code: null,
  error_message: null,
};

test("J0 campaign: four-stage setup executes and produces policy-backed results", async ({
  page,
}) => {
  await page.route("**/api/v1/campaign-planning", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(planning),
    });
  });
  await page.route("**/api/v1/campaign-plan-preview", async (route) => {
    expect(route.request().method()).toBe("POST");
    expect(route.request().postDataJSON()).toMatchObject({
      use_case_id: "general-capability",
      target_id: "local-target",
      candidate_ids: ["candidate-a", "candidate-b"],
      configuration_strategy: "fixed",
    });
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(preview),
    });
  });
  await page.route("**/api/v1/campaigns", async (route) => {
    expect(route.request().method()).toBe("POST");
    expect(route.request().postDataJSON()).toMatchObject({
      plan_digest: PLAN_DIGEST,
      plan: {
        use_case_id: "general-capability",
        target_id: "local-target",
        candidate_ids: ["candidate-a", "candidate-b"],
        configuration_strategy: "fixed",
      },
    });
    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify(campaign),
    });
  });
  await page.route("**/api/v1/campaigns/campaign-1", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(campaign),
    });
  });

  await page.goto("/#find-best-setup");
  await expect(page.getByRole("heading", { name: "Find best setup" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "What do you want to optimize?" })).toBeVisible();
  await expect(page.getByText("Draft", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByRole("heading", { name: "Select models to compare" })).toBeVisible();
  await expect(page.getByText("2 eligible models found", { exact: true })).toBeVisible();
  await expect(page.getByText("model-a", { exact: true })).toBeVisible();
  await expect(page.getByText("model-b", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(
    page.getByRole("heading", { name: "How thoroughly should we search?" }),
  ).toBeVisible();
  await expect(page.getByRole("radio", { name: /Quick/ })).toBeDisabled();
  await expect(
    page.getByText("will not invent sweep domains", { exact: false }).first(),
  ).toBeVisible();
  await expect(page.getByRole("radio", { name: /Single configuration/ })).toBeChecked();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByRole("heading", { name: "Review your evaluation" })).toBeVisible();
  await expect(page.getByText("Ready to evaluate", { exact: true })).toBeVisible();
  await expect(page.getByText("2", { exact: true }).first()).toBeVisible();
  await page.getByText("Technical details (advanced)", { exact: true }).click();
  await expect(page.getByText(PLAN_DIGEST)).toBeVisible();
  await expect(page.getByText("strict-quality-dominance@1.0.0")).toBeVisible();
  await page.getByRole("button", { name: "Start evaluation" }).click();

  await expect(page).toHaveURL(/#campaigns\/campaign-1$/);
  await expect(page.getByRole("heading", { name: "Evaluation complete" })).toBeVisible();
  await expect(page.getByLabel("Campaign results")).toBeVisible();
  await expect(
    page.getByText("No hidden weights · No universal score", { exact: false }),
  ).toBeVisible();
  await expect(page.getByText("Recommended setup", { exact: true })).toBeVisible();
  await expect(page.getByText("model-a", { exact: true }).last()).toBeVisible();
  await expect(page.getByText("Comparable", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Inspect recommended Run" })).toBeVisible();

  const resultsLeadTerminalProgress = await page.locator(".campaign-page").evaluate((root) => {
    const results = root.querySelector(".campaign-results");
    const progress = root.querySelector(".campaign-progress-section");
    if (!results || !progress) return false;
    const position = results.compareDocumentPosition(progress);
    return (position & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
  });
  expect(resultsLeadTerminalProgress).toBe(true);
});
