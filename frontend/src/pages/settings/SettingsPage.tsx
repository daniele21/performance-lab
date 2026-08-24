import { useEffect, useState } from "react";

import { listTargets, type TargetSummaryReadModel } from "../../api";
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
import "../secondary.css";

export type SettingsSection = "endpoints" | "devices-targets" | "advanced";

const SECTION_LABEL: Record<SettingsSection, "Endpoints" | "Devices / targets" | "Advanced"> = {
  endpoints: "Endpoints",
  "devices-targets": "Devices / targets",
  advanced: "Advanced",
};

const ENDPOINT_COLUMNS: readonly DataColumn<TargetSummaryReadModel>[] = [
  { id: "profile", header: "Endpoint profile", render: (item) => item.endpoint_profile_id },
  { id: "adapter", header: "Adapter", render: (item) => item.adapter_type },
  {
    id: "identity",
    header: "Safe identity",
    render: (item) => <code>{item.endpoint_identity}</code>,
  },
  { id: "target", header: "Used by target", render: (item) => item.display_name },
];

const TARGET_COLUMNS: readonly DataColumn<TargetSummaryReadModel>[] = [
  { id: "target", header: "Target", render: (item) => item.display_name },
  { id: "id", header: "Target ID", render: (item) => <code>{item.target_id}</code> },
  { id: "adapter", header: "Adapter", render: (item) => item.adapter_type },
  {
    id: "capabilities",
    header: "Capabilities",
    render: (item) => item.capabilities.join(", ") || "Not reported",
  },
];

interface SettingsViewProps {
  section: SettingsSection;
  targets: TargetSummaryReadModel[];
}

export function SettingsView({ section, targets }: SettingsViewProps) {
  const label = SECTION_LABEL[section];

  return (
    <AppShell activeSecondary={label}>
      <div className="secondary-page">
        <PageHeader
          eyebrow="Settings"
          title={label}
          description="Performance Lab keeps serving/runtime ownership outside the product core. These settings expose configured evaluation context without taking over the model runtime."
        />

        {section === "endpoints" &&
          (targets.length ? (
            <DataTable
              caption="Configured endpoint profiles used by targets"
              columns={ENDPOINT_COLUMNS}
              rows={targets}
              rowKey={(item) => `${item.endpoint_profile_id}:${item.target_id}`}
            />
          ) : (
            <EmptyState
              title="No endpoint context configured"
              description="Connect a target through the local Performance Lab configuration before starting an evaluation."
            />
          ))}

        {section === "devices-targets" &&
          (targets.length ? (
            <DataTable
              caption="Configured evaluation targets"
              columns={TARGET_COLUMNS}
              rows={targets}
              rowKey={(item) => item.target_id}
            />
          ) : (
            <EmptyState
              title="No targets configured"
              description="Targets identify where evaluation requests are sent. Device evidence remains explicit and is never inferred from a model name."
            />
          ))}

        {section === "advanced" && (
          <div className="secondary-page__cards" aria-label="Advanced evaluation context">
            <article className="secondary-card">
              <div className="secondary-card__heading">
                <h2>Runtime ownership</h2>
                <Status tone="neutral">External</Status>
              </div>
              <p>
                Performance Lab configures evaluation requests and records evidence. Loading,
                unloading and serving models stays with the connected runtime.
              </p>
            </article>
            <article className="secondary-card">
              <div className="secondary-card__heading">
                <h2>Configured targets</h2>
                <Status tone={targets.length ? "success" : "warning"}>{targets.length}</Status>
              </div>
              <p>
                Advanced target capabilities are read from backend-owned target contracts. Unknown
                capabilities remain unknown rather than being guessed in the UI.
              </p>
            </article>
          </div>
        )}
      </div>
    </AppShell>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; targets: TargetSummaryReadModel[] }
  | { status: "error"; message: string };

export function SettingsPage({ section }: { section: SettingsSection }) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const label = SECTION_LABEL[section];

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    listTargets({ signal: controller.signal })
      .then((targets) => setState({ status: "ready", targets }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message: error instanceof Error ? error.message : "Target context could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt]);

  if (state.status === "loading") {
    return (
      <AppShell activeSecondary={label}>
        <LoadingState
          title={`Loading ${label.toLowerCase()}`}
          description="Reading configured target context from the local backend."
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

  return <SettingsView section={section} targets={state.targets} />;
}
