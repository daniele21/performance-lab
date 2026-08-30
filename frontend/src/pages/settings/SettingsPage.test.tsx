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
  it("uses canonical Model connections language without taking runtime ownership", () => {
    const markup = renderToStaticMarkup(
      <SettingsView section="model-connections" targets={[target]} />,
    );

    expect(markup).toContain("Model connections");
    expect(markup).toContain("local-phone");
    expect(markup).toContain("safe-endpoint-id");
    expect(markup).toContain("without taking ownership of model loading or runtime lifecycle");
    expect(markup).not.toContain(">Endpoints<");
  });

  it("keeps advanced capabilities read-only and does not infer missing hardware", () => {
    const markup = renderToStaticMarkup(<SettingsView section="advanced" targets={[target]} />);

    expect(markup).toContain("Runtime ownership");
    expect(markup).toContain("External");
    expect(markup).toContain("Unknown capabilities remain unknown");
  });
});
