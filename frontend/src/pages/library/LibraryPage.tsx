import { useEffect, useState } from "react";

import {
  listBaselines,
  listBenchmarks,
  listDatasets,
  listEvaluators,
  listRegressionPolicies,
  type BaselineSummaryReadModel,
  type DatasetSummaryReadModel,
  type EvaluatorDefinitionReadModel,
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

export type LibrarySection =
  | "benchmarks"
  | "datasets"
  | "evaluators"
  | "baselines"
  | "regression-policies";

interface LibraryData {
  benchmarks: SuiteSummaryReadModel[];
  datasets: DatasetSummaryReadModel[];
  evaluators: EvaluatorDefinitionReadModel[];
  baselines: BaselineSummaryReadModel[];
  policies: PolicySummaryReadModel[];
}

const EMPTY_DATA: LibraryData = {
  benchmarks: [],
  datasets: [],
  evaluators: [],
  baselines: [],
  policies: [],
};

const SECTION_LABEL: Record<LibrarySection, string> = {
  benchmarks: "Benchmarks",
  datasets: "Datasets",
  evaluators: "Evaluators",
  baselines: "Baselines",
  "regression-policies": "Regression policies",
};

const SECTION_DESCRIPTION: Record<LibrarySection, string> = {
  benchmarks:
    "Benchmark definitions describe tasks and protocol context. Execution results remain separate immutable Run evidence.",
  datasets:
    "Versioned dataset snapshots expose their source and immutable identity without implying mutable catalog state.",
  evaluators:
    "Evaluator definitions describe scoring behavior and explanation capability. Weights are contextual, never global.",
  baselines:
    "Baselines are explicit immutable Run references used for regression comparisons; no implicit baseline is selected here.",
  "regression-policies":
    "Versioned regression policies define comparison thresholds without collapsing quality, performance and resources into one score.",
};

const BENCHMARK_COLUMNS: readonly DataColumn<SuiteSummaryReadModel>[] = [
  { id: "benchmark", header: "Benchmark", render: (item) => item.suite_id },
  { id: "version", header: "Version", render: (item) => item.suite_version },
  { id: "tasks", header: "Tasks", render: (item) => String(item.task_count) },
  { id: "task-ids", header: "Task IDs", render: (item) => item.task_ids.join(", ") },
];

const DATASET_COLUMNS: readonly DataColumn<DatasetSummaryReadModel>[] = [
  { id: "dataset", header: "Dataset", render: (item) => item.dataset_id },
  { id: "version", header: "Snapshot", render: (item) => item.dataset_version },
  { id: "source", header: "Source", render: (item) => item.source },
  { id: "split", header: "Split", render: (item) => item.split },
  { id: "samples", header: "Samples", render: (item) => String(item.sample_count) },
  { id: "selection", header: "Selection", render: (item) => item.selection_policy },
  {
    id: "digest",
    header: "Immutable digest",
    render: (item) => <code>{item.content_sha256.slice(0, 12)}…</code>,
  },
];

const EVALUATOR_COLUMNS: readonly DataColumn<EvaluatorDefinitionReadModel>[] = [
  { id: "evaluator", header: "Evaluator", render: (item) => item.evaluator_id },
  { id: "version", header: "Version", render: (item) => item.version },
  { id: "type", header: "Type", render: (item) => item.evaluator_type },
  {
    id: "deterministic",
    header: "Deterministic",
    render: (item) =>
      item.deterministic === null ? "Not reported" : item.deterministic ? "Yes" : "No",
  },
  {
    id: "explanation",
    header: "Explanation",
    render: (item) =>
      item.explanation_supported === null
        ? "Not reported"
        : item.explanation_supported
          ? "Supported"
          : "Unavailable",
  },
  { id: "rules", header: "Rule summary", render: (item) => item.rule_summary ?? "Not reported" },
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

  return (
    <AppShell activeSecondary={label}>
      <div className="secondary-page">
        <PageHeader
          eyebrow="Library"
          title={label}
          description={SECTION_DESCRIPTION[section]}
        />

        {section === "benchmarks" &&
          (data.benchmarks.length ? (
            <DataTable
              caption="Available benchmark definitions"
              columns={BENCHMARK_COLUMNS}
              rows={data.benchmarks}
              rowKey={(item) => `${item.suite_id}:${item.suite_version}`}
            />
          ) : (
            <EmptyState
              title="No benchmarks available"
              description="Configured benchmark definitions will appear here when exposed by the local Performance Lab backend."
            />
          ))}

        {section === "datasets" &&
          (data.datasets.length ? (
            <DataTable
              caption="Available dataset snapshots"
              columns={DATASET_COLUMNS}
              rows={data.datasets}
              rowKey={(item) => `${item.dataset_id}:${item.dataset_version}:${item.split}`}
            />
          ) : (
            <EmptyState
              title="No datasets available"
              description="Frozen dataset identities will appear here when a configured benchmark exposes them."
            />
          ))}

        {section === "evaluators" &&
          (data.evaluators.length ? (
            <DataTable
              caption="Available evaluator definitions"
              columns={EVALUATOR_COLUMNS}
              rows={data.evaluators}
              rowKey={(item) => `${item.evaluator_id}:${item.version}`}
            />
          ) : (
            <EmptyState
              title="No evaluators available"
              description="Evaluator definitions will appear here when registered by the backend."
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

async function loadSection(section: LibrarySection, signal: AbortSignal): Promise<LibraryData> {
  if (section === "benchmarks") {
    return { ...EMPTY_DATA, benchmarks: await listBenchmarks({ signal }) };
  }
  if (section === "datasets") {
    return { ...EMPTY_DATA, datasets: await listDatasets({ signal }) };
  }
  if (section === "evaluators") {
    return { ...EMPTY_DATA, evaluators: await listEvaluators({ signal }) };
  }
  if (section === "baselines") {
    return { ...EMPTY_DATA, baselines: await listBaselines({ signal }) };
  }
  return { ...EMPTY_DATA, policies: await listRegressionPolicies({ signal }) };
}

export function LibraryPage({ section }: { section: LibrarySection }) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    loadSection(section, controller.signal)
      .then((data) => setState({ status: "ready", data }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Library context could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt, section]);

  const label = SECTION_LABEL[section];
  if (state.status === "loading") {
    return (
      <AppShell activeSecondary={label}>
        <LoadingState
          title={`Loading ${label.toLowerCase()}`}
          description="Reading canonical local definitions and evidence references."
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

  return <LibraryView section={section} data={state.data} />;
}
