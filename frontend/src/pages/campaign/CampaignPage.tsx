import { useEffect, useMemo, useState } from "react";

import { cancelCampaign, getCampaign, listCampaignCases, subscribeCampaign } from "../../api";
import type {
  CampaignCaseSummaryReadModel,
  CampaignReadModel,
  MetricDimension,
} from "../../api";
import {
  AppShell,
  Button,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  RunProgress,
  SectionHeader,
  Status,
} from "../../components";
import "./campaign.css";

interface CampaignPageProps {
  campaignId: string;
  onOpenRun?: (runId: string) => void;
  onOpenCase?: (taskId: string, sampleId: string) => void;
  onNewCampaign?: () => void;
}

type ConnectionState = "connecting" | "live" | "reconnecting";

function isTerminal(campaign: CampaignReadModel) {
  return ["succeeded", "failed", "cancelled", "interrupted"].includes(campaign.status);
}

function stateTone(
  state: CampaignReadModel["status"],
): "neutral" | "success" | "warning" | "error" {
  if (state === "succeeded") return "success";
  if (state === "failed") return "error";
  if (state === "cancelled" || state === "interrupted" || state === "cancelling") {
    return "warning";
  }
  return "neutral";
}

function label(value: string) {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function metricValue(value: number | null, unit: string | null) {
  if (value === null) return "Unavailable";
  const rendered = Number.isInteger(value)
    ? String(value)
    : value.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
  return unit ? `${rendered} ${unit}` : rendered;
}

export function CampaignPage({
  campaignId,
  onOpenRun,
  onOpenCase,
  onNewCampaign,
}: CampaignPageProps) {
  const [campaign, setCampaign] = useState<CampaignReadModel | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadAttempt, setReloadAttempt] = useState(0);
  const [connection, setConnection] = useState<ConnectionState>("connecting");
  const [cancelLoading, setCancelLoading] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    let disposed = false;
    let closeStream: () => void = () => undefined;

    setLoadError(null);
    setCampaign(null);
    setConnection("connecting");

    const applySnapshot = (next: CampaignReadModel) => {
      if (disposed) return;
      setCampaign(next);
      setConnection("live");
    };

    getCampaign(campaignId, { signal: controller.signal })
      .then((initial) => {
        applySnapshot(initial);
        if (disposed || isTerminal(initial)) return;
        closeStream = subscribeCampaign(campaignId, {
          afterRevision: initial.revision,
          onSnapshot: applySnapshot,
          onDisconnect: () => {
            if (!disposed) setConnection("reconnecting");
          },
          onMalformedEvent: () => {
            if (!disposed) setConnection("reconnecting");
          },
        });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted || disposed) return;
        setLoadError(
          error instanceof Error ? error.message : "Campaign state could not be loaded.",
        );
      });

    return () => {
      disposed = true;
      controller.abort();
      closeStream();
    };
  }, [campaignId, reloadAttempt]);

  const progress = useMemo(() => {
    const entries = campaign?.entries ?? [];
    return entries.reduce(
      (total, entry) => ({
        completed: total.completed + entry.completed_samples,
        samples: total.samples + entry.total_samples,
        completedRuns: total.completedRuns + (entry.status === "succeeded" ? 1 : 0),
      }),
      { completed: 0, samples: 0, completedRuns: 0 },
    );
  }, [campaign]);

  const cancel = () => {
    if (!campaign || isTerminal(campaign)) return;
    setCancelLoading(true);
    setCancelError(null);
    cancelCampaign(campaignId)
      .then(setCampaign)
      .catch((error: unknown) =>
        setCancelError(
          error instanceof Error ? error.message : "The campaign could not be cancelled.",
        ),
      )
      .finally(() => setCancelLoading(false));
  };

  if (loadError) {
    return (
      <AppShell activePrimary="Find best setup">
        <ErrorState
          title="Could not reconnect to this campaign"
          description={`${loadError} The server-owned campaign may still be running. Reconnect before starting another evaluation.`}
          action={
            <Button variant="primary" onClick={() => setReloadAttempt((value) => value + 1)}>
              Reconnect to campaign
            </Button>
          }
        />
      </AppShell>
    );
  }

  if (!campaign) {
    return (
      <AppShell activePrimary="Find best setup">
        <LoadingState
          title="Connecting to campaign"
          description="Reading the latest persisted campaign lifecycle and immutable Run evidence."
        />
      </AppShell>
    );
  }

  return (
    <AppShell activePrimary="Find best setup">
      <div className="campaign-page">
        <PageHeader
          eyebrow={isTerminal(campaign) ? "Campaign results" : "Evaluation campaign"}
          title={campaign.use_case_id}
          description="Campaign progress is server-owned and reconnectable. Each completed row remains an immutable Run with its own evidence identity."
          actions={
            isTerminal(campaign) ? (
              <Button variant="quiet" onClick={onNewCampaign}>
                Find another setup
              </Button>
            ) : undefined
          }
        />

        <div className="campaign-status-row">
          <Status tone={stateTone(campaign.status)}>{label(campaign.status)}</Status>
          {!isTerminal(campaign) ? (
            <Status tone={connection === "reconnecting" ? "warning" : "neutral"}>
              {connection === "reconnecting" ? "Reconnecting" : "Live progress connected"}
            </Status>
          ) : null}
          <span className="campaign-id">{campaign.campaign_id}</span>
        </div>

        <section className="campaign-progress-section">
          <SectionHeader
            title="Campaign progress"
            description={`${progress.completedRuns} of ${campaign.entries.length} immutable runs completed successfully.`}
          />
          <RunProgress
            phase={label(campaign.status)}
            completed={progress.completed}
            total={progress.samples || null}
          />
          {!isTerminal(campaign) ? (
            <div className="campaign-actions">
              <Button
                variant="quiet"
                disabled={cancelLoading || campaign.status === "cancelling"}
                onClick={cancel}
              >
                {cancelLoading || campaign.status === "cancelling"
                  ? "Cancelling…"
                  : "Cancel campaign"}
              </Button>
              <span>Leaving this page does not cancel the campaign.</span>
            </div>
          ) : null}
          {cancelError ? (
            <p className="campaign-error" role="alert">
              {cancelError}
            </p>
          ) : null}
        </section>

        <section className="campaign-matrix">
          <SectionHeader
            title="Candidate runs"
            description="One row is one candidate + frozen configuration + immutable Run. Unknown identity remains explicit."
          />
          <div className="campaign-entry-list">
            {campaign.entries.map((entry) => (
              <article className="campaign-entry" key={entry.entry_id}>
                <div className="campaign-entry-heading">
                  <div>
                    <strong>{entry.model_id}</strong>
                    <span>
                      Quantization: {entry.identity?.quantization ?? "Unknown"} · Config{" "}
                      {entry.config_digest.slice(0, 12)}…
                    </span>
                  </div>
                  <Status tone={stateTone(entry.status)}>{label(entry.status)}</Status>
                </div>
                <RunProgress
                  phase={label(entry.status)}
                  completed={entry.completed_samples}
                  total={entry.total_samples || null}
                />
                {entry.error_message ? (
                  <p className="campaign-error" role="alert">
                    {entry.error_message}
                  </p>
                ) : null}
                {entry.run_id ? (
                  <Button variant="quiet" onClick={() => onOpenRun?.(entry.run_id!)}>
                    Open immutable Run
                  </Button>
                ) : null}
              </article>
            ))}
          </div>
        </section>

        {isTerminal(campaign) ? (
          <CampaignResults campaign={campaign} onOpenRun={onOpenRun} onOpenCase={onOpenCase} />
        ) : null}
      </div>
    </AppShell>
  );
}

function CampaignResults({
  campaign,
  onOpenRun,
  onOpenCase,
}: {
  campaign: CampaignReadModel;
  onOpenRun?: (runId: string) => void;
  onOpenCase?: (taskId: string, sampleId: string) => void;
}) {
  const { results } = campaign;
  return (
    <section className="campaign-results" aria-labelledby="campaign-results-title">
      <SectionHeader
        title="Results"
        description="Compatibility and the versioned decision policy are shown before any recommendation. Quality, performance and resources stay separate."
      />
      <div className="campaign-policy">
        <span>Decision policy</span>
        <strong>
          {results.decision_policy.policy_id}@{results.decision_policy.policy_version}
        </strong>
        <p>{results.decision_policy.description}</p>
        <small>No hidden weights · No universal score</small>
      </div>

      <div className="campaign-compatibility" aria-label="Evidence compatibility">
        {results.compatibility.map((dimension) => (
          <article key={dimension.dimension}>
            <span>
              {dimension.dimension === "capability" ? "Quality" : label(dimension.dimension)}
            </span>
            <Status
              tone={
                dimension.comparable && dimension.evidence_available
                  ? "success"
                  : dimension.evidence_available
                    ? "warning"
                    : "neutral"
              }
            >
              {!dimension.evidence_available
                ? "Evidence unavailable"
                : dimension.comparable
                  ? "Comparable"
                  : "Not comparable"}
            </Status>
            {dimension.reasons.length ? (
              <small>{dimension.reasons.map((reason) => reason.message).join(" · ")}</small>
            ) : null}
          </article>
        ))}
      </div>

      <div className="campaign-recommendation">
        <span>Best fit under this policy</span>
        {results.recommendation ? (
          <>
            <strong>{results.recommendation.model_id}</strong>
            <p>{results.recommendation.rationale}</p>
            <Button variant="quiet" onClick={() => onOpenRun?.(results.recommendation!.run_id)}>
              Inspect recommended Run
            </Button>
          </>
        ) : (
          <>
            <strong>No single recommended winner</strong>
            <p>{results.recommendation_reason}</p>
          </>
        )}
      </div>

      <SectionHeader
        title="Evidence by candidate"
        description="These are the retained metrics from each immutable Run, grouped by evidence dimension."
      />
      <div className="campaign-evidence-grid">
        {campaign.entries.map((entry) => (
          <article key={entry.entry_id}>
            <div className="campaign-evidence-heading">
              <strong>{entry.model_id}</strong>
              <span>Quantization: {entry.identity?.quantization ?? "Unknown"}</span>
            </div>
            {(["quality", "performance", "resources"] as MetricDimension[]).map((dimension) => {
              const metrics = entry.metrics.filter((metric) => metric.dimension === dimension);
              return (
                <div className="campaign-metric-group" key={dimension}>
                  <strong>{label(dimension)}</strong>
                  {metrics.length ? (
                    <dl>
                      {metrics.map((metric) => (
                        <div key={metric.metric_id}>
                          <dt>{metric.label}</dt>
                          <dd>{metricValue(metric.value, metric.unit)}</dd>
                        </div>
                      ))}
                    </dl>
                  ) : (
                    <span>Evidence unavailable</span>
                  )}
                </div>
              );
            })}
          </article>
        ))}
      </div>

      <CampaignCaseExplorer campaignId={campaign.campaign_id} onOpenCase={onOpenCase} />
    </section>
  );
}

type CampaignCasesLoadState =
  | { status: "loading" }
  | { status: "ready"; cases: CampaignCaseSummaryReadModel[] }
  | { status: "error"; message: string };

function CampaignCaseExplorer({
  campaignId,
  onOpenCase,
}: {
  campaignId: string;
  onOpenCase?: (taskId: string, sampleId: string) => void;
}) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<CampaignCasesLoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    listCampaignCases(campaignId, { signal: controller.signal })
      .then((cases) => setState({ status: "ready", cases }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Campaign cases could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt, campaignId]);

  return (
    <div className="campaign-case-explorer">
      <SectionHeader
        title="Compare exact benchmark cases"
        description="Choose one retained task/sample identity. Performance Lab will establish protocol compatibility before placing candidate evidence side by side."
      />
      {state.status === "loading" ? (
        <LoadingState
          title="Loading retained cases"
          description="Reading case identities from immutable campaign Runs."
        />
      ) : state.status === "error" ? (
        <ErrorState
          title="Could not load campaign cases"
          description={state.message}
          action={<Button onClick={() => setAttempt((value) => value + 1)}>Try again</Button>}
        />
      ) : state.cases.length ? (
        <div className="campaign-case-list">
          {state.cases.map((item) => (
            <article key={`${item.task_id}:${item.sample_id}`}>
              <div>
                <strong>{item.case_id ?? item.sample_id}</strong>
                <span>{item.task_id}</span>
                <small>
                  Retained in {item.available_candidate_count} of {item.candidate_count} candidate Runs
                </small>
              </div>
              <Button variant="quiet" onClick={() => onOpenCase?.(item.task_id, item.sample_id)}>
                Compare across candidates
              </Button>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No retained benchmark cases"
          description="Campaign Runs exist, but no sample identities are retained for same-case comparison."
        />
      )}
    </div>
  );
}
