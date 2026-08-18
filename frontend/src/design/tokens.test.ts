import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

import { BRAND_CONTRACT_VERSION, COLOR_TOKENS } from "./tokens";

interface BrandKit {
  contract_version: string;
  tokens: {
    colors: Record<string, string>;
  };
}

describe("semantic design tokens", () => {
  it("stays synchronized with the canonical brand kit", () => {
    const source = new URL("../../../design/brand-kit.json", import.meta.url);
    const brandKit = JSON.parse(readFileSync(source, "utf8")) as BrandKit;

    expect(BRAND_CONTRACT_VERSION).toBe(brandKit.contract_version);
    expect(COLOR_TOKENS).toEqual(brandKit.tokens.colors);
  });
});
