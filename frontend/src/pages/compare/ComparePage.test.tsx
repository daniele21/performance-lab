import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { ComparisonReadModel, RunSummaryReadModel } from "../../api";
import { CompareView } from "./ComparePage";

function run(runId: string, modelId: string): RunSummaryReadModel {
  return {
    api_version: "v1",
    read_model_version: 1,
    run_id: runId,
    status: "succeeded",
    created_at: "2026-08-18T10:00:00Z",
    completed_at: "2026-08-18T10:01:00Z",
    suite_id: "general-diagnostic-starter",
    suite_version: "1",
    fingerprint_id: `fingerprint-${runId}`,
    identity: {
      api_version: "v1",
      read_model_version: 1,
      model_id: modelId,
      revision: null,
      quantization: null,
      artifact_digest: null,
      target_id: "local-target",
      endpoint_identity: "loopback",
      runtime_name: null,
      runtime_version: null,
      hardware_device_id: "device-a",
      hardware_device_class: "laptop",
    },
    metrics: [],
  };
}

const runs = [run("baseline", "model-a"), run("candidate", "model-b")];

function comparison(): ComparisonReadModel {
  return {
    api_version: "v1",
    read_model_version: 1,
    baseline_run_id: "baseline",
    candidate_run_id: "candidate",
    identity_differences: [
      {
        path: "fingerprint.model.model_id",
        baseline: "model-a",
        candidate: "model-b",
      },
    ],
    dimensions: [
      {
        api_version: "v1",
        read_model_version: 1,
        dimension: "capability",
        comparable: false,
        reasons: [
          {
            api_version: "v1",
            read_model_version: 1,
            code: "dataset_snapshot_mismatch",
            field: "dataset_snapshots",
            message: "Dataset snapshots differ.",
            baseline: "a",
            candidate: "b",
          },
        ],
        deltas: [
          {
            metric: "must-not-render",
            baseline_value: 0.5,
            candidate_value: 0.9,
            absolute_delta: 0.4,
            relative_delta_pct: 80,
            higher_is_better: true,
            unit: null,
          },
        ],
        missing_in_baseline: [],
        missing_in_candidate: [],
      },
      {
        api_version: "v1",
        read_model_version: 1,
        dimension: "runtime",
        comparable: true,
        reasons: [],
        deltas: [
          {
            metric: "latency_ms|client|v1|ms",
            baseline_value: 100,
            candidate_value: 80,
            absolute_delta: -20,
            relative_delta_pct: -20,
            higher_is_better: null,
            unit: "ms",
          },
        ],
        missing_in_baseline: [],
        missing_in_candidate: [],
      },
      {
        api_version: "v1",
        read_model_version: 1,
        dimension: "resource",
        comparable: true,
        reasons: [],
        deltas: [],
        missing_in_baseline: [],
        missing_in_candidate: [],
      },
    ],
  };
}

describe("CompareView", () => {
  it("renders identity differences before dimension-specific compatibility", () => {
    const markup = renderToStaticMarkup(
      <CompareView
        runs={runs}
        baselineRunId="baseline"
        candidateRunId="candidate"
        comparison={comparison()}
      />,
    );

    expect(markup.indexOf("Identity differences")).toBeLessThan(markup.indexOf("Not comparable"));
    expect(markup).toContain("fingerprint.model.model_id");
    expect(markup).toContain("Dataset snapshots differ.");
  });

  it("suppresses deltas for non-comparable dimensions even if transport contains them", () => {
    const markup = renderToStaticMarkup(
      <CompareView
        runs={runs}
        baselineRunId="baseline"
        candidateRunId="candidate"
        comparison={comparison()}
      />,
    );

    expect(markup).not.toContain("must-not-render");
    expect(markup).toContain("latency_ms");
    expect(markup).toContain("Absolute: -20 ms");
  });

  it("keeps comparable-but-unevaluated evidence distinct from not comparable", () => {
    const markup = renderToStaticMarkup(
      <CompareView
        runs={runs}
        baselineRunId="baseline"
        candidateRunId="candidate"
        comparison={comparison()}
      />,
    );

    expect(markup).toContain("No shared evaluated metrics");
    expect(markup).toContain("the two runs do not expose a shared metric delta");
  });
});
