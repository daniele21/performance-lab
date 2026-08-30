import { useEffect, useState } from "react";

import { getSampleEvidence } from "../../api";
import type {
  EvidenceContentReadModel,
  SampleEvidenceDetailReadModel,
  SampleSummaryReadModel,
} from "../../api";
import {
  AppShell,
  Button,
  Disclosure,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  SectionHeader,
  Status,
} from "../../components";
import "../evidence-drilldown.css";

function renderValue(value: unknown) {
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

function sampleTone(status: SampleSummaryReadModel["status"]) {
  if (status === "succeeded") return "success" as const;
  if (status === "failed") return "error" as const;
  return "warning" as const;
}

function ContentPanel({ label, evidence }: { label: string; evidence: EvidenceContentReadModel }) {
  if (evidence.state === "retained") {
    return (
      <div className="evidence-drilldown__panel">
        <span className="evidence-drilldown__panel-label">{label}</span>
        <pre className="evidence-drilldown__pre">{renderValue(evidence.content)}</pre>
      </div>
    );
  }

  const title = evidence.state === "not_retained" ? "Content not retained" : "Content unavailable";
  return (
    <div className="evidence-drilldown__panel">
      <span className="evidence-drilldown__panel-label">{label}</span>
      <Status tone="unknown">{title}</Status>
      <p className="evidence-drilldown__muted">
        {evidence.reason ?? "No retained content is available for this evidence item."}
      </p>
    </div>
  );
}

export function SampleEvidenceView({ detail }: { detail: SampleEvidenceDetailReadModel }) {
  const { run, sample, benchmark_case: benchmarkCase } = detail;
  const identity = run.identity;

  return (
    <AppShell activePrimary="Runs">
      <div className="evidence-drilldown">
        <a className="evidence-drilldown__back" href={`#runs/${encodeURIComponent(run.run_id)}`}>
          ← Back to run samples
        </a>
        <PageHeader
          eyebrow={`${run.suite_id} · ${sample.task_id}`}
          title={sample.sample_id}
          description={`Attempt ${sample.attempt} · ${identity.model_id}${identity.quantization ? ` · ${identity.quantization}` : ""}. One immutable sample outcome from run ${run.run_id}.`}
        />

        <div className="evidence-drilldown__summary-grid" aria-label="Sample evidence summary">
          <div>
            <span>Outcome</span>
            <Status tone={sampleTone(sample.status)}>{sample.status}</Status>
          </div>
          <div>
            <span>Elapsed</span>
            <strong>{sample.elapsed_ms.toFixed(1)} ms</strong>
          </div>
          <div>
            <span>Tokens</span>
            <strong>
              {sample.input_tokens ?? "?"} in · {sample.output_tokens ?? "?"} out
            </strong>
          </div>
        </div>

        {sample.error ? (
          <div className="evidence-drilldown__notice" role="status">
            <Status tone="error">{sample.error.category}</Status>
            <p>
              {sample.error.code} · {sample.error.retryable ? "Retryable" : "Not marked retryable"}
            </p>
          </div>
        ) : null}

        {detail.definition_issues.length ? (
          <div className="evidence-drilldown__notice" role="status">
            <Status tone="warning">Definition context incomplete</Status>
            <ul>
              {detail.definition_issues.map((issue) => (
                <li key={issue}>{issue}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <section className="evidence-drilldown__section">
          <SectionHeader
            title="Case context"
            description="Authored benchmark definition is shown separately from retained execution content."
          />
          {benchmarkCase ? (
            <div className="evidence-drilldown__content-grid">
              <div className="evidence-drilldown__panel">
                <span className="evidence-drilldown__panel-label">Benchmark input</span>
                <pre className="evidence-drilldown__pre">{renderValue(benchmarkCase.input)}</pre>
              </div>
              <div className="evidence-drilldown__panel">
                <span className="evidence-drilldown__panel-label">Expected output</span>
                <pre className="evidence-drilldown__pre">{renderValue(benchmarkCase.expected)}</pre>
              </div>
            </div>
          ) : (
            <EmptyState
              title="Benchmark case definition unavailable"
              description="The sample identity is retained, but inspectable authored case content is not available."
            />
          )}
        </section>

        <section className="evidence-drilldown__section">
          <SectionHeader
            title="Execution content"
            description="Prompt and model response follow the evidence-retention contract; unavailable content is never reconstructed."
          />
          <div className="evidence-drilldown__content-grid">
            <ContentPanel label="Retained execution prompt" evidence={detail.prompt} />
            <ContentPanel label="Actual model response" evidence={detail.response} />
          </div>
        </section>

        <section className="evidence-drilldown__section">
          <SectionHeader
            title="Evaluator evidence"
            description="Scores and rule context are evaluator-owned. The browser never invents a reason for a score."
          />
          {detail.scores.length ? (
            <div className="evidence-drilldown__stack">
              {detail.scores.map((score) => (
                <article
                  className="evidence-drilldown__card"
                  key={`${score.evaluator_id}:${score.evaluator_version}:${score.metric}`}
                >
                  <div className="evidence-drilldown__card-header">
                    <div>
                      <h3>{score.metric}</h3>
                      <p>
                        {score.evaluator_id} · {score.evaluator_version}
                      </p>
                    </div>
                    <strong>{score.value}</strong>
                  </div>
                  <p>{score.evaluator_rule_summary ?? "Evaluator rule summary unavailable."}</p>
                  <div className="evidence-drilldown__notice">
                    <strong>Evaluation explanation</strong>
                    <p>
                      {score.explanation_state === "available" && score.explanation
                        ? score.explanation
                        : "Evaluation explanation unavailable"}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No evaluator scores retained"
              description="This sample has no evaluator score evidence to display."
            />
          )}
        </section>

        <section className="evidence-drilldown__section">
          <SectionHeader
            title="Measurements & provenance"
            description="Sample measurements retain scope, source and protocol rather than collapsing into a generic performance score."
          />
          {detail.measurements.length ? (
            <div className="evidence-drilldown__metadata-grid">
              {detail.measurements.map((measurement) => (
                <div key={`${measurement.name}:${measurement.protocol_version}`}>
                  <dl>
                    <dt>{measurement.name}</dt>
                    <dd>
                      {measurement.value} {measurement.unit}
                    </dd>
                    <dt>Provenance</dt>
                    <dd>
                      {measurement.provenance} · {measurement.scope} ·{" "}
                      {measurement.protocol_version}
                    </dd>
                  </dl>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No sample measurements retained"
              description="No trustworthy sample-level measurement evidence is available for this attempt."
            />
          )}
        </section>

        <Disclosure summary="Show run identity and fingerprint">
          <div className="evidence-drilldown__metadata-grid">
            <div>
              <dl>
                <dt>Model</dt>
                <dd>{identity.model_id}</dd>
              </dl>
            </div>
            <div>
              <dl>
                <dt>Quantization</dt>
                <dd>{identity.quantization ?? "Unknown"}</dd>
              </dl>
            </div>
            <div>
              <dl>
                <dt>Fingerprint</dt>
                <dd>{run.fingerprint_id}</dd>
              </dl>
            </div>
          </div>
          <pre className="evidence-drilldown__pre">
            {JSON.stringify(detail.fingerprint, null, 2)}
          </pre>
        </Disclosure>
      </div>
    </AppShell>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; detail: SampleEvidenceDetailReadModel }
  | { status: "error"; message: string };

export function SampleEvidencePage({
  runId,
  taskId,
  sampleId,
  attempt,
}: {
  runId: string;
  taskId: string;
  sampleId: string;
  attempt: number;
}) {
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    getSampleEvidence(runId, taskId, sampleId, attempt, { signal: controller.signal })
      .then((detail) => setState({ status: "ready", detail }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Sample evidence could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt, loadAttempt, runId, sampleId, taskId]);

  if (state.status === "loading") {
    return (
      <AppShell activePrimary="Runs">
        <LoadingState
          title="Loading sample evidence"
          description="Reading the immutable sample attempt, evaluator evidence and retained content state."
        />
      </AppShell>
    );
  }

  if (state.status === "error") {
    return (
      <AppShell activePrimary="Runs">
        <ErrorState
          title="Could not load this sample"
          description={state.message}
          action={<Button onClick={() => setLoadAttempt((value) => value + 1)}>Try again</Button>}
        />
      </AppShell>
    );
  }

  return <SampleEvidenceView detail={state.detail} />;
}
