import { describe, expect, it } from "vitest";

import { PRIMARY_NAVIGATION, SECONDARY_NAVIGATION } from "./navigation";

describe("product navigation contract", () => {
  it("keeps the task-model-first primary navigation stable", () => {
    expect(PRIMARY_NAVIGATION).toEqual(["Overview", "Test a model", "Runs", "Compare"]);
  });

  it("keeps expert benchmark concepts out of primary navigation", () => {
    const secondaryItems = Object.values(SECONDARY_NAVIGATION).flat();

    expect(secondaryItems).toContain("Datasets");
    expect(secondaryItems).toContain("Regression policies");
    expect(PRIMARY_NAVIGATION).not.toContain("Datasets");
  });
});
