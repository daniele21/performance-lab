import { describe, expect, it } from "vitest";

import {
  DEFAULT_CONNECTION_PREFERENCE,
  normalizeConnectionPreference,
} from "./connection-preference";

describe("connection preference", () => {
  it("keeps only a valid loopback connection preference", () => {
    expect(
      normalizeConnectionPreference({
        ...DEFAULT_CONNECTION_PREFERENCE,
        displayName: "  My server  ",
        host: "LOCALHOST",
        apiKey: "must-not-be-returned",
      }),
    ).toEqual({
      ...DEFAULT_CONNECTION_PREFERENCE,
      displayName: "My server",
      host: "localhost",
    });
  });

  it("rejects non-loopback or malformed persisted endpoints", () => {
    expect(
      normalizeConnectionPreference({
        ...DEFAULT_CONNECTION_PREFERENCE,
        host: "example.com",
      }),
    ).toBeNull();
    expect(
      normalizeConnectionPreference({
        ...DEFAULT_CONNECTION_PREFERENCE,
        port: "70000",
      }),
    ).toBeNull();
    expect(
      normalizeConnectionPreference({
        ...DEFAULT_CONNECTION_PREFERENCE,
        basePath: "/v1/?token=secret",
      }),
    ).toBeNull();
  });

  it("rejects unsupported server types and probe timeouts", () => {
    expect(
      normalizeConnectionPreference({
        ...DEFAULT_CONNECTION_PREFERENCE,
        serverType: "remote_api",
      }),
    ).toBeNull();
    expect(
      normalizeConnectionPreference({
        ...DEFAULT_CONNECTION_PREFERENCE,
        timeoutSeconds: "0",
      }),
    ).toBeNull();
  });
});
