import { describe, expect, it } from "vitest";

import { PRIMARY_NAVIGATION, SECONDARY_NAVIGATION } from "./navigation";

describe("product navigation contract", () => {
  it("keeps the use-case-first decision journey in primary navigation", () => {
    expect(PRIMARY_NAVIGATION).toEqual([
      "Overview",
      "Find best setup",
      "Test a model",
      "Runs",
      "Compare",
    ]);
  });

  it("keeps the complete canonical Library and Settings IA secondary", () => {
    expect(SECONDARY_NAVIGATION.Library.map((item) => item.label)).toEqual([
      "Models",
      "Benchmarks",
      "Datasets",
      "Evaluators",
      "Evidence",
      "Baselines",
      "Regression policies",
    ]);
    expect(SECONDARY_NAVIGATION.Settings.map((item) => item.label)).toEqual([
      "Model connections",
      "Devices / targets",
      "Evidence retention",
      "Accessibility",
      "Advanced",
    ]);
    expect(PRIMARY_NAVIGATION).not.toContain("Datasets");
  });

  it("keeps only genuinely unimplemented secondary surfaces unavailable", () => {
    const pending = Object.values(SECONDARY_NAVIGATION)
      .flat()
      .filter((item) => item.href === null)
      .map((item) => item.label);

    expect(pending).toEqual(["Models", "Evidence", "Evidence retention", "Accessibility"]);
  });

  it("exposes canonical routes for integrated Library and Settings owners", () => {
    expect(SECONDARY_NAVIGATION.Library.find((item) => item.label === "Benchmarks")?.href).toBe(
      "#benchmarks",
    );
    expect(SECONDARY_NAVIGATION.Library.find((item) => item.label === "Evaluators")?.href).toBe(
      "#evaluators",
    );
    expect(
      SECONDARY_NAVIGATION.Settings.find((item) => item.label === "Model connections")?.href,
    ).toBe("#model-connections");
  });
});
