import { expect, test } from "@playwright/test";

const API_IDENTITY = { api_version: "v1", read_model_version: 1 } as const;
const PLAN_DIGEST = "a".repeat(64);

const target = {
  ...API_IDENTITY,
  target_id: "local-target",
  display_name: "Local device",
  adapter_type: "openai-compatible",
  endpoint_profile_id: "local-openai",
  endpoint_identity: "127.0.0.1:1234/v1",
  capabilities: ["text_generation"],
};

const candidate = {
  ...API_IDENTITY,
  candidate_id: "candidate-a",
  target_id: "local-target",
  model_id: "model-a",
  revision: null,
  artifact_digest: null,
  quantization: null,
  runtime_name: null,
  runtime_version: null,
  runtime_config_digest: null,
  source: "configured",
};

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
      candidates: [candidate],
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
        {
          ...API_IDENTITY,
          strategy: "quick",
          title: "Quick",
          description: "Search multiple request-level configurations within bounded domains.",
          available: false,
          blocked_reason:
            "The runtime reports parameter support but no bounded search ranges. Performance Lab will not invent sweep domains.",
        },
        {
          ...API_IDENTITY,
          strategy: "standard",
          title: "Standard",
          description: "Search multiple request-level configurations within bounded domains.",
          available: false,
          blocked_reason:
            "The runtime reports parameter support but no bounded search ranges. Performance Lab will not invent sweep domains.",
        },
        {
          ...API_IDENTITY,
          strategy: "thorough",
          title: "Thorough",
          description: "Search multiple request-level configurations within bounded domains.",
          available: false,
          blocked_reason:
            "The runtime reports parameter support but no bounded search ranges. Performance Lab will not invent sweep domains.",
        },
        {
          ...API_IDENTITY,
          strategy: "custom",
          title: "Custom",
          description: "Search multiple request-level configurations within bounded domains.",
          available: false,
          blocked_reason:
            "The runtime reports parameter support but no bounded search ranges. Performance Lab will not invent sweep domains.",
        },
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
  candidates: [candidate],
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
    candidate_count: 1,
    configuration_count_per_candidate: 1,
    planned_run_count: 1,
    benchmark_case_count_per_run: 23,
    estimated_request_count: 23,
    estimated_duration_seconds: null,
    duration_reason:
      "Duration unavailable: no evidence-backed timing model exists for this target and plan.",
  },
  execution_available: false,
  execution_blocked_reason:
    "Campaign execution is not implemented yet; this preview only freezes the intended plan.",
};

test("J0 planning: use case to frozen campaign review is backend-owned and truthful", async ({
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
    const request = route.request().postDataJSON() as Record<string, unknown>;
    expect(request).toMatchObject({
      use_case_id: "general-capability",
      target_id: "local-target",
      candidate_ids: ["candidate-a"],
      configuration_strategy: "fixed",
    });
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(preview),
    });
  });

  await page.goto("/#find-best-setup");

  await expect(page.getByRole("heading", { name: "Find best setup" })).toBeVisible();
  await expect(page.getByText("Structured document extraction")).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByText("model-a", { exact: true })).toBeVisible();
  await expect(page.getByText("Quantization: Unknown")).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByText("Reported request parameters")).toBeVisible();
  await expect(page.getByRole("radio", { name: /Quick/ })).toBeDisabled();
  await expect(
    page.getByText("will not invent sweep domains", { exact: false }).first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "Build benchmark plan" }).click();

  await expect(page.getByRole("heading", { name: "Benchmark plan" })).toBeVisible();
  await expect(page.getByText("general-diagnostic-starter")).toBeVisible();
  await expect(page.getByText("23", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Review campaign" }).click();

  await expect(page.getByRole("heading", { name: "Campaign review / estimate" })).toBeVisible();
  await expect(page.getByText("Plan frozen")).toBeVisible();
  await expect(page.getByText(PLAN_DIGEST)).toBeVisible();
  await expect(page.getByText("Engine pending")).toBeVisible();
  await expect(page.getByRole("button", { name: "Start evaluation campaign" })).toBeDisabled();
  await expect(page.getByText("Duration unavailable", { exact: false })).toBeVisible();
  await expect(page.getByText("Recommended model")).toHaveCount(0);
});
