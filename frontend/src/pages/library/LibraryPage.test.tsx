import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type {
  BaselineSummaryReadModel,
  DatasetSummaryReadModel,
  EvaluatorDefinitionReadModel,
  PolicySummaryReadModel,
  SuiteSummaryReadModel,
} from "../../api";
import { LibraryView } from "./LibraryPage";

const benchmark: SuiteSummaryReadModel = {
  api_version: "v1",
  read_model_version: 1,
  suite_id: "starter",
  suite_version: "1",
  task_count: 2,
  task_ids: ["qa", "reasoning"],
};

const dataset: DatasetSummaryReadModel = {
  api_version: "v1",
  read_model_version: 1,
  dataset_id: "dataset-a",
  dataset_version: "2026-08",
  source: "fixture",
  split: "test",
  sample_count: 12,
  selection_policy: "frozen",
  content_sha256: "a".repeat(64),
};

const evaluator: EvaluatorDefinitionReadModel = {
  api_version: "v1",
  read_model_version: 1,
  evaluator_id: "exact-match",
  version: "1",
  evaluator_type: "deterministic",
  deterministic: true,
  explanation_supported: false,
  rule_summary: "Exact normalized match",
  configuration: {},
};

const baseline: BaselineSummaryReadModel = {
  api_version: "v1",
  read_model_version: 1,
  baseline_id: "baseline-a",
  run_id: "run-a",
  fingerprint_id: "fp-a",
  selected_at: "2026-08-23T18:00:00Z",
  label: "Release baseline",
};

const policy: PolicySummaryReadModel = {
  api_version: "v1",
  read_model_version: 1,
  policy_id: "policy-a",
  policy_version: "1",
  rule_count: 3,
};

const data = {
  benchmarks: [benchmark],
  datasets: [dataset],
  evaluators: [evaluator],
  baselines: [baseline],
  policies: [policy],
};

describe("LibraryView", () => {
  it("uses benchmark terminology and keeps definition separate from Run results", () => {
    const markup = renderToStaticMarkup(<LibraryView section="benchmarks" data={data} />);

    expect(markup).toContain("Benchmarks");
    expect(markup).toContain("starter");
    expect(markup).toContain("Execution results remain separate immutable Run evidence");
    expect(markup).not.toContain("Test suites");
  });

  it("keeps dataset snapshot provenance visible", () => {
    const markup = renderToStaticMarkup(<LibraryView section="datasets" data={data} />);

    expect(markup).toContain("dataset-a");
    expect(markup).toContain("fixture");
    expect(markup).toContain("frozen");
    expect(markup).toContain("aaaaaaaaaaaa…");
  });

  it("shows evaluator rules without inventing a global weight", () => {
    const markup = renderToStaticMarkup(<LibraryView section="evaluators" data={data} />);

    expect(markup).toContain("exact-match");
    expect(markup).toContain("Exact normalized match");
    expect(markup).toContain("Weights are contextual, never global");
    expect(markup).not.toContain("Default weight");
  });

  it("shows explicit immutable baseline identity rather than inventing one", () => {
    const markup = renderToStaticMarkup(<LibraryView section="baselines" data={data} />);

    expect(markup).toContain("Release baseline");
    expect(markup).toContain("run-a");
    expect(markup).toContain("fp-a");
    expect(markup).not.toContain("Recommended baseline");
  });
});
