import { useEffect, useMemo, useState } from "react";

import { compareRuns, listRuns } from "../../api";
import type {
  ComparisonReadModel,
  DimensionComparisonReadModel,
  MetricDelta,
  RunSummaryReadModel,
} from "../../api";
import {
  AppShell,
  Button,
  CompatibilitySummary,
  DataTable,
  Delta,
  EmptyState,
  ErrorState,
  IdentityDiff,
  LoadingState,
  PageHeader,
  SectionHeader,
  Select,
  Status,
} from "../../components";
import "./compare.css";

interface CompareViewProps {
  runs: RunSummaryReadModel[];
  baselineRunId: string;
  candidateRunId: string;
  comparison: ComparisonReadModel | null;
  loading?: boolean;
  error?: string | null;
  onBaselineChange?: (runId: string) => void;
  onCandidateChange?: (runId: string) => void;
  onCompare?: () => void;
}

const DIMENSION_LABELS: Record<DimensionComparisonReadModel["dimension"], string> = {
  capability: "Capability / quality",
  runtime: "Runtime",
  resource: "Resources",
};

function runLabel(run: RunSummaryReadModel) {
  const completed = run.completed_at
    ? new Date(run.completed_at).toLocaleString()
    : "completed run";
  return `${run.identity.model_id} · ${run.suite_id} · ${completed}`;
}

function formatNumber(value: number, unit: string | null) {
  const rounded = new Intl.NumberFormat(undefined, { maximumFractionDigits: 4 }).format(value);
  return unit ? `${rounded} ${unit}` : rounded;
}

function metricName(metric: string) {
  return metric.split("|")[0] || metric;
}

function DeltaTable({ dimension }: { dimension: DimensionComparisonReadModel }) {
  if (!dimension.comparable) return null;

  if (!dimension.deltas.length) {
    return (
      <div className="compare-not-evaluated">
        <Status tone="neutral">No shared evaluated metrics</Status>
        <p>
          The evidence identity is compatible for this dimension, but the two runs do not expose a
          shared metric delta.
        </p>
      </div>
    );
  }

  const columns = [
    {
      id: "metric",
      header: "Metric",
      render: (delta: MetricDelta) => <code>{metricName(delta.metric)}</code>,
    },
    {
      id: "baseline",
      header: "Baseline",
      align: "end" as const,
      render: (delta: MetricDelta) => formatNumber(delta.baseline_value, delta.unit),
    },
    {
      id: "candidate",
      header: "Candidate",
      align: "end" as const,
      render: (delta: MetricDelta) => formatNumber(delta.candidate_value, delta.unit),
    },
    {
      id: "change",
      header: "Change",
      align: "end" as const,
      render: (delta: MetricDelta) => (
        <div className="compare-delta-cell">
          <Delta
            value={delta.absolute_delta}
            unit={delta.unit ?? undefined}
            higherIsBetter={delta.higher_is_better}
            label="Absolute"
          />
          {delta.relative_delta_pct === null ? null : (
            <span>{formatNumber(delta.relative_delta_pct, "%")}</span>
          )}
        </div>
      ),
    },
  ];

  return (
    <DataTable
      caption={`${DIMENSION_LABELS[dimension.dimension]} metric deltas`}
      columns={columns}
      rows={dimension.deltas}
      rowKey={(delta) => delta.metric}
    />
  );
}

function MissingEvidence({ dimension }: { dimension: DimensionComparisonReadModel }) {
  if (!dimension.comparable) return null;
  if (!dimension.missing_in_baseline.length && !dimension.missing_in_candidate.length) {
    return null;
  }

  return (
    <div className="compare-missing">
      <strong>Evidence coverage differs</strong>
      {dimension.missing_in_baseline.length ? (
        <p>Only candidate: {dimension.missing_in_baseline.join(", ")}</p>
      ) : null}
      {dimension.missing_in_candidate.length ? (
        <p>Only baseline: {dimension.missing_in_candidate.join(", ")}</p>
      ) : null}
    </div>
  );
}

export function CompareView({
  runs,
  baselineRunId,
  candidateRunId,
  comparison,
  loading = false,
  error = null,
  onBaselineChange,
  onCandidateChange,
  onCompare,
}: CompareViewProps) {
  const baseline = runs.find((run) => run.run_id === baselineRunId);
  const candidate = runs.find((run) => run.run_id === candidateRunId);
  const canCompare = Boolean(baseline && candidate && baselineRunId !== candidateRunId && !loading);

  return (
    <AppShell activePrimary="Compare">
      <div className="compare-page">
        <PageHeader
          eyebrow="Evidence comparison"
          title="Compare runs"
          description="Choose a baseline and candidate. Compatibility is established from frozen execution evidence before metric deltas appear."
        />

        <section className="compare-selection" aria-label="Evidence selection">
          <SectionHeader
            title="Choose evidence"
            description="Baseline and candidate must be two different immutable completed runs."
          />
          <div className="compare-selectors">
            <Select
              label="Baseline"
              value={baselineRunId}
              onChange={(event) => onBaselineChange?.(event.currentTarget.value)}
            >
              <option value="">Choose baseline</option>
              {runs.map((run) => (
                <option key={run.run_id} value={run.run_id}>
                  {runLabel(run)}
                </option>
              ))}
            </Select>
            <Select
              label="Candidate"
              value={candidateRunId}
              onChange={(event) => onCandidateChange?.(event.currentTarget.value)}
            >
              <option value="">Choose candidate</option>
              {runs.map((run) => (
                <option key={run.run_id} value={run.run_id}>
                  {runLabel(run)}
                </option>
              ))}
            </Select>
          </div>
          <div className="compare-selection-actions">
            <Button variant="primary" disabled={!canCompare} onClick={onCompare}>
              {loading ? "Comparing…" : "Compare evidence"}
            </Button>
            {baselineRunId && baselineRunId === candidateRunId ? (
              <span role="alert">Choose two different runs.</span>
            ) : null}
          </div>
        </section>

        {error ? (
          <ErrorState
            title="Could not compare these runs"
            description={error}
            action={<Button onClick={onCompare}>Try again</Button>}
          />
        ) : null}

        {comparison ? (
          <div className="compare-results">
            <section className="compare-identity" aria-label="Identity differences">
              <SectionHeader
                title="Identity differences"
                description="Inspect the frozen identity differences that govern whether each dimension can be compared."
              />
              <IdentityDiff differences={comparison.identity_differences} />
            </section>

            <div className="compare-dimensions">
              {comparison.dimensions.map((dimension) => (
                <section className="compare-dimension" key={dimension.dimension}>
                  <SectionHeader title={DIMENSION_LABELS[dimension.dimension]} />
                  <CompatibilitySummary
                    comparable={dimension.comparable}
                    reasons={dimension.reasons}
                  />
                  <DeltaTable dimension={dimension} />
                  <MissingEvidence dimension={dimension} />
                </section>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; runs: RunSummaryReadModel[] }
  | { status: "error"; message: string };

interface ComparePageProps {
  initialCandidateRunId?: string;
}

export function ComparePage({ initialCandidateRunId }: ComparePageProps) {
  const [loadState, setLoadState] = useState<LoadState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [baselineRunId, setBaselineRunId] = useState("");
  const [candidateRunId, setCandidateRunId] = useState(initialCandidateRunId ?? "");
  const [comparison, setComparison] = useState<ComparisonReadModel | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    listRuns({ limit: 200 }, { signal: controller.signal })
      .then((runs) => {
        setLoadState({ status: "ready", runs });
        const candidate =
          (initialCandidateRunId &&
            runs.find((run) => run.run_id === initialCandidateRunId)?.run_id) ||
          runs[0]?.run_id ||
          "";
        const baseline = runs.find((run) => run.run_id !== candidate)?.run_id || "";
        setCandidateRunId(candidate);
        setBaselineRunId(baseline);
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setLoadState({
          status: "error",
          message: error instanceof Error ? error.message : "Run evidence could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt, initialCandidateRunId]);

  const runs = useMemo(() => (loadState.status === "ready" ? loadState.runs : []), [loadState]);

  const resetComparison = () => {
    setComparison(null);
    setComparisonError(null);
  };

  const compare = () => {
    if (!baselineRunId || !candidateRunId || baselineRunId === candidateRunId) return;
    setComparisonLoading(true);
    setComparisonError(null);
    compareRuns(baselineRunId, candidateRunId)
      .then(setComparison)
      .catch((error: unknown) =>
        setComparisonError(
          error instanceof Error ? error.message : "Comparison could not be loaded.",
        ),
      )
      .finally(() => setComparisonLoading(false));
  };

  if (loadState.status === "loading") {
    return (
      <AppShell activePrimary="Compare">
        <LoadingState
          title="Loading completed runs"
          description="Reading immutable evidence available for comparison."
        />
      </AppShell>
    );
  }

  if (loadState.status === "error") {
    return (
      <AppShell activePrimary="Compare">
        <ErrorState
          title="Could not load runs"
          description={loadState.message}
          action={<Button onClick={() => setAttempt((value) => value + 1)}>Try again</Button>}
        />
      </AppShell>
    );
  }

  if (runs.length < 2) {
    return (
      <AppShell activePrimary="Compare">
        <EmptyState
          title="Two completed runs are required"
          description="Run another evaluation before comparing evidence."
        />
      </AppShell>
    );
  }

  return (
    <CompareView
      runs={runs}
      baselineRunId={baselineRunId}
      candidateRunId={candidateRunId}
      comparison={comparison}
      loading={comparisonLoading}
      error={comparisonError}
      onBaselineChange={(runId) => {
        setBaselineRunId(runId);
        resetComparison();
      }}
      onCandidateChange={(runId) => {
        setCandidateRunId(runId);
        resetComparison();
      }}
      onCompare={compare}
    />
  );
}
