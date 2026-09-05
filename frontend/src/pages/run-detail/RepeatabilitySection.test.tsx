import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { RepeatabilityReadModel } from "../../api";
import { RepeatabilityEvidenceView } from "./RepeatabilitySection";

const identity = { api_version: "v1", read_model_version: 1 } as const;

const available: RepeatabilityReadModel = {
  ...identity,
  anchor_run_id: "run-2",
  fingerprint_id: "f".repeat(64),
  state: "available",
  load_profile: {
    concurrency: 1,
    request_count: 4,
    warmup_requests: 0,
    streaming: false,
  },
  run_ids: ["run-1", "run-2", "run-failed"],
  run_count: 3,
  succeeded_run_count: 2,
  failed_run_count: 1,
  cancelled_run_count: 0,
  sample_attempt_count: 9,
  succeeded_sample_count: 7,
  failed_sample_count: 2,
  cancelled_sample_count: 0,
  note: "Failures remain in the cohort denominators and are not converted to zero.",
  metrics: [
    {
      ...identity,
      metric_id: "total_latency_ms|client|single-request-v1|ms",
      label: "total_latency_ms",
      dimension: "performance",
      unit: "ms",
      higher_is_better: null,
      run_values: [
        { ...identity, run_id: "run-1", value: 100, source_sample_count: 4 },
        { ...identity, run_id: "run-2", value: 120, source_sample_count: 3 },
      ],
      distribution: {
        ...identity,
        sample_count: 2,
        minimum: 100,
        maximum: 120,
        mean: 110,
        median: 110,
        stddev: 10,
        coefficient_of_variation: 0.0909,
        p90: {
          ...identity,
          percentile: 90,
          value: null,
          sample_count: 2,
          qualified: false,
          qualification: "requires at least 10 samples; only 2 available",
        },
        p95: {
          ...identity,
          percentile: 95,
          value: null,
          sample_count: 2,
          qualified: false,
          qualification: "requires at least 20 samples; only 2 available",
        },
      },
    },
  ],
};

describe("RepeatabilityEvidenceView", () => {
  it("shows exact-fingerprint denominators and qualified variability without a verdict", () => {
    const markup = renderToStaticMarkup(<RepeatabilityEvidenceView evidence={available} />);

    expect(markup).toContain("Evidence available");
    expect(markup).toContain("3 exact-fingerprint runs");
    expect(markup).toContain("Concurrency 1 · 4 measured requests · 0 warmups · non-streaming");
    expect(markup).toContain("2 succeeded · 1 failed · 0 cancelled");
    expect(markup).toContain("Show run-to-run variability");
    expect(markup).toContain("requires at least 10 samples; only 2 available");
    expect(markup).not.toContain(">Stable<");
    expect(markup).not.toContain(">Good<");
  });

  it("keeps a single retained run explicitly insufficient", () => {
    const insufficient: RepeatabilityReadModel = {
      ...available,
      anchor_run_id: "run-1",
      state: "insufficient_repeats",
      run_ids: ["run-1"],
      run_count: 1,
      succeeded_run_count: 1,
      failed_run_count: 0,
      sample_attempt_count: 4,
      succeeded_sample_count: 4,
      failed_sample_count: 0,
      note: "Only one exact-fingerprint Run is retained. Repeat this exact frozen test.",
      metrics: [],
    };

    const markup = renderToStaticMarkup(<RepeatabilityEvidenceView evidence={insufficient} />);

    expect(markup).toContain("Insufficient repeats");
    expect(markup).toContain("1 exact-fingerprint run");
    expect(markup).toContain("Repeat this exact frozen test");
    expect(markup).not.toContain("Show run-to-run variability");
  });
});
