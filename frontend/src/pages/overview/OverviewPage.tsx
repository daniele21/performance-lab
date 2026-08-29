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
          eyebrow="Local evidence"
          title="Your tested models"
          description="Models are grouped by model, runtime and hardware identity. Quality, performance and resource evidence stay separate so different trade-offs remain visible."
          actions={
            <div className="overview-page__actions">
              <Button variant="quiet" onClick={onTestModel}>
                Test a model
              </Button>
              <Button variant="primary" onClick={onFindBestSetup}>
                Find best setup
              </Button>
            </div>
          }
        />

        {models.length === 0 ? (
          <EmptyState
            title="No tested models yet"
            description="Start from a use case to define the model/configuration decision you want Performance Lab to evaluate."
            action={
              <Button variant="primary" onClick={onFindBestSetup}>
                Find best setup
              </Button>
            }
          />
        ) : (
          <section className="overview-page__section">
            <SectionHeader
              title="Tested models"
              description="Latest evidence for each model/runtime/hardware cohort. No cross-cohort recommendation is shown unless comparability has been established explicitly."
            />
            <DataTable
              caption="Tested model evidence"
              columns={MODEL_COLUMNS}
              rows={models}
              rowKey={(model) => model.cohort_key}
            />
          </section>
        )}

        <section className="overview-page__section">
          <SectionHeader
            title="Recent runs"
            description="Immutable completed evidence, newest first."
          />
          <DataTable
            caption="Recent evaluation runs"
            columns={RUN_COLUMNS}
            rows={runs.slice(0, 8)}
            rowKey={(run) => run.run_id}
            emptyMessage="No completed runs yet."
          />
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
          title="Loading tested models"
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
    <OverviewView
      {...state.data}
      onFindBestSetup={onFindBestSetup}
      onTestModel={onTestModel}
    />
  );
}
