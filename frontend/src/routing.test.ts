import { describe, expect, it } from "vitest";

import { parseHash } from "./routing";

describe("hash routing", () => {
  it("uses Overview as the default product surface", () => {
    expect(parseHash("")).toEqual({ kind: "overview" });
    expect(parseHash("#overview")).toEqual({ kind: "overview" });
  });

  it("routes the use-case-first best setup journey explicitly", () => {
    expect(parseHash("#find-best-setup")).toEqual({ kind: "best-setup" });
  });

  it("keeps campaign identity in a refresh-safe campaign route", () => {
    expect(parseHash("#campaigns/campaign%2Fone")).toEqual({
      kind: "campaign",
      campaignId: "campaign/one",
    });
  });

  it("routes one exact campaign benchmark case without changing evidence identity", () => {
    expect(parseHash("#campaigns/campaign%2Fone/cases/task%2Fone/sample%2Fone")).toEqual({
      kind: "campaign-case-comparison",
      campaignId: "campaign/one",
      taskId: "task/one",
      sampleId: "sample/one",
    });
  });

  it("decodes immutable run identities from the Runs route", () => {
    expect(parseHash("#runs/run%2Fone")).toEqual({ kind: "run-detail", runId: "run/one" });
  });

  it("routes one immutable sample attempt under its run", () => {
    expect(parseHash("#runs/run%2Fone/samples/task%2Fone/sample%2Fone/2")).toEqual({
      kind: "sample-evidence",
      runId: "run/one",
      taskId: "task/one",
      sampleId: "sample/one",
      attempt: 2,
    });
  });

  it("keeps server-owned job identity in a refresh-safe Live Run route", () => {
    expect(parseHash("#live-run/job%2Fone")).toEqual({ kind: "live-run", jobId: "job/one" });
  });

  it("preserves compare context without implementing comparison semantics in routing", () => {
    expect(parseHash("#compare?run=run-1")).toEqual({ kind: "compare", runId: "run-1" });
  });

  it("routes benchmark definition identity without mixing result context", () => {
    expect(parseHash("#benchmarks/suite%2Fone/1.0")).toEqual({
      kind: "benchmark-detail",
      suiteId: "suite/one",
      suiteVersion: "1.0",
    });
  });

  it("routes canonical secondary destinations to canonical page owners", () => {
    expect(parseHash("#benchmarks")).toEqual({ kind: "library", section: "benchmarks" });
    expect(parseHash("#evaluators")).toEqual({ kind: "library", section: "evaluators" });
    expect(parseHash("#model-connections")).toEqual({
      kind: "settings",
      section: "model-connections",
    });
    expect(parseHash("#datasets")).toEqual({ kind: "library", section: "datasets" });
    expect(parseHash("#devices-targets")).toEqual({
      kind: "settings",
      section: "devices-targets",
    });
  });

  it("preserves legacy deep links by resolving them to canonical owners", () => {
    expect(parseHash("#test-suites")).toEqual({ kind: "library", section: "benchmarks" });
    expect(parseHash("#endpoints")).toEqual({
      kind: "settings",
      section: "model-connections",
    });
    expect(parseHash("#regression-policies")).toEqual({
      kind: "library",
      section: "regression-policies",
    });
  });

  it("keeps unavailable canonical surfaces explicit instead of routing them to wrong owners", () => {
    expect(parseHash("#models")).toEqual({ kind: "not-found", path: "models" });
    expect(parseHash("#evidence")).toEqual({ kind: "not-found", path: "evidence" });
    expect(parseHash("#evidence-retention")).toEqual({
      kind: "not-found",
      path: "evidence-retention",
    });
  });

  it("keeps malformed run and campaign routes explicit", () => {
    expect(parseHash("#runs/%E0%A4%A")).toEqual({
      kind: "not-found",
      path: "runs/%E0%A4%A",
    });
    expect(parseHash("#campaigns/%E0%A4%A")).toEqual({
      kind: "not-found",
      path: "campaigns/%E0%A4%A",
    });
    expect(parseHash("#campaigns/campaign/cases/%E0%A4%A/sample")).toEqual({
      kind: "not-found",
      path: "campaigns/campaign/cases/%E0%A4%A/sample",
    });
    expect(parseHash("#live-run/%E0%A4%A")).toEqual({
      kind: "not-found",
      path: "live-run/%E0%A4%A",
    });
    expect(parseHash("#runs/run-1/samples/task/sample/0")).toEqual({
      kind: "not-found",
      path: "runs/run-1/samples/task/sample/0",
    });
  });
});
