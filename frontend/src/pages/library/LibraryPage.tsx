import { useEffect, useState } from "react";

import {
  listBaselines,
  listDatasets,
  listRegressionPolicies,
  listSuites,
  type BaselineSummaryReadModel,
  type DatasetSummaryReadModel,
  type PolicySummaryReadModel,
  type SuiteSummaryReadModel,
} from "../../api";
import {
  AppShell,
  Button,
  DataTable,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  type DataColumn,
} from "../../components";
import "../secondary.css";

export type LibrarySection = "test-suites" | "datasets" | "baselines" | "regression-policies";

interface LibraryData {
  suites: SuiteSummaryReadModel[];
  datasets: DatasetSummaryReadModel[];
  baselines: BaselineSummaryReadModel[];
  policies: PolicySummaryReadModel[];
}

const EMPTY_DATA: LibraryData = { suites: [], datasets: [], baselines: [], policies: [] };

const SECTION_LABEL: Record<
  LibrarySection,
  "Test suites" | "Datasets" | "Baselines" | "Regression policies"
> = {
  "test-suites": "Test suites",
  datasets: "Datasets",
  baselines: "Baselines",
  "regression-policies": "Regression policies",
};

const SUITE_COLUMNS: readonly DataColumn<SuiteSummaryReadModel>[] = [
  { id: "suite", header: "Suite", render: (item) => item.suite_id },
  { id: "version", header: "Version", render: (item) => item.suite_version },
  { id: "tasks", header: "Tasks", render: (item) => String(item.task_count) },
  { id: "task-ids", header: "Task IDs", render: (item) => item.task_ids.join(", ") },
];

const DATASET_COLUMNS: readonly DataColumn<DatasetSummaryReadModel>[] = [
  { id: "dataset", header: "Dataset", render: (item) => item.dataset_id },
  { id: "version", header: "Version", render: (item) => item.dataset_version },
  { id: "split", header: "Split", render: (item) => item.split },
  { id: "samples", header: "Samples", render: (item) => String(item.sample_count) },
  { id: "selection", header: "Selection", render: (item) => item.selection_policy },
];

const BASELINE_COLUMNS: readonly DataColumn<BaselineSummaryReadModel>[] = [
  { id: "baseline", header: "Baseline", render: (item) => item.label ?? item.baseline_id },
  {
    id: "run",
    header: "Run",
    render: (item) => <a href={`#runs/${encodeURIComponent(item.run_id)}`}>{item.run_id}</a>,
  },
  { id: "fingerprint", header: "Fingerprint", render: (item) => item.fingerprint_id },
  {
    id: "selected",
    header: "Selected",
    render: (item) => new Date(item.selected_at).toLocaleString(),
  },
];

const POLICY_COLUMNS: readonly DataColumn<PolicySummaryReadModel>[] = [
  { id: "policy", header: "Policy", render: (item) => item.policy_id },
  { id: "version", header: "Version", render: (item) => item.policy_version },
  { id: "rules", header: "Rules", render: (item) => String(item.rule_count) },
];

interface LibraryViewProps {
  section: LibrarySection;
  data: LibraryData;
}

export function LibraryView({ section, data }: LibraryViewProps) {
  const label = SECTION_LABEL[section];
  const commonDescription =
    "Library is read-only product context. Benchmark definitions and evidence identity remain owned by the backend contracts.";

  return (
    <AppShell activeSecondary={label}>
      <div className="secondary-page">
        <PageHeader eyebrow="Library" title={label} description={commonDescription} />

        {section === "test-suites" &&
          (data.suites.length ? (
            <DataTable
              caption="Available test suites"
              columns={SUITE_COLUMNS}
              rows={data.suites}
              rowKey={(item) => `${item.suite_id}:${item.suite_version}`}
            />
          ) : (
            <EmptyState
              title="No test suites available"
              description="Configured evaluation suites will appear here when exposed by the local Performance Lab backend."
            />
          ))}

        {section === "datasets" &&
          (data.datasets.length ? (
            <DataTable
              caption="Available datasets"
              columns={DATASET_COLUMNS}
              rows={data.datasets}
              rowKey={(item) => `${item.dataset_id}:${item.dataset_version}:${item.split}`}
            />
          ) : (
            <EmptyState
              title="No datasets available"
              description="Frozen dataset identities will appear here when a configured suite exposes them."
            />
          ))}

        {section === "baselines" &&
          (data.baselines.length ? (
            <DataTable
              caption="Selected regression baselines"
              columns={BASELINE_COLUMNS}
              rows={data.baselines}
              rowKey={(item) => item.baseline_id}
            />
          ) : (
            <EmptyState
              title="No baselines selected"
              description="A baseline is an explicit immutable run reference. No implicit baseline is invented here."
            />
          ))}

        {section === "regression-policies" &&
          (data.policies.length ? (
            <DataTable
              caption="Regression policies"
              columns={POLICY_COLUMNS}
              rows={data.policies}
              rowKey={(item) => `${item.policy_id}:${item.policy_version}`}
            />
          ) : (
            <EmptyState
              title="No regression policies available"
              description="Versioned threshold policies will appear here when configured in the backend."
            />
          ))}
      </div>
    </AppShell>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; data: LibraryData }
  | { status: "error"; message: string };

export function LibraryPage({ section }: { section: LibrarySection }) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    Promise.all([
      listSuites({ signal: controller.signal }),
      listDatasets({ signal: controller.signal }),
      listBaselines({ signal: controller.signal }),
      listRegressionPolicies({ signal: controller.signal }),
    ])
      .then(([suites, datasets, baselines, policies]) => {
        setState({ status: "ready", data: { suites, datasets, baselines, policies } });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Library context could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt]);

  const label = SECTION_LABEL[section];
  if (state.status === "loading") {
    return (
      <AppShell activeSecondary={label}>
        <LoadingState
          title={`Loading ${label.toLowerCase()}`}
          description="Reading canonical local configuration and evidence references."
        />
      </AppShell>
    );
  }

  if (state.status === "error") {
    return (
      <AppShell activeSecondary={label}>
        <ErrorState
          title={`Could not load ${label.toLowerCase()}`}
          description={state.message}
          action={<Button onClick={() => setAttempt((value) => value + 1)}>Try again</Button>}
        />
      </AppShell>
    );
  }

  return <LibraryView section={section} data={state.data ?? EMPTY_DATA} />;
}
