export const CONNECTION_PREFERENCE_STORAGE_KEY = "performance-lab.connection-preference.v1";

export type ConnectionServerType = "local_llm_server" | "openai_compatible";

export interface ConnectionPreference {
  displayName: string;
  host: string;
  port: string;
  basePath: string;
  serverType: ConnectionServerType;
  timeoutSeconds: string;
}

export const DEFAULT_CONNECTION_PREFERENCE: ConnectionPreference = {
  displayName: "Local model server",
  host: "127.0.0.1",
  port: "1235",
  basePath: "/v1/",
  serverType: "local_llm_server",
  timeoutSeconds: "5",
};

const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "::1", "[::1]"]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function normalizeConnectionPreference(
  value: unknown,
): ConnectionPreference | null {
  if (!isRecord(value)) return null;

  const displayName =
    typeof value.displayName === "string" ? value.displayName.trim() : "";
  const host =
    typeof value.host === "string" ? value.host.trim().toLowerCase() : "";
  const port = typeof value.port === "string" ? value.port.trim() : "";
  const basePath =
    typeof value.basePath === "string" ? value.basePath.trim() : "";
  const serverType = value.serverType;
  const timeoutSeconds =
    typeof value.timeoutSeconds === "string" ? value.timeoutSeconds.trim() : "";

  const portNumber = Number(port);
  const timeoutNumber = Number(timeoutSeconds);
  const validServerType =
    serverType === "local_llm_server" || serverType === "openai_compatible";

  if (
    !displayName ||
    !LOOPBACK_HOSTS.has(host) ||
    !Number.isInteger(portNumber) ||
    portNumber < 1 ||
    portNumber > 65535 ||
    !basePath.startsWith("/") ||
    basePath.includes("?") ||
    basePath.includes("#") ||
    !validServerType ||
    !Number.isFinite(timeoutNumber) ||
    timeoutNumber < 0.1 ||
    timeoutNumber > 120
  ) {
    return null;
  }

  return {
    displayName,
    host,
    port,
    basePath,
    serverType,
    timeoutSeconds,
  };
}

export function getConnectionPreference(): ConnectionPreference | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(CONNECTION_PREFERENCE_STORAGE_KEY);
    if (!raw) return null;
    return normalizeConnectionPreference(JSON.parse(raw) as unknown);
  } catch {
    return null;
  }
}

export function setConnectionPreference(
  preference: ConnectionPreference,
): boolean {
  const normalized = normalizeConnectionPreference(preference);
  if (!normalized || typeof window === "undefined") return false;
  try {
    window.localStorage.setItem(
      CONNECTION_PREFERENCE_STORAGE_KEY,
      JSON.stringify(normalized),
    );
    return true;
  } catch {
    return false;
  }
}
