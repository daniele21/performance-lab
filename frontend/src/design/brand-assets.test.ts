import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

function read(relative: string) {
  return readFileSync(new URL(relative, import.meta.url), "utf8");
}

describe("Performance Lab brand assets", () => {
  it("keeps the shipped compact mark synchronized with the canonical asset", () => {
    const canonicalMark = read("../../../docs/assets/brand/mark.svg");
    const shippedMark = read("../assets/brand/mark.svg");

    expect(shippedMark).toBe(canonicalMark);
    expect(canonicalMark).toContain("Performance Lab mark");
    expect(canonicalMark).not.toContain("AI Performance Lab");
  });

  it("uses the canonical product name and decision-oriented tagline", () => {
    const lockup = read("../../../docs/assets/brand/logo-lockup.svg");

    expect(lockup).toContain(">Performance Lab</text>");
    expect(lockup).toContain("MEASURE. COMPARE. DECIDE.");
    expect(lockup).not.toContain("AI Performance Lab");
    expect(lockup).not.toContain("IMPROVE");
  });
});
