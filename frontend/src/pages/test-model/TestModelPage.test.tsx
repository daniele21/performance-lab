import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type {
  RunPreflightReadModel,
  ScenarioSummaryReadModel,
  TargetSummaryReadModel,
} from "../../api";
import { TestModelView } from "./TestModelPage";

const target: TargetSummaryReadModel = {
  api_version: "v1",
  read_model_version: 1,
  target_id: "local-device",
  display_name: "Local device",
  adapter_type: "openai-compatible",
  endpoint_profile_id: "local-openai",
  endpoint_identity: "loopback:1234",
  capabilities: ["text_generation"],
};

const scenarios: ScenarioSummaryReadModel[] = [
  {
    api_version: "v1",
    read_model_version: 1,
    scenario: "general_capability",
    title: "General capability",
    description: "Balanced diagnostic coverage.",
    supported: true,
    blocked_reason: null,
    suite_id: "general-diagnostic-starter",
  },
  {
    api_version: "v1",
    read_model_version: 1,
    scenario: "performance",
    title: "Performance",
    description: "Performance-only scenario.",
    supported: false,
    blocked_reason: "Dedicated performance presets are not wired yet.",
    suite_id: null,
  },
];

const selection = {
  targetId: "local-device",
  modelId: "model-a",
  scenario: "general_capability" as const,
  useHostTelemetry: true,
};

const preflight: RunPreflightReadModel = {
  api_version: "v1",
  read_model_version: 1,
  can_run: true,
  issues: [],
  preview: {
    api_version: "v1",
    read_model_version: 1,
    scenario: "general_capability",
    config: {
      target_id: "local-device",
      endpoint_identity: "loopback:1234",
      endpoint: {},
      model_id: "model-a",
      output_dir: "artifacts/starter-run",
      store_path: "artifacts/performance-lab.sqlite3",
      run_id: null,
      write_bundle: true,
      use_host_telemetry: true,
      suite_id: "general-diagnostic-starter",
    },
    config_digest: "a".repeat(64),
    target,
    suite: {
      api_version: "v1",
      read_model_version: 1,
      suite_id: "general-diagnostic-starter",
      suite_version: "1",
      task_count: 1,
      task_ids: ["qa"],
    },
    datasets: [],
    evaluator_ids: ["exact-match@1"],
    generation: {},
    load_profile: {},
    prompt_template_version: "direct-user-v1",
    benchmark_protocol_version: "starter-quality-v1",
    identity_resolution: "resolved_at_launch",
  },
};

describe("TestModelView", () => {
  it("keeps unsupported scenarios visible but disabled with the backend reason", () => {
    const markup = renderToStaticMarkup(
      <TestModelView
        targets={[target]}
        scenarios={scenarios}
        selection={selection}
        step="scenario"
        preflight={null}
      />,
    );

    expect(markup).toContain("Performance");
    expect(markup).toContain("Dedicated performance presets are not wired yet.");
    expect(markup).toContain("disabled");
  });

  it("shows the frozen config digest and keeps launch disabled until lifecycle exists", () => {
    const markup = renderToStaticMarkup(
      <TestModelView
        targets={[target]}
        scenarios={scenarios}
        selection={selection}
        step="review"
        preflight={preflight}
      />,
    );

    expect(markup).toContain("Frozen config digest");
    expect(markup).toContain("a".repeat(64));
    expect(markup).toContain("Run test");
    expect(markup).toContain("Launch remains disabled");
  });
});
