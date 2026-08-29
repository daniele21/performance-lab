export const PRIMARY_NAVIGATION = [
  "Overview",
  "Find best setup",
  "Test a model",
  "Runs",
  "Compare",
] as const;

export const SECONDARY_NAVIGATION = {
  Library: ["Test suites", "Datasets", "Baselines", "Regression policies"],
  Settings: ["Endpoints", "Devices / targets", "Advanced"],
} as const;
