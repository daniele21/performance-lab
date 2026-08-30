import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getBenchmark,
  getRun,
  getSampleEvidence,
  listBenchmarks,
  listEvaluators,
  listRuns,
  listRunSamples,
} from "./client";
import type { ApiError } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("Performance Lab API client", () => {
  it("uses the versioned run endpoint and URL-encodes the run identity", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ summary: { run_id: "run/one" } }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await getRun("run/one");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/runs/run%2Fone",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("keeps list pagination explicit in the request", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response("[]", {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await listRuns({ offset: 25, limit: 25 });

    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/runs?offset=25&limit=25");
  });

  it("uses canonical benchmark and evaluator Library endpoints", async () => {
    const fetchMock = vi.fn().mockImplementation(async () => {
      return new Response("[]", {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    await listBenchmarks();
    await listEvaluators();

    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual([
      "/api/v1/benchmarks",
      "/api/v1/evaluators",
    ]);
  });

  it("uses canonical benchmark and sample drilldown endpoints with encoded identities", async () => {
    const fetchMock = vi.fn().mockImplementation(async () => {
      return new Response("{}", {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    await getBenchmark("suite/one", "1.0");
    await listRunSamples("run/one");
    await getSampleEvidence("run/one", "task/one", "sample/one", 2);

    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual([
      "/api/v1/benchmarks/suite%2Fone/1.0",
      "/api/v1/runs/run%2Fone/samples",
      "/api/v1/runs/run%2Fone/samples/task%2Fone/sample%2Fone/2",
    ]);
  });

  it("turns typed API failures into an actionable ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "completed run not found" }), {
          status: 404,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(getRun("missing")).rejects.toEqual(
      expect.objectContaining<ApiError>({
        name: "ApiError",
        status: 404,
        message: "completed run not found",
      }),
    );
  });
});
