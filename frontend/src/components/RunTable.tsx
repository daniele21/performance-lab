import { DataTable, type DataColumn } from "./DataTable";
import { Status } from "./Status";

export interface RunTableRow {
  runId: string;
  model: string;
  scenario: string;
  status: "succeeded" | "failed" | "cancelled" | "running" | "planned";
  completedAt?: string | null;
}

const STATUS_TONES: Record<RunTableRow["status"], "neutral" | "success" | "warning" | "error"> = {
  succeeded: "success",
  failed: "error",
  cancelled: "warning",
  running: "neutral",
  planned: "neutral",
};

const RUN_COLUMNS: readonly DataColumn<RunTableRow>[] = [
  { id: "model", header: "Model", render: (row) => row.model },
  { id: "scenario", header: "Scenario", render: (row) => row.scenario },
  {
    id: "status",
    header: "Status",
    render: (row) => <Status tone={STATUS_TONES[row.status]}>{row.status}</Status>,
  },
  {
    id: "completed",
    header: "Completed",
    render: (row) => row.completedAt ?? "—",
  },
];

interface RunTableProps {
  rows: readonly RunTableRow[];
}

export function RunTable({ rows }: RunTableProps) {
  return (
    <DataTable
      caption="Evaluation runs"
      columns={RUN_COLUMNS}
      rows={rows}
      rowKey={(row) => row.runId}
      emptyMessage="No completed runs yet."
    />
  );
}
