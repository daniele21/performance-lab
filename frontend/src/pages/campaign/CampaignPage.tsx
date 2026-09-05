import { useEffect, useMemo, useState } from "react";

import { cancelCampaign, getCampaign, listCampaignCases, subscribeCampaign } from "../../api";
import type { CampaignCaseSummaryReadModel, CampaignReadModel, MetricDimension } from "../../api";
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
    .split(/[_-]/)
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

  const terminal = isTerminal(campaign);

  return (
    <AppShell activePrimary="Find best setup">
      <div className="campaign-page">
        <PageHeader
          title={terminal ? "Evaluation complete" : "Evaluation in progress"}
          description={
            terminal
              ? `${label(campaign.use_case_id)} · compatibility, decision policy and retained Run evidence explain the result.`
              : `${label(campaign.use_case_id)} · progress is persisted by the server and each candidate/configuration remains an immutable Run.`
          }
          actions={
            terminal ? (
              <Button variant="quiet" onClick={onNewCampaign}>
                Find another setup
              </Button>
            ) : undefined
          }
        />

        <div className="campaign-status-row">
          <Status tone={stateTone(campaign.status)}>{label(campaign.status)}</Status>
          {!terminal ? (
            <Status tone={connection === "reconnecting" ? "warning" : "neutral"}>
              {connection === "reconnecting" ? "Reconnecting" : "Live progress connected"}
            </Status>
          ) : null}
          <span className="campaign-id">{campaign.campaign_id}</span>
        </div>

        {terminal ? (
          <CampaignResults campaign={campaign} onOpenRun={onOpenRun} onOpenCase={onOpenCase} />
        ) : null}

        <section
          className={`campaign-progress-section${terminal ? " campaign-progress-section--completed" : ""}`}
        >
          <SectionHeader
            title={terminal ? "Completed progress" : "Overall progress"}
            description={`${progress.completedRuns} of ${campaign.entries.length} immutable runs completed successfully.`}
          />
          <RunProgress
            phase={label(campaign.status)}
            completed={progress.completed}
            total={progress.samples || null}
          />
          {!terminal ? (
            <div className="campaign-actions">
              <span>Progress is preserved if you leave this screen.</span>
              <Button
                variant="quiet"
                disabled={cancelLoading || campaign.status === "cancelling"}
                onClick={cancel}
              >
                {cancelLoading || campaign.status === "cancelling"
                  ? "Cancelling…"
                  : "Stop campaign"}
              </Button>
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
            title={terminal ? "Candidate runs" : "Live progress"}
            description="Each row is one candidate + frozen configuration + immutable Run. Unknown identity remains explicit."
          />
          <div className="campaign-entry-list">
            {campaign.entries.map((entry) => (
              <article className="campaign-entry" key={entry.entry_id}>
                <div className="campaign-entry-heading">
                  <div>
                    <strong>{entry.model_id}</strong>
                    <span>
                      Quantization: {entry.identity?.quantization ?? "Unknown"} · Configuration:{" "}
                      {entry.configuration_id} · Config {entry.config_digest.slice(0, 12)}…
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
  const availableCompatibility = results.compatibility.filter((item) => item.evidence_available);
  const allAvailableComparable =
    availableCompatibility.length > 0 && availableCompatibility.every((item) => item.comparable);
  const recommendedEntry = results.recommendation
    ? (campaign.entries.find(
        (entry) =>
          entry.candidate_id === results.recommendation?.candidate_id &&
          entry.configuration_id === results.recommendation?.configuration_id,
      ) ?? null)
    : null;

  return (
    <section className="campaign-results" aria-label="Campaign results">
      <SectionHeader
        title="Results"
        description="Compatibility and the explicit decision policy come first; the recommendation then explains the best fit without collapsing evidence into an overall score."
      />

      <div className="campaign-results-context">
        <div>
          <span>Evidence compatibility</span>
          <Status tone={allAvailableComparable ? "success" : "warning"}>
            {allAvailableComparable
              ? "Available evidence is comparable"
              : availableCompatibility.length
                ? "Some evidence is not comparable"
                : "Comparable evidence unavailable"}
          </Status>
        </div>
        <div>
          <span>Decision policy</span>
          <strong>{results.decision_policy.title}</strong>
          <small>
            {results.decision_policy.policy_id}@{results.decision_policy.policy_version} · No hidden
            weights · No universal score
          </small>
        </div>
      </div>

      <div className="campaign-recommendation">
        <span>Recommended setup</span>
        {results.recommendation ? (
          <div className="campaign-recommendation__body">
            <div className="campaign-recommendation__identity">
              <strong>{results.recommendation.model_id}</strong>
              <small>
                Quantization: {recommendedEntry?.identity?.quantization ?? "Unknown"} ·
                Configuration: {results.recommendation.configuration_id}
              </small>
            </div>
            <div className="campaign-recommendation__reason">
              <strong>Why this setup</strong>
              <p>{results.recommendation.rationale}</p>
            </div>
            <Button variant="secondary" onClick={() => onOpenRun?.(results.recommendation!.run_id)}>
              Inspect recommended Run
            </Button>
          </div>
        ) : (
          <div className="campaign-recommendation__body">
            <div className="campaign-recommendation__identity">
              <strong>No single recommended setup</strong>
            </div>
            <div className="campaign-recommendation__reason">
              <strong>Why</strong>
              <p>{results.recommendation_reason}</p>
            </div>
          </div>
        )}
      </div>

      <div className="campaign-compatibility" aria-label="Evidence compatibility by dimension">
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
            ) : dimension.evidence_note ? (
              <small>{dimension.evidence_note}</small>
            ) : null}
          </article>
        ))}
      </div>

      <SectionHeader
        title="Comparison"
        description="Retained metrics from each immutable Run. Quality, performance and decision-grade resources remain separate rather than collapsing into an overall score."
      />
      <div className="campaign-evidence-grid">
        {campaign.entries.map((entry) => (
          <article key={entry.entry_id}>
            <div className="campaign-evidence-heading">
              <strong>{entry.model_id}</strong>
              <span>Quantization: {entry.identity?.quantization ?? "Unknown"}</span>
            </div>
            {(["quality", "performance"] as MetricDimension[]).map((dimension) => {
              const metrics = entry.metrics.filter((metric) => metric.dimension === dimension);
              return (
                <div className="campaign-metric-group" data-dimension={dimension} key={dimension}>
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
            <div className="campaign-metric-group" data-dimension="resources">
              <strong>Resources</strong>
              {entry.resources.state === "available" ? (
                <dl>
                  {entry.resources.measurements.map((measurement) => (
                    <div
                      key={`${measurement.name}:${measurement.protocol_version}:${measurement.unit}`}
                    >
                      <dt>{measurement.name}</dt>
                      <dd>{metricValue(measurement.value, measurement.unit)}</dd>
                    </div>
                  ))}
                </dl>
              ) : (
                <>
                  <Status tone={entry.resources.state === "not_comparable" ? "warning" : "neutral"}>
                    {entry.resources.state === "not_comparable"
                      ? "Not comparable"
                      : "Evidence unavailable"}
                  </Status>
                  <span>{entry.resources.note}</span>
                </>
              )}
            </div>
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
                  Retained in {item.available_candidate_count} of {item.candidate_count} candidate
                  Runs
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
