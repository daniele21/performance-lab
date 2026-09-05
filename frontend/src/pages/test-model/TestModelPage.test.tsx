import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type {
  EndpointProbeReadModel,
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
      evidence_mode: "evidence_rich",
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

const probe: EndpointProbeReadModel = {
  api_version: "v1",
  read_model_version: 1,
  healthy: true,
  endpoint_identity: "127.0.0.1:1235/v1/",
  target: {
    ...target,
    target_id: "session-123",
    display_name: "Local LLM Server",
    endpoint_profile_id: "session-profile-123",
    endpoint_identity: "127.0.0.1:1235/v1/",
  },
  models: [
    {
      api_version: "v1",
      read_model_version: 1,
      model_id: "model-a",
      runtime_parameters: [
        {
          api_version: "v1",
          read_model_version: 1,
          name: "n_batch",
          scope: "runtime_load",
          current_value: 512,
          editable: false,
          provenance: "local_llm_server",
        },
      ],
      generation_parameter_domains: [],
    },
  ],
  capabilities: [
    {
      api_version: "v1",
      read_model_version: 1,
      name: "model_discovery",
      state: "supported",
      source: "observed",
      detail: "GET /v1/models responded successfully",
    },
  ],
  supported_generation_parameters: ["max_output_tokens", "temperature", "top_p"],
  warning: null,
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

  it("shows automatically discovered models for a configured target", () => {
    const markup = renderToStaticMarkup(
      <TestModelView
        targets={[target]}
        scenarios={scenarios}
        selection={selection}
        step="model"
        preflight={null}
        modelSource="configured"
        probe={{ ...probe, target }}
      />,
    );

    expect(markup).toContain("Model");
    expect(markup).toContain("model-a");
    expect(markup).toContain("reported by 127.0.0.1:1235/v1/");
    expect(markup).not.toContain("Automatic discovery is unavailable");
  });

  it("keeps manual model ID as a fallback when configured discovery fails", () => {
    const markup = renderToStaticMarkup(
      <TestModelView
        targets={[target]}
        scenarios={scenarios}
        selection={{ ...selection, modelId: "" }}
        step="model"
        preflight={null}
        modelSource="configured"
        probeError="Target discovery failed"
      />,
    );

    expect(markup).toContain("Target discovery failed");
    expect(markup).toContain("Model ID");
    expect(markup).toContain("only as a fallback");
  });

  it("shows discovered local models and honest runtime/request capabilities", () => {
    const markup = renderToStaticMarkup(
      <TestModelView
        targets={[target]}
        scenarios={scenarios}
        selection={{ ...selection, targetId: "session-123" }}
        step="model"
        preflight={null}
        modelSource="local"
        probe={probe}
      />,
    );

    expect(markup).toContain("Connect &amp; discover");
    expect(markup).toContain("model-a");
    expect(markup).toContain("temperature");
    expect(markup).toContain("n_batch");
    expect(markup).toContain("saved in this browser");
    expect(markup).toContain("Credentials are never stored");
    expect(markup).toContain("do not imply server-specific min/max ranges");
  });

  it("shows the frozen config digest and enables launch only after executable preflight", () => {
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
    expect(markup).toContain("evidence_rich");
    expect(markup).toContain("a".repeat(64));
    expect(markup).toContain("Run test");
    expect(markup).toContain("continues in the local Performance Lab process");
    expect(markup).not.toContain("Launch remains disabled");
  });
});
