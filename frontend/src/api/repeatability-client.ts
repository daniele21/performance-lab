import { ApiError } from "./client";
import type { RepeatabilityReadModel } from "./repeatability-types";

interface RequestOptions {
  signal?: AbortSignal;
}

async function readError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string" && payload.detail.trim())
      return payload.detail;
  } catch {
    // Fall through to the stable status-based message.
  }
  return `Performance Lab API request failed (${response.status})`;
}

export async function getRunRepeatability(
  runId: string,
  options: RequestOptions = {},
): Promise<RepeatabilityReadModel> {
  const response = await fetch(
    `/api/v1/runs/${encodeURIComponent(runId)}/repeatability`,
    {
      method: "GET",
      headers: { Accept: "application/json" },
      signal: options.signal,
    },
  );
  if (!response.ok) throw new ApiError(response.status, await readError(response));
  return (await response.json()) as RepeatabilityReadModel;
}
