import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type { TargetSummaryReadModel } from "../../api";
import { SettingsView } from "./SettingsPage";

const target: TargetSummaryReadModel = {
  api_version: "v1",
  read_model_version: 1,
  target_id: "android-a56",
  display_name: "Samsung A56",
  adapter_type: "openai-compatible",
  endpoint_profile_id: "local-phone",
  endpoint_identity: "safe-endpoint-id",
  capabilities: ["streaming", "temperature"],
};

describe("SettingsView", () => {
  it("shows endpoint identity without taking runtime ownership", () => {
    const markup = renderToStaticMarkup(<SettingsView section="endpoints" targets={[target]} />);

    expect(markup).toContain("local-phone");
    expect(markup).toContain("safe-endpoint-id");
    expect(markup).toContain("serving/runtime ownership outside the product core");
  });

  it("keeps advanced capabilities read-only and does not infer missing hardware", () => {
    const markup = renderToStaticMarkup(<SettingsView section="advanced" targets={[target]} />);

    expect(markup).toContain("Runtime ownership");
    expect(markup).toContain("External");
    expect(markup).toContain("Unknown capabilities remain unknown");
  });
});
