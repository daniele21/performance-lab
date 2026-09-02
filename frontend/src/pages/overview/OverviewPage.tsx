import { useEffect, useState } from "react";

import { listRuns, listTestedModels } from "../../api";
import type {
  MetricReadModel,
  RunStatus,
  RunSummaryReadModel,
  TestedModelReadModel,
} from "../../api";
import {
  AppShell,
  Button,
  DataTable,
  EmptyState,
  ErrorState,
  LoadingState,
  Metric,
  PageHeader,
  SectionHeader,
  Status,
  type DataColumn,
} from "../../components";
import "./overview.css";

interface OverviewData {
  models: TestedModelReadModel[];
  runs: RunSummaryReadModel[];
}

interface OverviewViewProps extends OverviewData {
  onFindBestSetup?: () => void;
  onTestModel?: () => void;
}

const RUN_STATUS_TONE: Record<RunStatus, "neutral" | "success" | "warning" | "error"> = {
  planned: "neutral",
  running: "neutral",
  succeeded: "success",
  failed: "error",
  cancelled: "warning",
};

function metricFor(model: TestedModelReadModel, dimension: MetricReadModel["dimension"]) {
  return model.latest_metrics.find((metric) => metric.dimension === dimension);
}

function formatTimestamp(value: string | null) {
  if (!value) return "Not available";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString();
}

function deviceContext(model: TestedModelReadModel) {
  const identity = model.identity;
  return (
    identity.hardware_device_id ??
    identity.hardware_device_class ??
    identity.runtime_name ??
    identity.target_id
  );
}

const MODEL_COLUMNS: readonly DataColumn<TestedModelReadModel>[] = [
  {
    id: "model",
    header: "Tested model",
    render: (model) => (
      <div className="overview-model-identity">
        <strong>{model.identity.model_id}</strong>
        <span>{deviceContext(model)}</span>
        {model.identity.quantization ? <span>{model.identity.quantization}</span> : null}
      </div>
    ),
  },
  {
    id: "quality",
    header: "Quality",
    render: (model) => {
      const metric = metricFor(model, "quality");
      return metric ? (
        <Metric
          label={metric.label}
          value={metric.value}
          unit={metric.unit ?? undefined}
          dimension="quality"
          availability={metric.availability}
        />
      ) : (
        <Metric label="Quality" value={null} dimension="quality" availability="not_evaluated" />
      );
    },
  },
  {
    id: "performance",
    header: "Performance",
    render: (model) => {
      const metric = metricFor(model, "performance");
      return metric ? (
        <Metric
          label={metric.label}
          value={metric.value}
          unit={metric.unit ?? undefined}
          dimension="performance"
          availability={metric.availability}
        />
      ) : (
        <Metric
          label="Performance"
          value={null}
          dimension="performance"
          availability="not_evaluated"
        />
      );
    },
  },
  {
    id: "resources",
    header: "Resources",
    render: (model) => {
      const metric = metricFor(model, "resources");
      return metric ? (
        <Metric
          label={metric.label}
          value={metric.value}
          unit={metric.unit ?? undefined}
          dimension="resources"
          availability={metric.availability}
        />
      ) : (
        <Metric label="Resources" value={null} dimension="resources" availability="not_evaluated" />
      );
    },
  },
  {
    id: "runs",
    header: "Runs",
    align: "end",
    render: (model) => model.run_count,
  },
];

const RUN_COLUMNS: readonly DataColumn<RunSummaryReadModel>[] = [
  {
    id: "model",
    header: "Model",
    render: (run) => run.identity.model_id,
  },
  {
    id: "suite",
    header: "Test suite",
    render: (run) => `${run.suite_id} · v${run.suite_version}`,
  },
  {
    id: "status",
    header: "Status",
    render: (run) => <Status tone={RUN_STATUS_TONE[run.status]}>{run.status}</Status>,
  },
  {
    id: "completed",
    header: "Completed",
    render: (run) => formatTimestamp(run.completed_at),
  },
];

export function OverviewView({ models, runs, onFindBestSetup, onTestModel }: OverviewViewProps) {
  return (
    <AppShell activePrimary="Overview">
      <div className="overview-page">
        <PageHeader
          title="Overview"
          description="Choose the next decision to evaluate, then return to the evidence that Performance Lab has already produced."
          actions={
            <Button variant="quiet" onClick={onTestModel}>
              Test a model
            </Button>
          }
        />

        <section className="overview-decision" aria-labelledby="overview-decision-title">
          <div className="overview-decision__copy">
            <h2 id="overview-decision-title">Find the best setup for your goal</h2>
            <p>
              Tell Performance Lab what the model needs to do and where it has to run. We'll compare
              eligible models, quantizations and configurations, then explain the best evidence-backed
              fit.
            </p>
            <ul>
              <li>Start from the workload and target device.</li>
              <li>Compare only evidence-backed candidates and configuration ranges.</li>
              <li>Keep quality, performance and resources separate in the recommendation.</li>
            </ul>
            <Button variant="primary" onClick={onFindBestSetup}>
              Find best setup
            </Button>
          </div>
          <div className="overview-decision__summary" aria-label="Decision flow">
            <span>Goal</span>
            <span>Models</span>
            <span>Optimization</span>
            <span>Recommendation</span>
          </div>
        </section>

        <section className="overview-page__section overview-page__section--primary">
          <SectionHeader
            title="Recent evaluations"
            description="Immutable evidence from your latest runs, newest first."
          />
          <DataTable
            caption="Recent evaluation runs"
            columns={RUN_COLUMNS}
            rows={runs.slice(0, 8)}
            rowKey={(run) => run.run_id}
            emptyMessage="No evaluations yet. Start with Find best setup or Test a model."
          />
        </section>

        <section className="overview-page__section overview-page__section--secondary">
          <SectionHeader
            title="Tested models"
            description={
              models.length
                ? `${models.length} model${models.length === 1 ? "" : "s"} with retained evidence. Exact recommendations still require explicit comparability.`
                : "Model evidence appears here after a completed evaluation."
            }
          />
          {models.length ? (
            <DataTable
              caption="Tested model evidence"
              columns={MODEL_COLUMNS}
              rows={models}
              rowKey={(model) => model.cohort_key}
            />
          ) : (
            <EmptyState
              title="No model evidence yet"
              description="Start from a goal and device to create comparable evidence for the decision you need to make."
              action={
                <Button variant="primary" onClick={onFindBestSetup}>
                  Find best setup
                </Button>
              }
            />
          )}
        </section>
      </div>
    </AppShell>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; data: OverviewData }
  | { status: "error"; message: string };

interface OverviewPageProps {
  onFindBestSetup?: () => void;
  onTestModel?: () => void;
}

export function OverviewPage({ onFindBestSetup, onTestModel }: OverviewPageProps) {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    Promise.all([
      listTestedModels({ signal: controller.signal }),
      listRuns({ limit: 8 }, { signal: controller.signal }),
    ])
      .then(([models, runs]) => setState({ status: "ready", data: { models, runs } }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Local evidence could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt]);

  if (state.status === "loading") {
    return (
      <AppShell activePrimary="Overview">
        <LoadingState
          title="Loading local evidence"
          description="Reading immutable evidence from the local Performance Lab store."
        />
      </AppShell>
    );
  }

  if (state.status === "error") {
    return (
      <AppShell activePrimary="Overview">
        <ErrorState
          title="Could not load local evidence"
          description={state.message}
          action={<Button onClick={() => setAttempt((value) => value + 1)}>Try again</Button>}
        />
      </AppShell>
    );
  }

  return (
    <OverviewView {...state.data} onFindBestSetup={onFindBestSetup} onTestModel={onTestModel} />
  );
}
