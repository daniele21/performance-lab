import { afterEach, describe, expect, it, vi } from "vitest";

import { getRunRepeatability } from "./repeatability-client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("repeatability API client", () => {
  it("uses the versioned exact-run endpoint and URL-encodes the run identity", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ anchor_run_id: "run/one" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await getRunRepeatability("run/one");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/runs/run%2Fone/repeatability",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("preserves the API detail for a missing retained run", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "completed run not found" }), {
          status: 404,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(getRunRepeatability("missing")).rejects.toEqual(
      expect.objectContaining({
        name: "ApiError",
        status: 404,
        message: "completed run not found",
      }),
    );
  });
});
