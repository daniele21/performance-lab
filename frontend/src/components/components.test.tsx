import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import {
  Button,
  CompatibilitySummary,
  DataTable,
  Delta,
  EvidenceState,
  Field,
  Metric,
  Progress,
  StateSurface,
  Toggle,
} from ".";

describe("design system primitives", () => {
  it("keeps native disabled button semantics", () => {
    const markup = renderToStaticMarkup(<Button disabled>Run test</Button>);
    expect(markup).toContain("disabled");
    expect(markup).toContain("Run test");
  });

  it("renders unavailable evidence explicitly instead of inventing a zero", () => {
    const markup = renderToStaticMarkup(
      <Metric
        label="Peak memory"
        dimension="resources"
        availability="unavailable"
        value={null}
        unit="MiB"
      />,
    );

    expect(markup).toContain("Unavailable");
    expect(markup).not.toContain(">0 MiB<");
  });

  it("does not rely on color alone for evidence state meaning", () => {
    const markup = renderToStaticMarkup(<EvidenceState state="not_evaluated" />);
    expect(markup).toContain("Not evaluated");
  });

  it("links field errors to native input semantics", () => {
    const markup = renderToStaticMarkup(<Field label="Endpoint" error="Connection failed" />);
    expect(markup).toContain('aria-invalid="true"');
    expect(markup).toContain("Connection failed");
  });

  it("uses switch semantics for binary controls", () => {
    const markup = renderToStaticMarkup(<Toggle label="Enable telemetry" onChange={vi.fn()} />);
    expect(markup).toContain('role="switch"');
  });

  it("foregrounds non-comparability and the reason", () => {
    const markup = renderToStaticMarkup(
      <CompatibilitySummary
        comparable={false}
        reasons={[{ code: "hardware", message: "Hardware identity differs" }]}
      />,
    );
    expect(markup).toContain("Not comparable");
    expect(markup).toContain("Metric deltas are hidden");
    expect(markup).toContain("Hardware identity differs");
  });

  it("keeps unavailable deltas explicit", () => {
    const markup = renderToStaticMarkup(<Delta label="Latency" value={null} unit="ms" />);
    expect(markup).toContain("Latency: unavailable");
  });

  it("renders native progress semantics", () => {
    const markup = renderToStaticMarkup(<Progress label="Evaluating" value={50} />);
    expect(markup).toContain("<progress");
    expect(markup).toContain('value="50"');
  });

  it("renders an explicit empty row when a data table has no evidence", () => {
    const markup = renderToStaticMarkup(
      <DataTable<{ id: string }>
        caption="Runs"
        columns={[{ id: "id", header: "Run", render: (row) => row.id }]}
        rows={[]}
        rowKey={(row) => row.id}
      />,
    );
    expect(markup).toContain("No evidence available.");
  });

  it("announces loading state politely", () => {
    const markup = renderToStaticMarkup(
      <StateSurface kind="loading" title="Loading runs" description="Reading evidence." />,
    );
    expect(markup).toContain('role="status"');
    expect(markup).toContain('aria-live="polite"');
    expect(markup).toContain('aria-atomic="true"');
  });

  it("announces recoverable errors assertively", () => {
    const markup = renderToStaticMarkup(
      <StateSurface kind="error" title="Could not load runs" description="Try again." />,
    );
    expect(markup).toContain('role="alert"');
    expect(markup).toContain('aria-live="assertive"');
    expect(markup).toContain('aria-atomic="true"');
  });
});
