import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { CampaignPlanningContextReadModel } from "../../api";
import { FindBestSetupView } from "./FindBestSetupPage";

const API_IDENTITY = { api_version: "v1", read_model_version: 1 } as const;

const context: CampaignPlanningContextReadModel = {
  ...API_IDENTITY,
  use_cases: [
    {
      ...API_IDENTITY,
      use_case_id: "general-capability",
      version: "1",
      title: "General capability",
      description: "Balanced authored diagnostics.",
      task_family: "general_capability",
      suite_id: "general-diagnostic-starter",
      suite_version: "2026-08-15-v1",
      source: "starter",
    },
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
      target: {
        ...API_IDENTITY,
        target_id: "local-target",
        display_name: "Local target",
        adapter_type: "openai-compatible",
        endpoint_profile_id: "local-openai",
        endpoint_identity: "loopback:1234",
        capabilities: [],
      },
      hardware_device_id: "device-a",
      hardware_device_class: "laptop",
      candidates: [
        {
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
          generation_parameter_domains: [],
          source: "configured",
        },
      ],
      supported_generation_parameters: ["temperature", "top_p"],
      bounded_generation_parameter_ranges: [],
      configuration_search_options: [
        {
          ...API_IDENTITY,
          strategy: "fixed",
          title: "Fixed",
          description: "Use the authored benchmark configuration.",
          available: true,
          blocked_reason: null,
        },
        {
          ...API_IDENTITY,
          strategy: "quick",
          title: "Quick",
          description: "Search bounded request-level configurations.",
          available: false,
          blocked_reason: "No bounded search ranges were reported.",
        },
      ],
    },
  ],
};

describe("FindBestSetupView", () => {
  it("starts from the use case and exposes the complete canonical journey", () => {
    const markup = renderToStaticMarkup(<FindBestSetupView context={context} />);

    expect(markup).toContain("Find best setup");
    expect(markup).toContain("General capability");
    expect(markup).toContain("Structured document extraction");
    expect(markup).toContain("Candidate models");
    expect(markup).toContain("Configuration search");
    expect(markup).toContain("Benchmark plan");
    expect(markup).toContain("Campaign review / estimate");
    expect(markup).toContain("Campaign");
    expect(markup).toContain("Results");
    expect(markup).not.toContain("Recommended model");
  });
});
