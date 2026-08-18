import { describe, expect, it } from "vitest";

import { parseHash } from "./routing";

describe("hash routing", () => {
  it("uses Overview as the default product surface", () => {
    expect(parseHash("")).toEqual({ kind: "overview" });
    expect(parseHash("#overview")).toEqual({ kind: "overview" });
  });

  it("decodes immutable run identities from the Runs route", () => {
    expect(parseHash("#runs/run%2Fone")).toEqual({ kind: "run-detail", runId: "run/one" });
  });

  it("preserves compare context without implementing comparison semantics in routing", () => {
    expect(parseHash("#compare?run=run-1")).toEqual({ kind: "compare", runId: "run-1" });
  });

  it("keeps malformed run routes explicit", () => {
    expect(parseHash("#runs/%E0%A4%A")).toEqual({
      kind: "not-found",
      path: "runs/%E0%A4%A",
    });
  });
});
