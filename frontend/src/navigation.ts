export const PRIMARY_NAVIGATION = [
  "Overview",
  "Find best setup",
  "Test a model",
  "Runs",
  "Compare",
] as const;

export interface SecondaryNavigationItem {
  label: string;
  href: string | null;
  activeAliases?: readonly string[];
  disabledReason?: string;
}

export const SECONDARY_NAVIGATION = {
  Library: [
    {
      label: "Models",
      href: null,
      disabledReason: "Model registry surface is pending a complete model inventory contract.",
    },
    { label: "Benchmarks", href: "#benchmarks" },
    { label: "Datasets", href: "#datasets" },
    { label: "Evaluators", href: "#evaluators" },
    {
      label: "Evidence",
      href: null,
      disabledReason: "Evidence repository surface is pending its dedicated read model.",
    },
    { label: "Baselines", href: "#baselines" },
    { label: "Regression policies", href: "#regression-policies" },
  ],
  Settings: [
    { label: "Model connections", href: "#model-connections" },
    { label: "Devices / targets", href: "#devices-targets" },
    {
      label: "Evidence retention",
      href: null,
      disabledReason: "Evidence retention controls are not implemented yet.",
    },
    {
      label: "Accessibility",
      href: null,
      disabledReason: "Accessibility preferences are not implemented yet.",
    },
    { label: "Advanced", href: "#advanced" },
  ],
} as const satisfies Record<string, readonly SecondaryNavigationItem[]>;

export function isSecondaryNavigationActive(
  item: SecondaryNavigationItem,
  activeLabel: string | undefined,
): boolean {
  if (activeLabel === undefined) return false;
  return item.label === activeLabel || (item.activeAliases?.includes(activeLabel) ?? false);
}
