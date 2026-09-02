export const THEME_STORAGE_KEY = "performance-lab.theme";

export type ThemePreference = "light" | "dark" | "system";

export function normalizeThemePreference(value: unknown): ThemePreference {
  return value === "dark" || value === "system" ? value : "light";
}

export function getThemePreference(): ThemePreference {
  if (typeof window === "undefined") return "light";
  try {
    return normalizeThemePreference(window.localStorage.getItem(THEME_STORAGE_KEY));
  } catch {
    return "light";
  }
}

export function applyThemePreference(preference: ThemePreference): void {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = preference;
}

export function setThemePreference(preference: ThemePreference): void {
  applyThemePreference(preference);
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, preference);
  } catch {
    // A blocked storage API must not prevent the local appearance change.
  }
}
