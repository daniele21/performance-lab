import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { RunSummaryReadModel } from "../../api";
import { RunsView } from "./RunsPage";

const run: RunSummaryReadModel = {
  api_version: "v1",
  read_model_version: 1,
  run_id: "run/one",
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
  metrics: [],
};

describe("RunsView", () => {
  it("links immutable run rows to their detail route", () => {
    const markup = renderToStaticMarkup(<RunsView runs={[run]} offset={0} canLoadMore={false} />);

    expect(markup).toContain('href="#runs/run%2Fone"');
    expect(markup).toContain("run/one");
    expect(markup).toContain("device-a");
  });

  it("renders the explicit empty evidence state", () => {
    const markup = renderToStaticMarkup(<RunsView runs={[]} offset={0} canLoadMore={false} />);

    expect(markup).toContain("No completed runs yet");
  });
});
