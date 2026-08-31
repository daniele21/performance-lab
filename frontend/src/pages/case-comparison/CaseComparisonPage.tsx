import { useEffect, useState } from "react";

import { getCampaignCaseComparison } from "../../api";
import type {
  CampaignCaseCandidateReadModel,
  CampaignCaseComparisonReadModel,
  EvidenceContentReadModel,
} from "../../api";
import {
  AppShell,
  Button,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  SectionHeader,
  Status,
} from "../../components";
import "./case-comparison.css";

function renderValue(value: unknown) {
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

function comparisonTone(state: CampaignCaseComparisonReadModel["state"]) {
  if (state === "ready") return "success" as const;
  if (state === "partial") return "warning" as const;
  return "warning" as const;
}

function contentLabel(evidence: EvidenceContentReadModel) {
  if (evidence.state === "retained") return null;
  return evidence.state === "not_retained" ? "Content not retained" : "Content unavailable";
}

function CandidateCard({ candidate }: { candidate: CampaignCaseCandidateReadModel }) {
  const evidence = candidate.evidence;
  const responseState = evidence ? contentLabel(evidence.response) : null;
  const identity = candidate.identity;
  const status = !evidence
    ? "Evidence unavailable"
    : candidate.comparable_to_reference
      ? "Comparable"
      : "Not comparable";
  const tone = !evidence ? "neutral" : candidate.comparable_to_reference ? "success" : "warning";

  return (
    <article className="case-comparison__candidate">
      <header className="case-comparison__candidate-header">
        <div>
          <h3>{candidate.model_id}</h3>
          <p>
            Quantization: {identity?.quantization ?? "Unknown"} · Config{" "}
            {candidate.config_digest.slice(0, 12)}…
          </p>
        </div>
        <Status tone={tone}>{status}</Status>
      </header>

      {candidate.compatibility_reasons.length ? (
        <div className="case-comparison__notice" role="status">
          <strong>Why this candidate is not comparable</strong>
          <ul>
            {candidate.compatibility_reasons.map((reason) => (
              <li key={`${reason.code}:${reason.field}`}>{reason.message}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {candidate.unavailable_reason ? (
        <div className="case-comparison__notice" role="status">
          <strong>Evidence unavailable</strong>
          <p>{candidate.unavailable_reason}</p>
        </div>
      ) : null}

      {evidence ? (
        <>
          <dl className="case-comparison__facts">
            <div>
              <dt>Run</dt>
              <dd>{evidence.run.run_id}</dd>
            </div>
            <div>
              <dt>Attempt</dt>
              <dd>{evidence.sample.attempt}</dd>
            </div>
            <div>
              <dt>Outcome</dt>
              <dd>{evidence.sample.status}</dd>
            </div>
            <div>
              <dt>Elapsed</dt>
              <dd>{evidence.sample.elapsed_ms.toFixed(1)} ms</dd>
            </div>
          </dl>

          <div className="case-comparison__response">
            <span>Actual model response</span>
            {evidence.response.state === "retained" ? (
              <pre>{renderValue(evidence.response.content)}</pre>
            ) : (
              <>
                <Status tone="unknown">{responseState}</Status>
                <p>{evidence.response.reason ?? "No retained response content is available."}</p>
              </>
            )}
          </div>

          <div className="case-comparison__scores">
            <strong>Evaluator evidence</strong>
            {evidence.scores.length ? (
              <dl>
                {evidence.scores.map((score) => (
                  <div key={`${score.evaluator_id}:${score.evaluator_version}:${score.metric}`}>
                    <dt>
                      {score.metric} · {score.evaluator_id}@{score.evaluator_version}
                    </dt>
                    <dd>{score.value}</dd>
                  </div>
                ))}
              </dl>
            ) : (
              <span>No evaluator scores retained</span>
            )}
          </div>

          {evidence.measurements.length ? (
            <div className="case-comparison__measurements">
              <strong>Sample measurements</strong>
              <dl>
                {evidence.measurements.map((measurement) => (
                  <div key={`${measurement.name}:${measurement.protocol_version}`}>
                    <dt>{measurement.name}</dt>
                    <dd>
                      {measurement.value} {measurement.unit} · {measurement.provenance}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          ) : null}

          <a
            className="case-comparison__evidence-link"
            href={`#runs/${encodeURIComponent(evidence.run.run_id)}/samples/${encodeURIComponent(
              evidence.sample.task_id,
            )}/${encodeURIComponent(evidence.sample.sample_id)}/${evidence.sample.attempt}`}
          >
            Open exact sample evidence
          </a>
        </>
      ) : null}
    </article>
  );
}

export function CaseComparisonView({ detail }: { detail: CampaignCaseComparisonReadModel }) {
  return (
    <AppShell activePrimary="Find best setup">
      <div className="case-comparison">
        <a
          className="case-comparison__back"
          href={`#campaigns/${encodeURIComponent(detail.campaign_id)}`}
        >
          ← Back to campaign results
        </a>
        <PageHeader
          eyebrow={`${detail.suite_id} · ${detail.task_id}`}
          title={detail.sample_id}
          description="The same immutable benchmark case across candidate Runs. Compatibility is established in Python before evidence is placed side by side."
        />

        <div className="case-comparison__summary" role="status">
          <Status tone={comparisonTone(detail.state)}>
            {detail.state === "ready"
              ? "Comparable"
              : detail.state === "partial"
                ? "Partially comparable"
                : "Not comparable"}
          </Status>
          <p>{detail.summary}</p>
          <small>
            {detail.comparable_candidate_count} compatible candidate Runs · reference{" "}
            {detail.reference_run_id ?? "unavailable"}. The reference establishes protocol
            compatibility only; it is not a winner or baseline score.
          </small>
        </div>

        <section className="case-comparison__section">
          <SectionHeader
            title="Exact case context"
            description="Authored input and expected output are benchmark definition data, kept separate from each candidate execution."
          />
          {detail.benchmark_case ? (
            <div className="case-comparison__context-grid">
              <div>
                <span>Benchmark input</span>
                <pre>{renderValue(detail.benchmark_case.input)}</pre>
              </div>
              <div>
                <span>Expected output</span>
                <pre>{renderValue(detail.benchmark_case.expected)}</pre>
              </div>
            </div>
          ) : (
            <EmptyState
              title="Benchmark case definition unavailable"
              description="The retained task/sample identity can still be audited, but authored case content is not inspectable."
            />
          )}
        </section>

        <section className="case-comparison__section">
          <SectionHeader
            title="Candidate evidence"
            description="Model + quantization + frozen configuration + immutable Run stay visible. No cross-case delta or forced winner is introduced."
          />
          <div className="case-comparison__candidate-grid">
            {detail.candidates.map((candidate) => (
              <CandidateCard candidate={candidate} key={candidate.entry_id} />
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; detail: CampaignCaseComparisonReadModel }
  | { status: "error"; message: string };

export function CaseComparisonPage({
  campaignId,
  taskId,
  sampleId,
}: {
  campaignId: string;
  taskId: string;
  sampleId: string;
}) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    getCampaignCaseComparison(campaignId, taskId, sampleId, { signal: controller.signal })
      .then((detail) => setState({ status: "ready", detail }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Case comparison could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt, campaignId, sampleId, taskId]);

  if (state.status === "loading") {
    return (
      <AppShell activePrimary="Find best setup">
        <LoadingState
          title="Loading same-case evidence"
          description="Resolving exact retained sample attempts and Python-owned compatibility across campaign Runs."
        />
      </AppShell>
    );
  }

  if (state.status === "error") {
    return (
      <AppShell activePrimary="Find best setup">
        <ErrorState
          title="Could not compare this case"
          description={state.message}
          action={<Button onClick={() => setAttempt((value) => value + 1)}>Try again</Button>}
        />
      </AppShell>
    );
  }

  return <CaseComparisonView detail={state.detail} />;
}
