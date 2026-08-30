import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { Field, Select } from "./Field";

describe("form field accessibility", () => {
  it("keeps input descriptions out of the accessible label", () => {
    const markup = renderToStaticMarkup(
      <Field label="Host" description="Loopback only" defaultValue="127.0.0.1" />,
    );

    expect(markup).toContain('<label class="field__label" for="field-host">Host</label>');
    expect(markup).toContain('id="field-host-description"');
    expect(markup).toContain('aria-describedby="field-host-description"');
    expect(markup).not.toContain('<label class="field"');
  });

  it("keeps select descriptions out of the accessible label", () => {
    const markup = renderToStaticMarkup(
      <Select label="Model" description="1 model reported by the server." defaultValue="model-a">
        <option value="model-a">model-a</option>
      </Select>,
    );

    expect(markup).toContain('<label class="field__label" for="select-model">Model</label>');
    expect(markup).toContain('id="select-model-description"');
    expect(markup).toContain('aria-describedby="select-model-description"');
    expect(markup).not.toContain('<label class="field"');
  });
});
