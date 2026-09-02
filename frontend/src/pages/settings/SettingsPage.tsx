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
import { getThemePreference, setThemePreference, type ThemePreference } from "../../theme";
import "../secondary.css";

export type SettingsSection = "model-connections" | "devices-targets" | "appearance" | "advanced";

const SECTION_LABEL: Record<
  SettingsSection,
  "Model connections" | "Devices / targets" | "Appearance" | "Advanced"
> = {
  "model-connections": "Model connections",
  "devices-targets": "Devices / targets",
  appearance: "Appearance",
  advanced: "Advanced",
};

const SECTION_DESCRIPTION: Record<SettingsSection, string> = {
  "model-connections":
    "Performance Lab evaluates external serving runtimes without taking ownership of model loading or runtime lifecycle.",
  "devices-targets":
    "Configured evaluation targets identify where requests run and which backend-reported capabilities are available.",
  appearance:
    "Choose the workspace theme. Light is the canonical default; Dark is optional and System follows your operating system.",
  advanced:
    "Inspect runtime ownership and target capability boundaries without promoting backend configuration into browser-owned state.",
};

const CONNECTION_COLUMNS: readonly DataColumn<TargetSummaryReadModel>[] = [
  { id: "profile", header: "Connection profile", render: (item) => item.endpoint_profile_id },
  { id: "adapter", header: "Adapter", render: (item) => item.adapter_type },
  {
    id: "identity",
    header: "Safe endpoint identity",
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

const APPEARANCE_OPTIONS: readonly {
  value: ThemePreference;
  label: string;
  description: string;
}[] = [
  {
    value: "light",
    label: "Light",
    description: "Canonical Performance Lab workspace. Bright, calm and evidence-first.",
  },
  {
    value: "dark",
    label: "Dark",
    description: "Lower-luminance workspace using the same semantic hierarchy and evidence colors.",
  },
  {
    value: "system",
    label: "System",
    description: "Follow the operating system light or dark appearance automatically.",
  },
];

function AppearanceSettings() {
  const [preference, setPreference] = useState<ThemePreference>(getThemePreference);

  return (
    <fieldset className="appearance-settings">
      <legend>Theme</legend>
      <p className="appearance-settings__description">
        Light is the default product reference. Your choice is stored only in this browser.
      </p>
      <div className="appearance-settings__options">
        {APPEARANCE_OPTIONS.map((option) => (
          <label className="appearance-option" key={option.value}>
            <input
              type="radio"
              name="theme"
              value={option.value}
              checked={preference === option.value}
              onChange={() => {
                setPreference(option.value);
                setThemePreference(option.value);
              }}
            />
            <span className="appearance-option__copy">
              <strong>{option.label}</strong>
              <span>{option.description}</span>
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

interface SettingsViewProps {
  section: SettingsSection;
  targets: TargetSummaryReadModel[];
}

export function SettingsView({ section, targets }: SettingsViewProps) {
  const label = SECTION_LABEL[section];

  return (
    <AppShell activeSecondary={label}>
      <div className="secondary-page">
        <PageHeader eyebrow="Settings" title={label} description={SECTION_DESCRIPTION[section]} />

        {section === "model-connections" &&
          (targets.length ? (
            <DataTable
              caption="Configured model connection profiles used by evaluation targets"
              columns={CONNECTION_COLUMNS}
              rows={targets}
              rowKey={(item) => `${item.endpoint_profile_id}:${item.target_id}`}
            />
          ) : (
            <EmptyState
              title="No model connections configured"
              description="Use Test a model to connect and discover a local server, or configure an evaluation target in the backend. Session connections are not presented as persisted settings."
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

        {section === "appearance" && <AppearanceSettings />}

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
                Target capabilities come from backend-owned contracts. Unknown capabilities remain
                unknown rather than being guessed in the browser.
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
  const [state, setState] = useState<LoadState>(() =>
    section === "appearance" ? { status: "ready", targets: [] } : { status: "loading" },
  );
  const label = SECTION_LABEL[section];

  useEffect(() => {
    if (section === "appearance") {
      setState({ status: "ready", targets: [] });
      return;
    }

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
  }, [attempt, section]);

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
