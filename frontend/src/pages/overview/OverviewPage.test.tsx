import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { TestedModelReadModel } from "../../api";
import { OverviewView } from "./OverviewPage";

const model: TestedModelReadModel = {
  api_version: "v1",
  read_model_version: 1,
  cohort_key: "cohort-a",
  run_count: 2,
  latest_run_id: "run-2",
  latest_completed_at: "2026-08-18T08:00:00Z",
  identity: {
    api_version: "v1",
    read_model_version: 1,
    model_id: "model-a",
    revision: null,
    quantization: "q4",
    artifact_digest: null,
    target_id: "local",
    endpoint_identity: "loopback",
    runtime_name: "runtime-a",
    runtime_version: "1",
    hardware_device_id: "device-a",
    hardware_device_class: "cpu",
  },
  latest_metrics: [
    {
      api_version: "v1",
      read_model_version: 1,
      metric_id: "accuracy",
      label: "Accuracy",
      dimension: "quality",
      availability: "available",
      value: 0.82,
      unit: null,
      higher_is_better: true,
      provenance: "exact-match@1",
      protocol_version: null,
    },
  ],
};

describe("OverviewView", () => {
  it("foregrounds tested-model identity without inventing a recommendation", () => {
    const markup = renderToStaticMarkup(<OverviewView models={[model]} runs={[]} />);

    expect(markup).toContain("model-a");
    expect(markup).toContain("device-a");
    expect(markup).toContain("Accuracy");
    expect(markup).not.toContain("Recommended model");
  });

  it("makes the use-case-first decision path the primary empty-state action", () => {
    const markup = renderToStaticMarkup(<OverviewView models={[]} runs={[]} />);

    expect(markup).toContain("No tested models yet");
    expect(markup).toContain("Find best setup");
    expect(markup).toContain("Test a model");
  });
});
