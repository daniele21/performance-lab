import { useEffect, useRef, useState } from "react";

import { getRun } from "../../api";
import type { MetricReadModel, RunDetailReadModel } from "../../api";
import {
  AppShell,
  Button,
  Disclosure,
  ErrorState,
  LoadingState,
  Metric,
  MetricGroup,
  PageHeader,
  SectionHeader,
  Status,
} from "../../components";
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
    <section className="run-detail__metric-section">
      <SectionHeader title={title} description={description} />
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

        <Metrics
          title="Quality"
          description="Evaluator-owned quality scores. No generic good/bad label is inferred without an explicit policy."
          dimension="quality"
          metrics={summary.metrics}
        />
        <Metrics
          title="Performance"
          description="Client-observed latency and throughput evidence for this exact execution identity."
          dimension="performance"
          metrics={summary.metrics}
        />
        <Metrics
          title="Resources"
          description="Host/runtime resource evidence. Missing telemetry remains explicitly not evaluated."
          dimension="resources"
          metrics={summary.metrics}
        />

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
