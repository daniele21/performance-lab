import {
  AppShell,
  Button,
  Disclosure,
  PageHeader,
  SectionHeader,
  Status,
} from "../../components";
import "./find-best-setup.css";

const CAMPAIGN_STEPS = ["Use case", "Models", "Configuration search", "Campaign", "Results"] as const;

interface FindBestSetupPageProps {
  onManualTest?: () => void;
}

export function FindBestSetupPage({ onManualTest }: FindBestSetupPageProps) {
  return (
    <AppShell activePrimary="Find best setup">
      <div className="best-setup-page">
        <PageHeader
          eyebrow="Use-case optimization"
          title="Find best setup"
          description="Start from the workload you care about, evaluate model and configuration candidates against the relevant benchmark evidence, then choose the best fit for this device."
          actions={
            <Button variant="quiet" onClick={onManualTest}>
              Manual test
            </Button>
          }
        />

        <ol className="best-setup-steps" aria-label="Automatic evaluation campaign flow">
          {CAMPAIGN_STEPS.map((step, index) => (
            <li data-active={index === 0 ? "true" : undefined} key={step}>
              <span>{index + 1}</span>
              <strong>{step}</strong>
            </li>
          ))}
        </ol>

        <section className="best-setup-panel">
          <SectionHeader
            title="Choose the use case first"
            description="The application layer must own the mapping from a use case to versioned suites, dataset snapshots, evaluators and decision evidence. The browser will not invent benchmark semantics."
          />

          <div className="best-setup-status">
            <div>
              <strong>Automatic campaign setup</strong>
              <p>
                The product UX is defined here, but multi-model configuration search and campaign
                orchestration are not executable in the current backend yet.
              </p>
            </div>
            <Status tone="warning">Engine pending</Status>
          </div>

          <div className="best-setup-flow" aria-label="Best setup decision model">
            <article>
              <span>1</span>
              <div>
                <strong>Use case</strong>
                <p>Resolve the relevant benchmark suite, datasets, evaluators and evidence goals.</p>
              </div>
            </article>
            <article>
              <span>2</span>
              <div>
                <strong>Candidate models</strong>
                <p>
                  Select discovered model artifacts. Different quantizations are different model
                  candidates and keep distinct evidence identity.
                </p>
              </div>
            </article>
            <article>
              <span>3</span>
              <div>
                <strong>Configuration search</strong>
                <p>
                  Sweep supported request settings. Runtime-load settings join the search only when
                  the serving runtime exposes an explicit mutable configuration contract.
                </p>
              </div>
            </article>
            <article>
              <span>4</span>
              <div>
                <strong>Evidence campaign</strong>
                <p>
                  Each candidate configuration produces immutable runs with quality, performance
                  and resource evidence kept separate.
                </p>
              </div>
            </article>
            <article>
              <span>5</span>
              <div>
                <strong>Best-fit result</strong>
                <p>
                  Recommend a model + quantization + configuration for the selected use case while
                  preserving the trade-offs and alternatives behind the decision.
                </p>
              </div>
            </article>
          </div>

          <Disclosure summary="What remains server-owned">
            <ul className="best-setup-list">
              <li>Use-case catalog and versioned benchmark/dataset mapping.</li>
              <li>Candidate configuration generation and search strategy.</li>
              <li>Campaign scheduling, cancellation, recovery and resource ownership.</li>
              <li>Compatibility-aware aggregation and recommendation policy.</li>
            </ul>
          </Disclosure>

          <div className="best-setup-actions">
            <Button variant="primary" disabled>
              Start evaluation campaign
            </Button>
            <p>
              Disabled intentionally until the campaign engine can execute this journey end to end.
            </p>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
