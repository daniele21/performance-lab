import { AppShell, Button, PageHeader, Status } from "./components";
import "./foundation.css";

export function App() {
  return (
    <AppShell activePrimary="Overview">
      <div className="product-intro">
        <PageHeader
          eyebrow="UIK-001 · design system"
          title="Performance Lab"
          description="The product shell now consumes executable semantic tokens and reusable primitives. Product pages will compose these primitives against versioned application read models."
          actions={<Button variant="primary">Test a model</Button>}
        />

        <section className="product-intro__status" aria-labelledby="design-system-status-title">
          <Status tone="success">Semantic token foundation active</Status>
          <h2 id="design-system-status-title">Primitive slice ready for product composition</h2>
          <p>
            Navigation, page hierarchy, actions, evidence states, metrics and recovery surfaces now
            share one semantic system rather than page-specific styles.
          </p>
        </section>
      </div>
    </AppShell>
  );
}
