import { expect, test, type Route } from "@playwright/test";

const API_IDENTITY = { api_version: "v1", read_model_version: 1 } as const;
const NOW = "2026-08-28T08:00:00Z";
const DIGEST = "c".repeat(64);

async function json(route: Route, payload: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(payload) });
}

const target = {
  ...API_IDENTITY,
  target_id: "session-local",
  display_name: "Local LLM Server",
  adapter_type: "openai-compatible",
  endpoint_profile_id: "session-profile-local",
  endpoint_identity: "127.0.0.1:1235/v1/",
  capabilities: ["text_generation"],
};

const scenario = {
  ...API_IDENTITY,
  scenario: "general_capability",
  title: "General capability",
  description: "Use the frozen starter suite.",
  supported: true,
  blocked_reason: null,
  suite_id: "general-diagnostic-starter",
};

const preflight = {
  ...API_IDENTITY,
  can_run: true,
  issues: [],
  preview: {
    ...API_IDENTITY,
    scenario: "general_capability",
    config: {
      target_id: target.target_id,
      endpoint_identity: target.endpoint_identity,
      endpoint: {
        profile_id: target.endpoint_profile_id,
        base_url: "http://127.0.0.1:1235/v1/",
      },
      model_id: "model-discovered",
      output_dir: "results",
      store_path: ".performance-lab/runs.sqlite3",
      run_id: null,
      write_bundle: true,
      use_host_telemetry: false,
      suite_id: "general-diagnostic-starter",
    },
    config_digest: DIGEST,
    target,
    suite: {
      ...API_IDENTITY,
      suite_id: "general-diagnostic-starter",
      suite_version: "1",
      task_count: 1,
      task_ids: ["fixture-task"],
    },
    datasets: [],
    evaluator_ids: ["fixture@1"],
    generation: {},
    load_profile: {},
    prompt_template_version: "1",
    benchmark_protocol_version: "1",
    identity_resolution: "resolved_at_launch",
  },
};

function job(state: "running" | "succeeded") {
  return {
    api_version: "v1",
    job_id: "job-discovered",
    state,
    revision: state === "running" ? 1 : 2,
    created_at: NOW,
    updated_at: NOW,
    config_digest: DIGEST,
    target_id: target.target_id,
    model_id: "model-discovered",
    scenario: "general_capability",
    phase: state === "running" ? "evaluating" : "completed",
    completed_samples: state === "running" ? 1 : 4,
    total_samples: 4,
    run_id: state === "succeeded" ? "run-discovered" : null,
    run_status: state === "succeeded" ? "succeeded" : "running",
    error_code: null,
    error_message: null,
  };
}

const runDetail = {
  ...API_IDENTITY,
  summary: {
    ...API_IDENTITY,
    run_id: "run-discovered",
    status: "succeeded",
    created_at: NOW,
    completed_at: NOW,
    suite_id: "general-diagnostic-starter",
    suite_version: "1",
    fingerprint_id: "fp-discovered",
    identity: {
      ...API_IDENTITY,
      model_id: "model-discovered",
      revision: null,
      quantization: null,
      artifact_digest: null,
      target_id: target.target_id,
      endpoint_identity: target.endpoint_identity,
      runtime_name: "llama.cpp",
      runtime_version: "fixture",
      hardware_device_id: "local-device",
      hardware_device_class: "desktop",
    },
    metrics: [],
  },
  evidence: {
    ...API_IDENTITY,
    fingerprint: { fingerprint_id: "fp-discovered", fixture: true },
    dataset_count: 1,
    evaluator_count: 1,
    sample_count: 4,
  },
};

test("J1 discovery: connect local server, discover model, freeze, run and inspect result", async ({
  page,
}) => {
  let probeBody: Record<string, unknown> | null = null;

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;

    if (path === "/api/v1/targets" && request.method() === "GET") {
      await json(route, []);
      return;
    }
    if (path === "/api/v1/scenarios" && request.method() === "GET") {
      await json(route, [scenario]);
      return;
    }
    if (path === "/api/v1/endpoint-probes" && request.method() === "POST") {
      probeBody = request.postDataJSON() as Record<string, unknown>;
      await json(route, {
        ...API_IDENTITY,
        healthy: true,
        endpoint_identity: target.endpoint_identity,
        target,
        models: [
          {
            ...API_IDENTITY,
            model_id: "model-discovered",
            runtime_parameters: [
              {
                ...API_IDENTITY,
                name: "n_batch",
                scope: "runtime_load",
                current_value: 512,
                editable: false,
                provenance: "local_llm_server",
              },
            ],
          },
        ],
        capabilities: [
          {
            ...API_IDENTITY,
            name: "model_discovery",
            state: "supported",
            source: "observed",
            detail: "GET /v1/models responded successfully",
          },
        ],
        supported_generation_parameters: ["max_output_tokens", "temperature", "top_p"],
        warning: null,
      });
      return;
    }
    if (path === "/api/v1/run-preflight" && request.method() === "POST") {
      await json(route, preflight);
      return;
    }
    if (path === "/api/v1/run-jobs" && request.method() === "POST") {
      await json(route, job("running"), 202);
      return;
    }
    if (path === "/api/v1/run-jobs/job-discovered" && request.method() === "GET") {
      await json(route, job("running"));
      return;
    }
    if (path === "/api/v1/run-jobs/job-discovered/events" && request.method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: `event: run_job\ndata: ${JSON.stringify(job("succeeded"))}\n\n`,
      });
      return;
    }
    if (path === "/api/v1/runs/run-discovered" && request.method() === "GET") {
      await json(route, runDetail);
      return;
    }

    await json(route, { detail: `Unhandled route: ${request.method()} ${path}` }, 500);
  });

  await page.goto("/#test-a-model");
  await expect(page.getByRole("heading", { name: "Test a model" })).toBeVisible();
  await expect(page.getByLabel("Model source")).toHaveValue("local");

  await page.getByRole("button", { name: "Connect & discover" }).click();
  await expect(page.getByText("Connection discovered")).toBeVisible();
  await expect(page.getByLabel("Model", { exact: true })).toHaveValue("model-discovered");

  const runtimeConfig = page.locator("details.disclosure").filter({
    has: page
      .locator("summary")
      .filter({ hasText: "Runtime configuration reported by Local LLM Server" }),
  });
  await expect(runtimeConfig).not.toHaveAttribute("open", "");
  await expect(runtimeConfig.getByText("n_batch")).toBeHidden();
  await runtimeConfig.locator("summary").click();
  await expect(runtimeConfig).toHaveAttribute("open", "");
  await expect(runtimeConfig.getByText("n_batch")).toBeVisible();

  expect(probeBody).toMatchObject({
    base_url: "http://127.0.0.1:1235/v1/",
    server_type: "local_llm_server",
  });

  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByText("Preflight passed")).toBeVisible();
  await page.getByRole("button", { name: "Run test" }).click();

  await expect(page).toHaveURL(/#runs\/run-discovered$/);
  await expect(page.getByRole("heading", { name: "model-discovered" })).toBeVisible();
  await expect(page.getByText("fp-discovered", { exact: true })).toBeVisible();
});
