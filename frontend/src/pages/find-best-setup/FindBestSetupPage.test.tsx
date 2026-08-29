import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { FindBestSetupPage } from "./FindBestSetupPage";

describe("FindBestSetupPage", () => {
  it("models the use-case-first campaign without pretending the engine exists", () => {
    const markup = renderToStaticMarkup(<FindBestSetupPage />);

    expect(markup).toContain("Find best setup");
    expect(markup).toContain("Use case");
    expect(markup).toContain("Candidate models");
    expect(markup).toContain("Different quantizations");
    expect(markup).toContain("Configuration search");
    expect(markup).toContain("Evidence campaign");
    expect(markup).toContain("Best-fit result");
    expect(markup).toContain("Engine pending");
    expect(markup).toContain("disabled");
  });
});
