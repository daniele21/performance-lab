import { useEffect, useRef, useState } from "react";

import { getRun, listRunSamples } from "../../api";
import type { MetricReadModel, RunDetailReadModel, SampleSummaryReadModel } from "../../api";
import {
  AppShell,
  Button,
  Disclosure,
  EmptyState,
  ErrorState,
  LoadingState,
  Metric,
  MetricGroup,
  PageHeader,
  SectionHeader,
  Status,
} from "../../components";
import "../evidence-drilldown.css";
import { RunRepeatabilitySection } from "./RepeatabilitySection";
import "./run-detail.css";

interface RunDetailViewProps {
  run: RunDetailReadModel;
  onCompare?: (runId: string) => void;
}

function formatTimestamp(value: string | null) {
  if (!value) return "Not available";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString();
}

function statusTone(status: RunDetailReadModel["summary"]["status"]) {
  if (status === "succeeded") return "success" as const;
  if (status === "failed") return "error" as const;
  if (status === "cancelled") return "warning" as const;
  return "neutral" as const;
}

function sampleTone(status: SampleSummaryReadModel["status"]) {
  if (status === "succeeded") return "success" as const;
  if (status === "failed") return "error" as const;
  return "warning" as const;
}

function Metrics({
  title,
  description,
  dimension,
  metrics,
}: {
  title: string;
  description: string;
  dimension: MetricReadModel["dimension"];
  metrics: MetricReadModel[];
}) {
  const selected = metrics.filter((metric) => metric.dimension === dimension);
  return (
    <article className="run-detail__metric-dimension" data-dimension={dimension}>
      <header className="run-detail__metric-heading">
        <h3>{title}</h3>
        <p>{description}</p>
      </header>
      {selected.length ? (
        <MetricGroup label={`${title} evidence`}>
          {selected.map((metric) => (
            <Metric
              key={metric.metric_id}
              label={metric.label}
              value={metric.value}
              unit={metric.unit ?? undefined}
              dimension={metric.dimension}
              availability={metric.availability}
            />
          ))}
        </MetricGroup>
      ) : (
        <MetricGroup label={`${title} evidence`}>
          <Metric label={title} value={null} dimension={dimension} availability="not_evaluated" />
        </MetricGroup>
      )}
    </article>
  );
}

type SamplesState =
  | { status: "loading" }
  | { status: "ready"; samples: SampleSummaryReadModel[] }
  | { status: "error"; message: string };

export function RunSamplesSection({ runId }: { runId: string }) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<SamplesState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    listRunSamples(runId, { signal: controller.signal })
      .then((samples) => setState({ status: "ready", samples }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Run samples could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt, runId]);

  return (
    <section className="evidence-drilldown__section">
      <SectionHeader
        title="Samples"
        description="Each row is one immutable benchmark-case attempt contributing to this run."
      />
      {state.status === "loading" ? (
        <div className="evidence-drilldown__notice" role="status">
          <p>Loading sample evidence…</p>
        </div>
      ) : null}
      {state.status === "error" ? (
        <div className="evidence-drilldown__notice" role="alert">
          <strong>Could not load run samples</strong>
          <p>{state.message}</p>
          <div>
            <Button onClick={() => setAttempt((value) => value + 1)}>Try again</Button>
          </div>
        </div>
      ) : null}
      {state.status === "ready" && !state.samples.length ? (
        <EmptyState
          title="No sample evidence retained"
          description="This run has no retained sample attempts to inspect."
        />
      ) : null}
      {state.status === "ready" && state.samples.length ? (
        <div className="evidence-drilldown__stack">
          {state.samples.map((sample) => (
            <article
              className="evidence-drilldown__card"
              key={`${sample.task_id}:${sample.sample_id}:${sample.attempt}`}
            >
              <div className="evidence-drilldown__card-header">
                <div>
                  <h3>{sample.sample_id}</h3>
                  <p>
                    {sample.task_id} · attempt {sample.attempt}
                  </p>
                </div>
                <Status tone={sampleTone(sample.status)}>{sample.status}</Status>
              </div>
              <div className="evidence-drilldown__metadata-grid">
                <div>
                  <dl>
                    <dt>Elapsed</dt>
                    <dd>{sample.elapsed_ms.toFixed(1)} ms</dd>
                  </dl>
                </div>
                <div>
                  <dl>
                    <dt>Tokens</dt>
                    <dd>
                      {sample.input_tokens ?? "?"} in · {sample.output_tokens ?? "?"} out
                    </dd>
                  </dl>
                </div>
                <div>
                  <dl>
                    <dt>Evidence</dt>
                    <dd>
                      {sample.score_count} scores · {sample.measurement_count} measurements
                    </dd>
                  </dl>
                </div>
              </div>
              <a
                className="evidence-drilldown__link"
                href={`#runs/${encodeURIComponent(runId)}/samples/${encodeURIComponent(sample.task_id)}/${encodeURIComponent(sample.sample_id)}/${sample.attempt}`}
              >
                Inspect sample evidence
              </a>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}

export function RunDetailView({ run, onCompare }: RunDetailViewProps) {
  const { summary, evidence } = run;
  const identity = summary.identity;
  const evidenceRef = useRef<HTMLElement>(null);

  const inspectEvidence = () => {
    evidenceRef.current?.scrollIntoView({ block: "start" });
    evidenceRef.current?.focus();
  };

  return (
    <AppShell activePrimary="Runs">
      <div className="run-detail">
        <a className="run-detail__back" href="#runs">
          ← Back to runs
        </a>
        <PageHeader
          eyebrow={`${summary.suite_id} · v${summary.suite_version}`}
          title={identity.model_id}
          description={`${identity.hardware_device_id ?? identity.hardware_device_class ?? identity.target_id} · ${identity.runtime_name ?? "Runtime unknown"} · Completed ${formatTimestamp(summary.completed_at)}`}
          actions={
            <div className="run-detail__actions">
              <Button variant="primary" onClick={inspectEvidence}>
                Inspect evidence
              </Button>
              <Button variant="secondary" onClick={() => onCompare?.(summary.run_id)}>
                Compare
              </Button>
            </div>
          }
        />

        <div className="run-detail__status-row">
          <Status tone={statusTone(summary.status)}>{summary.status}</Status>
          <code>{summary.run_id}</code>
        </div>

        <section className="run-detail__metric-panel" aria-label="Run evidence">
          <SectionHeader
            title="Run evidence"
            description="Exact quality, performance and resource evidence for this execution identity."
          />
          <div className="run-detail__metric-grid">
            <Metrics
              title="Quality"
              description="Evaluator-owned scores."
              dimension="quality"
              metrics={summary.metrics}
            />
            <Metrics
              title="Performance"
              description="Latency and throughput for this execution."
              dimension="performance"
              metrics={summary.metrics}
            />
            <Metrics
              title="Resources"
              description="Observed resources; missing telemetry stays not evaluated."
              dimension="resources"
              metrics={summary.metrics}
            />
          </div>
        </section>

        <RunRepeatabilitySection runId={summary.run_id} />

        <RunSamplesSection runId={summary.run_id} />

        <section
          className="run-detail__evidence"
          ref={evidenceRef}
          tabIndex={-1}
          aria-label="Run evidence and reproducibility"
        >
          <SectionHeader
            title="Evidence & reproducibility"
            description="The immutable execution identity behind the result."
          />
          <div className="run-detail__evidence-summary">
            <div>
              <span>Fingerprint</span>
              <code>{summary.fingerprint_id}</code>
            </div>
            <div>
              <span>Datasets</span>
              <strong>{evidence.dataset_count}</strong>
            </div>
            <div>
              <span>Evaluators</span>
              <strong>{evidence.evaluator_count}</strong>
            </div>
            <div>
              <span>Samples</span>
              <strong>{evidence.sample_count}</strong>
            </div>
          </div>

          <Disclosure summary="Show execution identity and fingerprint">
            <dl className="run-detail__identity-grid">
              <div>
                <dt>Model revision</dt>
                <dd>{identity.revision ?? "Unknown"}</dd>
              </div>
              <div>
                <dt>Quantization</dt>
                <dd>{identity.quantization ?? "Unknown"}</dd>
              </div>
              <div>
                <dt>Endpoint identity</dt>
                <dd>{identity.endpoint_identity}</dd>
              </div>
              <div>
                <dt>Runtime version</dt>
                <dd>{identity.runtime_version ?? "Unknown"}</dd>
              </div>
            </dl>
            <pre className="run-detail__fingerprint">
              {JSON.stringify(evidence.fingerprint, null, 2)}
            </pre>
          </Disclosure>
        </section>
      </div>
    </AppShell>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; run: RunDetailReadModel }
  | { status: "error"; message: string };

export function RunDetailPage({
  runId,
  onCompare,
}: {
  runId: string;
  onCompare?: (runId: string) => void;
}) {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    getRun(runId, { signal: controller.signal })
      .then((run) => setState({ status: "ready", run }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Run evidence could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt, runId]);

  if (state.status === "loading") {
    return (
      <AppShell activePrimary="Runs">
        <LoadingState
          title="Loading run evidence"
          description="Reading the immutable run and fingerprint from local storage."
        />
      </AppShell>
    );
  }

  if (state.status === "error") {
    return (
      <AppShell activePrimary="Runs">
        <ErrorState
          title="Could not load this run"
          description={state.message}
          action={<Button onClick={() => setAttempt((value) => value + 1)}>Try again</Button>}
        />
      </AppShell>
    );
  }

  return <RunDetailView run={state.run} onCompare={onCompare} />;
}
