import { describe, expect, it } from "vitest";

import {
  PRIMARY_NAVIGATION,
  SECONDARY_NAVIGATION,
  isSecondaryNavigationActive,
} from "./navigation";

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

  it("marks not-yet-implemented secondary surfaces as unavailable instead of inventing routes", () => {
    const pending = Object.values(SECONDARY_NAVIGATION)
      .flat()
      .filter((item) => item.href === null)
      .map((item) => item.label);

    expect(pending).toEqual([
      "Models",
      "Evaluators",
      "Evidence",
      "Evidence retention",
      "Accessibility",
    ]);
  });

  it("keeps canonical navigation active while legacy page labels remain during convergence", () => {
    const benchmarks = SECONDARY_NAVIGATION.Library.find((item) => item.label === "Benchmarks");
    const connections = SECONDARY_NAVIGATION.Settings.find(
      (item) => item.label === "Model connections",
    );

    expect(benchmarks).toBeDefined();
    expect(connections).toBeDefined();
    expect(isSecondaryNavigationActive(benchmarks!, "Test suites")).toBe(true);
    expect(isSecondaryNavigationActive(connections!, "Endpoints")).toBe(true);
  });
});
