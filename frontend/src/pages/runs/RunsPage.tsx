import { useEffect, useState } from "react";

import { listRuns } from "../../api";
import type { RunStatus, RunSummaryReadModel } from "../../api";
import {
  AppShell,
  Button,
  DataTable,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  Status,
  type DataColumn,
} from "../../components";
import "./runs.css";

const PAGE_SIZE = 25;

const STATUS_TONE: Record<RunStatus, "neutral" | "success" | "warning" | "error"> = {
  planned: "neutral",
  running: "neutral",
  succeeded: "success",
  failed: "error",
  cancelled: "warning",
};

function formatTimestamp(value: string | null) {
  if (!value) return "Not available";
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString();
}

const RUN_COLUMNS: readonly DataColumn<RunSummaryReadModel>[] = [
  {
    id: "run",
    header: "Run",
    render: (run) => (
      <a className="runs-page__run-link" href={`#runs/${encodeURIComponent(run.run_id)}`}>
        <strong>{run.identity.model_id}</strong>
        <code>{run.run_id}</code>
      </a>
    ),
  },
  {
    id: "suite",
    header: "Test suite",
    render: (run) => `${run.suite_id} · v${run.suite_version}`,
  },
  {
    id: "target",
    header: "Device / target",
    render: (run) =>
      run.identity.hardware_device_id ??
      run.identity.hardware_device_class ??
      run.identity.target_id,
  },
  {
    id: "status",
    header: "Status",
    render: (run) => <Status tone={STATUS_TONE[run.status]}>{run.status}</Status>,
  },
  {
    id: "completed",
    header: "Completed",
    render: (run) => formatTimestamp(run.completed_at),
  },
];

interface RunsViewProps {
  runs: RunSummaryReadModel[];
  offset: number;
  canLoadMore: boolean;
  onPrevious?: () => void;
  onNext?: () => void;
}

export function RunsView({ runs, offset, canLoadMore, onPrevious, onNext }: RunsViewProps) {
  return (
    <AppShell activePrimary="Runs">
      <div className="runs-page">
        <PageHeader
          eyebrow="Immutable evidence"
          title="Runs"
          description="Completed evaluations with their exact model, target, suite and execution identity."
        />

        {runs.length === 0 && offset === 0 ? (
          <EmptyState
            title="No completed runs yet"
            description="Completed evaluations will appear here with their exact model, target, suite and fingerprint identity."
          />
        ) : (
          <>
            <DataTable
              caption="Completed Performance Lab runs"
              columns={RUN_COLUMNS}
              rows={runs}
              rowKey={(run) => run.run_id}
              emptyMessage="No runs exist on this page."
            />
            <nav className="runs-page__pagination" aria-label="Runs pagination">
              <Button disabled={offset === 0} onClick={onPrevious}>
                Previous
              </Button>
              <span>
                Runs {offset + 1}–{offset + runs.length}
              </span>
              <Button disabled={!canLoadMore} onClick={onNext}>
                Next
              </Button>
            </nav>
          </>
        )}
      </div>
    </AppShell>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; runs: RunSummaryReadModel[] }
  | { status: "error"; message: string };

export function RunsPage() {
  const [offset, setOffset] = useState(0);
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    listRuns({ offset, limit: PAGE_SIZE }, { signal: controller.signal })
      .then((runs) => setState({ status: "ready", runs }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Run evidence could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt, offset]);

  if (state.status === "loading") {
    return (
      <AppShell activePrimary="Runs">
        <LoadingState
          title="Loading runs"
          description="Reading immutable completed evidence from local storage."
        />
      </AppShell>
    );
  }

  if (state.status === "error") {
    return (
      <AppShell activePrimary="Runs">
        <ErrorState
          title="Could not load runs"
          description={state.message}
          action={<Button onClick={() => setAttempt((value) => value + 1)}>Try again</Button>}
        />
      </AppShell>
    );
  }

  return (
    <RunsView
      runs={state.runs}
      offset={offset}
      canLoadMore={state.runs.length === PAGE_SIZE}
      onPrevious={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
      onNext={() => setOffset((value) => value + PAGE_SIZE)}
    />
  );
}
