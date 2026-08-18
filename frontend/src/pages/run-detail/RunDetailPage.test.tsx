import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { RunDetailReadModel } from "../../api";
import { RunDetailView } from "./RunDetailPage";

const run: RunDetailReadModel = {
  api_version: "v1",
  read_model_version: 1,
  summary: {
    api_version: "v1",
    read_model_version: 1,
    run_id: "run-1",
    status: "succeeded",
    created_at: "2026-08-18T07:00:00Z",
    completed_at: "2026-08-18T07:01:00Z",
    suite_id: "starter",
    suite_version: "1",
    fingerprint_id: "fingerprint-1",
    identity: {
      api_version: "v1",
      read_model_version: 1,
      model_id: "model-a",
      revision: "rev-a",
      quantization: "q4",
      artifact_digest: null,
      target_id: "local",
      endpoint_identity: "loopback",
      runtime_name: "runtime-a",
      runtime_version: "1",
      hardware_device_id: "device-a",
      hardware_device_class: "cpu",
    },
    metrics: [
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
      {
        api_version: "v1",
        read_model_version: 1,
        metric_id: "latency",
        label: "Latency",
        dimension: "performance",
        availability: "available",
        value: 420,
        unit: "ms",
        higher_is_better: null,
        provenance: "client",
        protocol_version: "latency-v1",
      },
    ],
  },
  evidence: {
    api_version: "v1",
    read_model_version: 1,
    fingerprint: { fingerprint_id: "fingerprint-1", target_id: "local" },
    dataset_count: 1,
    evaluator_count: 1,
    sample_count: 20,
  },
};

describe("RunDetailView", () => {
  it("keeps quality, performance and resources as separate evidence dimensions", () => {
    const markup = renderToStaticMarkup(<RunDetailView run={run} />);

    expect(markup).toContain("Quality");
    expect(markup).toContain("Performance");
    expect(markup).toContain("Resources");
    expect(markup).toContain("Not evaluated");
  });

  it("exposes immutable evidence identity without inventing a generic verdict", () => {
    const markup = renderToStaticMarkup(<RunDetailView run={run} />);

    expect(markup).toContain("fingerprint-1");
    expect(markup).toContain("Show execution identity and fingerprint");
    expect(markup).not.toContain(">Good<");
  });
});
