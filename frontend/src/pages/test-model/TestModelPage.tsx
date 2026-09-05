import { useEffect, useMemo, useState } from "react";

import {
  launchRunJob,
  listScenarios,
  listTargets,
  preflightRun,
  probeEndpoint,
  probeTarget,
} from "../../api";
import type {
  EndpointConnectionInput,
  EndpointProbeReadModel,
  RunPreflightReadModel,
  ScenarioKind,
  ScenarioSummaryReadModel,
  TargetSummaryReadModel,
} from "../../api";
import {
  AppShell,
  Button,
  Disclosure,
  EmptyState,
  ErrorState,
  Field,
  LoadingState,
  PageHeader,
  SectionHeader,
  Select,
  Status,
  Toggle,
} from "../../components";
import {
  DEFAULT_CONNECTION_PREFERENCE,
  getConnectionPreference,
  setConnectionPreference,
  type ConnectionPreference,
} from "../../connection-preference";
import "./test-model.css";

type WizardStep = "model" | "scenario" | "test" | "review";
type ModelSource = "configured" | "local";
type ConnectionDraft = ConnectionPreference;

const STEPS: readonly { id: WizardStep; label: string }[] = [
  { id: "model", label: "Model" },
  { id: "scenario", label: "Scenario" },
  { id: "test", label: "Test" },
  { id: "review", label: "Review" },
];

interface WizardSelection {
  targetId: string;
  modelId: string;
  scenario: ScenarioKind;
  useHostTelemetry: boolean;
}

interface TestModelViewProps {
  targets: TargetSummaryReadModel[];
  scenarios: ScenarioSummaryReadModel[];
  selection: WizardSelection;
  step: WizardStep;
  preflight: RunPreflightReadModel | null;
  modelSource?: ModelSource;
  connection?: ConnectionDraft;
  probe?: EndpointProbeReadModel | null;
  probeLoading?: boolean;
  probeError?: string | null;
  preflightLoading?: boolean;
  preflightError?: string | null;
  launchLoading?: boolean;
  launchError?: string | null;
  onSelectionChange?: (selection: WizardSelection) => void;
  onModelSourceChange?: (source: ModelSource) => void;
  onConnectionChange?: (connection: ConnectionDraft) => void;
  onProbe?: () => void;
  onStepChange?: (step: WizardStep) => void;
  onReview?: () => void;
  onLaunch?: () => void;
}

function stepIndex(step: WizardStep) {
  return STEPS.findIndex((item) => item.id === step);
}

function capabilityTone(state: "supported" | "unsupported" | "unknown") {
  if (state === "supported") return "success" as const;
  if (state === "unsupported") return "warning" as const;
  return "neutral" as const;
}

function renderRuntimeValue(value: unknown) {
  if (value === null || value === undefined) return "Unknown";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

export function TestModelView({
  targets,
  scenarios,
  selection,
  step,
  preflight,
  modelSource = "configured",
  connection = DEFAULT_CONNECTION_PREFERENCE,
  probe = null,
  probeLoading = false,
  probeError = null,
  preflightLoading = false,
  preflightError = null,
  launchLoading = false,
  launchError = null,
  onSelectionChange,
  onModelSourceChange,
  onConnectionChange,
  onProbe,
  onStepChange,
  onReview,
  onLaunch,
}: TestModelViewProps) {
  const currentIndex = stepIndex(step);
  const selectedScenario = scenarios.find((item) => item.scenario === selection.scenario);
  const selectedDiscoveredModel = probe?.models.find((item) => item.model_id === selection.modelId);
  const hasSelectedTarget = Boolean(selection.targetId);
  const hasDiscoveredModels = Boolean(probe?.healthy && probe.models.length);
  const configuredDiscoveryFailed = Boolean(
    probeError || (probe && (!probe.healthy || !probe.models.length)),
  );
  const showConfiguredModels = hasSelectedTarget && !probeLoading && hasDiscoveredModels;
  const showConfiguredFallback = hasSelectedTarget && !probeLoading && configuredDiscoveryFailed;
  const discoveredModelCount = probe?.models.length ?? 0;
  const discoveredModelNoun = discoveredModelCount === 1 ? "model" : "models";
  const configuredModelDescription = probe
    ? `${discoveredModelCount} ${discoveredModelNoun} reported by ${probe.endpoint_identity}.`
    : "";
  const canLeaveModel = Boolean(selection.targetId && selection.modelId.trim());
  const canLeaveScenario = Boolean(selectedScenario?.supported);

  const updateSelection = (patch: Partial<WizardSelection>) => {
    onSelectionChange?.({ ...selection, ...patch });
  };

  const updateConnection = (patch: Partial<ConnectionDraft>) => {
    onConnectionChange?.({ ...connection, ...patch });
  };

  const goBack = () => {
    const previous = STEPS[currentIndex - 1];
    if (previous) onStepChange?.(previous.id);
  };

  const goForward = () => {
    const next = STEPS[currentIndex + 1];
    if (!next) return;
    if (next.id === "review") onReview?.();
    onStepChange?.(next.id);
  };

  return (
    <AppShell activePrimary="Test a model">
      <div className="test-model-page">
        <PageHeader
          eyebrow="New evaluation"
          title="Test a model"
          description="Connect to a local model server or use an existing target, choose what you want to learn, then review the exact frozen execution before launch."
        />

        <ol className="test-model-steps" aria-label="Evaluation setup progress">
          {STEPS.map((item, index) => (
            <li data-active={item.id === step ? "true" : undefined} key={item.id}>
              <span>{index + 1}</span>
              <strong>{item.label}</strong>
            </li>
          ))}
        </ol>

        <section className="test-model-panel">
          {step === "model" ? (
            <>
              <SectionHeader
                title="Which model are you testing?"
                description="Performance Lab talks to the inference server; the browser never calls the model runtime directly."
              />
              <Select
                label="Model source"
                value={modelSource}
                onChange={(event) =>
                  onModelSourceChange?.(event.currentTarget.value as ModelSource)
                }
              >
                <option value="local">Connect local server</option>
                <option value="configured" disabled={!targets.length}>
                  Configured target{targets.length ? "" : " · none available"}
                </option>
              </Select>

              {modelSource === "configured" ? (
                <div className="test-model-fields">
                  <Select
                    label="Target"
                    value={selection.targetId}
                    onChange={(event) =>
                      updateSelection({ targetId: event.currentTarget.value, modelId: "" })
                    }
                  >
                    <option value="">Choose a target</option>
                    {targets.map((target) => (
                      <option key={target.target_id} value={target.target_id}>
                        {target.display_name} · {target.endpoint_identity}
                      </option>
                    ))}
                  </Select>

                  {hasSelectedTarget && probeLoading ? (
                    <p className="test-model-disclosure-note" role="status">
                      Discovering models from this target…
                    </p>
                  ) : null}

                  {hasSelectedTarget && probeError ? (
                    <p className="test-model-connection-error" role="alert">
                      {probeError}
                    </p>
                  ) : null}

                  {showConfiguredModels && probe ? (
                    <Select
                      label="Model"
                      description={configuredModelDescription}
                      value={selection.modelId}
                      onChange={(event) => updateSelection({ modelId: event.currentTarget.value })}
                    >
                      {probe.models.map((model) => (
                        <option key={model.model_id} value={model.model_id}>
                          {model.model_id}
                        </option>
                      ))}
                    </Select>
                  ) : null}

                  {showConfiguredFallback ? (
                    <>
                      {probe?.warning ? (
                        <p className="test-model-discovery-warning">{probe.warning}</p>
                      ) : null}
                      <Field
                        label="Model ID"
                        description="Automatic discovery is unavailable for this target. Enter a model ID only as a fallback."
                        value={selection.modelId}
                        onChange={(event) =>
                          updateSelection({ modelId: event.currentTarget.value })
                        }
                        placeholder="e.g. local-model"
                      />
                    </>
                  ) : null}
                </div>
              ) : (
                <div className="test-model-connection">
                  <div className="test-model-connection-grid">
                    <Field
                      label="Connection name"
                      value={connection.displayName}
                      onChange={(event) =>
                        updateConnection({ displayName: event.currentTarget.value })
                      }
                    />
                    <Select
                      label="Server type"
                      value={connection.serverType}
                      onChange={(event) =>
                        updateConnection({
                          serverType: event.currentTarget.value as ConnectionDraft["serverType"],
                        })
                      }
                    >
                      <option value="local_llm_server">Local LLM Server</option>
                      <option value="openai_compatible">OpenAI-compatible</option>
                    </Select>
                    <Field
                      label="Host"
                      description="Local connections remain restricted to localhost/loopback."
                      value={connection.host}
                      onChange={(event) => updateConnection({ host: event.currentTarget.value })}
                      placeholder="127.0.0.1"
                    />
                    <Field
                      label="Port"
                      type="number"
                      min="1"
                      max="65535"
                      value={connection.port}
                      onChange={(event) => updateConnection({ port: event.currentTarget.value })}
                      placeholder="1235"
                    />
                  </div>

                  <Disclosure summary="Advanced connection settings">
                    <div className="test-model-connection-grid">
                      <Field
                        label="API base path"
                        description="OpenAI-compatible servers normally expose /v1/."
                        value={connection.basePath}
                        onChange={(event) =>
                          updateConnection({ basePath: event.currentTarget.value })
                        }
                      />
                      <Field
                        label="Probe timeout (seconds)"
                        type="number"
                        min="0.1"
                        max="120"
                        step="0.1"
                        value={connection.timeoutSeconds}
                        onChange={(event) =>
                          updateConnection({ timeoutSeconds: event.currentTarget.value })
                        }
                      />
                    </div>
                  </Disclosure>

                  <div className="test-model-connect-action">
                    <Button variant="primary" disabled={probeLoading} onClick={onProbe}>
                      {probeLoading ? "Connecting…" : "Connect & discover"}
                    </Button>
                    <p>
                      Successful loopback connection details are saved in this browser. Credentials
                      are never stored.
                    </p>
                  </div>

                  {probeError ? (
                    <p className="test-model-connection-error" role="alert">
                      {probeError}
                    </p>
                  ) : null}

                  {probe ? (
                    <div className="test-model-discovery" aria-live="polite">
                      <div className="test-model-discovery-heading">
                        <div>
                          <strong>
                            {probe.healthy ? "Connection discovered" : "Connection unavailable"}
                          </strong>
                          <span>{probe.endpoint_identity}</span>
                        </div>
                        <Status tone={probe.healthy ? "success" : "error"}>
                          {probe.healthy ? "Connected" : "Unavailable"}
                        </Status>
                      </div>

                      {probe.warning ? (
                        <p className="test-model-discovery-warning">{probe.warning}</p>
                      ) : null}

                      {probe.healthy && probe.target ? (
                        probe.models.length ? (
                          <Select
                            label="Model"
                            description={`${probe.models.length} model${probe.models.length === 1 ? "" : "s"} reported by the server.`}
                            value={selection.modelId}
                            onChange={(event) =>
                              updateSelection({ modelId: event.currentTarget.value })
                            }
                          >
                            {probe.models.map((model) => (
                              <option key={model.model_id} value={model.model_id}>
                                {model.model_id}
                              </option>
                            ))}
                          </Select>
                        ) : (
                          <p className="test-model-discovery-warning">
                            The endpoint is reachable, but GET /v1/models did not report a model.
                          </p>
                        )
                      ) : null}

                      {probe.capabilities.length ? (
                        <div
                          className="test-model-capabilities"
                          aria-label="Discovered endpoint capabilities"
                        >
                          {probe.capabilities.map((capability) => (
                            <div key={capability.name}>
                              <span>{capability.name.replaceAll("_", " ")}</span>
                              <Status tone={capabilityTone(capability.state)}>
                                {capability.state}
                              </Status>
                            </div>
                          ))}
                        </div>
                      ) : null}

                      {probe.supported_generation_parameters.length ? (
                        <Disclosure summary="Request controls available through this adapter">
                          <div className="test-model-parameter-tags">
                            {probe.supported_generation_parameters.map((parameter) => (
                              <code key={parameter}>{parameter}</code>
                            ))}
                          </div>
                          <p className="test-model-disclosure-note">
                            These names describe controls the Performance Lab adapter can send. They
                            do not imply server-specific min/max ranges when the runtime has not
                            published them.
                          </p>
                        </Disclosure>
                      ) : null}

                      {selectedDiscoveredModel?.runtime_parameters.length ? (
                        <Disclosure summary="Runtime configuration reported by Local LLM Server">
                          <dl className="test-model-runtime-parameters">
                            {selectedDiscoveredModel.runtime_parameters.map((parameter) => (
                              <div key={parameter.name}>
                                <dt>{parameter.name}</dt>
                                <dd>{renderRuntimeValue(parameter.current_value)}</dd>
                              </div>
                            ))}
                          </dl>
                          <p className="test-model-disclosure-note">
                            Runtime-load settings are evidence only in this slice. Performance Lab
                            does not take ownership of loading or reconfiguring the external
                            runtime.
                          </p>
                        </Disclosure>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              )}
            </>
          ) : null}

          {step === "scenario" ? (
            <>
              <SectionHeader
                title="What do you want to learn?"
                description="Only scenarios with a real execution contract can be selected."
              />
              <div className="test-model-scenarios">
                {scenarios.map((scenario) => (
                  <button
                    className="test-model-scenario"
                    data-selected={scenario.scenario === selection.scenario ? "true" : undefined}
                    disabled={!scenario.supported}
                    key={scenario.scenario}
                    type="button"
                    aria-pressed={scenario.scenario === selection.scenario}
                    onClick={() => updateSelection({ scenario: scenario.scenario })}
                  >
                    <strong>{scenario.title}</strong>
                    <span>{scenario.description}</span>
                    {!scenario.supported && scenario.blocked_reason ? (
                      <small>{scenario.blocked_reason}</small>
                    ) : null}
                  </button>
                ))}
              </div>
            </>
          ) : null}

          {step === "test" ? (
            <>
              <SectionHeader
                title="Test settings"
                description="The selected scenario supplies the benchmark suite and deterministic defaults. Endpoint capabilities stay visible without exposing unsupported controls as if they worked."
              />
              <Toggle
                label="Collect host telemetry"
                description="Add host-level resource evidence when the local collector is available."
                checked={selection.useHostTelemetry}
                onChange={(event) =>
                  updateSelection({ useHostTelemetry: event.currentTarget.checked })
                }
              />
              {probe?.supported_generation_parameters.length ? (
                <Disclosure summary="Discovered request parameters">
                  <div className="test-model-parameter-tags">
                    {probe.supported_generation_parameters.map((parameter) => (
                      <code key={parameter}>{parameter}</code>
                    ))}
                  </div>
                  <p className="test-model-disclosure-note">
                    The current starter scenario keeps its versioned generation defaults. A server
                    must publish a typed configuration contract before Performance Lab can safely
                    offer server-specific ranges instead of guessing them.
                  </p>
                </Disclosure>
              ) : null}
              <Disclosure summary="Advanced execution details">
                <p>
                  General capability uses the canonical starter suite. Dataset snapshots,
                  evaluators, generation settings and load profile are resolved server-side and
                  shown on the frozen Review before launch.
                </p>
              </Disclosure>
            </>
          ) : null}

          {step === "review" ? (
            <ReviewPanel
              preflight={preflight}
              loading={preflightLoading}
              error={preflightError}
              launchLoading={launchLoading}
              launchError={launchError}
              onRetry={onReview}
              onLaunch={onLaunch}
            />
          ) : null}
        </section>

        <div className="test-model-actions">
          <Button variant="quiet" disabled={currentIndex === 0 || launchLoading} onClick={goBack}>
            Back
          </Button>
          {step !== "review" ? (
            <Button
              variant="primary"
              disabled={
                (step === "model" && !canLeaveModel) || (step === "scenario" && !canLeaveScenario)
              }
              onClick={goForward}
            >
              Continue
            </Button>
          ) : null}
        </div>
      </div>
    </AppShell>
  );
}

function ReviewPanel({
  preflight,
  loading,
  error,
  launchLoading,
  launchError,
  onRetry,
  onLaunch,
}: {
  preflight: RunPreflightReadModel | null;
  loading: boolean;
  error: string | null;
  launchLoading: boolean;
  launchError: string | null;
  onRetry?: () => void;
  onLaunch?: () => void;
}) {
  if (loading) {
    return (
      <LoadingState
        title="Freezing execution input"
        description="Validating target, suite, datasets and exact run configuration."
      />
    );
  }
  if (error) {
    return (
      <ErrorState
        title="Could not prepare this run"
        description={error}
        action={<Button onClick={onRetry}>Try again</Button>}
      />
    );
  }
  if (!preflight) {
    return (
      <EmptyState
        title="Review not prepared"
        description="Return to the test settings and prepare the frozen execution preview."
      />
    );
  }
  if (!preflight.can_run || !preflight.preview) {
    return (
      <ErrorState
        title="This run cannot be prepared yet"
        description={
          preflight.issues.map((issue) => issue.message).join(" · ") ||
          "The server did not return an executable preview."
        }
        action={<Button onClick={onRetry}>Validate again</Button>}
      />
    );
  }

  const preview = preflight.preview;
  return (
    <div className="test-model-review">
      <SectionHeader
        title="Review frozen execution"
        description="This is the exact configuration Performance Lab will pass to the starter runner. Runtime and hardware identity are resolved at launch, after endpoint probing."
      />
      <Status tone="success">Preflight passed</Status>
      <dl className="test-model-review-grid">
        <div>
          <dt>Model</dt>
          <dd>{preview.config.model_id}</dd>
        </div>
        <div>
          <dt>Target</dt>
          <dd>{preview.target.display_name}</dd>
        </div>
        <div>
          <dt>Suite</dt>
          <dd>
            {preview.suite.suite_id} · v{preview.suite.suite_version}
          </dd>
        </div>
        <div>
          <dt>Datasets</dt>
          <dd>{preview.datasets.length}</dd>
        </div>
        <div>
          <dt>Evaluators</dt>
          <dd>{preview.evaluator_ids.length}</dd>
        </div>
        <div>
          <dt>Host telemetry</dt>
          <dd>{preview.config.use_host_telemetry ? "Enabled" : "Disabled"}</dd>
        </div>
      </dl>
      <div className="test-model-digest">
        <span>Frozen config digest</span>
        <code>{preview.config_digest}</code>
      </div>
      <Disclosure summary="Show exact frozen configuration">
        <pre className="test-model-config">{JSON.stringify(preview, null, 2)}</pre>
      </Disclosure>
      <div className="test-model-launch">
        <Button variant="primary" disabled={launchLoading} onClick={onLaunch}>
          {launchLoading ? "Starting run…" : "Run test"}
        </Button>
        <p>
          The run continues in the local Performance Lab process if this browser view disconnects.
        </p>
      </div>
      {launchError ? (
        <p className="test-model-launch-error" role="alert">
          {launchError}
        </p>
      ) : null}
    </div>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; targets: TargetSummaryReadModel[]; scenarios: ScenarioSummaryReadModel[] }
  | { status: "error"; message: string };

interface TestModelPageProps {
  onLaunched?: (jobId: string) => void;
}

function connectionRequest(connection: ConnectionDraft): EndpointConnectionInput {
  const path = connection.basePath.trim() || "/v1/";
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return {
    display_name: connection.displayName.trim() || "Local model server",
    base_url: `http://${connection.host.trim()}:${connection.port.trim()}${normalizedPath}`,
    server_type: connection.serverType,
    timeout_seconds: Number(connection.timeoutSeconds),
  };
}

export function TestModelPage({ onLaunched }: TestModelPageProps) {
  const [catalog, setCatalog] = useState<LoadState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [step, setStep] = useState<WizardStep>("model");
  const [modelSource, setModelSource] = useState<ModelSource>("configured");
  const [connection, setConnection] = useState<ConnectionDraft>(
    () => getConnectionPreference() ?? DEFAULT_CONNECTION_PREFERENCE,
  );
  const [probe, setProbe] = useState<EndpointProbeReadModel | null>(null);
  const [probeLoading, setProbeLoading] = useState(false);
  const [probeError, setProbeError] = useState<string | null>(null);
  const [selection, setSelection] = useState<WizardSelection>({
    targetId: "",
    modelId: "",
    scenario: "general_capability",
    useHostTelemetry: false,
  });
  const [preflight, setPreflight] = useState<RunPreflightReadModel | null>(null);
  const [preflightLoading, setPreflightLoading] = useState(false);
  const [preflightError, setPreflightError] = useState<string | null>(null);
  const [launchLoading, setLaunchLoading] = useState(false);
  const [launchError, setLaunchError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      listTargets({ signal: controller.signal }),
      listScenarios({ signal: controller.signal }),
    ])
      .then(([targets, scenarios]) => {
        setCatalog({ status: "ready", targets, scenarios });
        setModelSource(targets.length ? "configured" : "local");
        setSelection((current) => ({
          ...current,
          targetId: current.targetId || targets[0]?.target_id || "",
          scenario: scenarios.find((scenario) => scenario.supported)?.scenario ?? current.scenario,
        }));
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setCatalog({
          status: "error",
          message: error instanceof Error ? error.message : "Setup catalog could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt]);

  useEffect(() => {
    if (catalog.status !== "ready" || modelSource !== "configured" || !selection.targetId) {
      return;
    }

    const targetId = selection.targetId;
    const controller = new AbortController();
    setProbeLoading(true);
    setProbeError(null);
    setProbe(null);
    setPreflight(null);

    probeTarget(targetId, { signal: controller.signal })
      .then((result) => {
        if (controller.signal.aborted) return;
        setProbe(result);
        setSelection((current) => {
          if (current.targetId !== targetId) return current;
          const currentStillAvailable = result.models.some(
            (model) => model.model_id === current.modelId,
          );
          const firstDiscoveredModelId = result.models[0]?.model_id ?? "";
          return {
            ...current,
            modelId: currentStillAvailable ? current.modelId : firstDiscoveredModelId,
          };
        });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setSelection((current) =>
          current.targetId === targetId ? { ...current, modelId: "" } : current,
        );
        if (error instanceof Error) {
          setProbeError(error.message);
          return;
        }
        setProbeError("Models could not be discovered for this target.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setProbeLoading(false);
      });

    return () => controller.abort();
  }, [catalog.status, modelSource, selection.targetId]);

  const request = useMemo(
    () => ({
      target_id: selection.targetId,
      model_id: selection.modelId.trim(),
      scenario: selection.scenario,
      use_host_telemetry: selection.useHostTelemetry,
    }),
    [selection],
  );

  const connectAndDiscover = () => {
    setProbeLoading(true);
    setProbeError(null);
    setProbe(null);
    setPreflight(null);
    probeEndpoint(connectionRequest(connection))
      .then((result) => {
        setProbe(result);
        if (result.healthy && result.target) {
          setConnectionPreference(connection);
          setSelection((current) => ({
            ...current,
            targetId: result.target?.target_id ?? "",
            modelId: result.models[0]?.model_id ?? "",
          }));
        } else {
          setSelection((current) => ({ ...current, targetId: "", modelId: "" }));
        }
      })
      .catch((error: unknown) => {
        setSelection((current) => ({ ...current, targetId: "", modelId: "" }));
        setProbeError(
          error instanceof Error ? error.message : "The local server could not be probed.",
        );
      })
      .finally(() => setProbeLoading(false));
  };

  const prepareReview = () => {
    setPreflightLoading(true);
    setPreflightError(null);
    setLaunchError(null);
    setPreflight(null);
    preflightRun(request)
      .then(setPreflight)
      .catch((error: unknown) =>
        setPreflightError(
          error instanceof Error ? error.message : "Execution preview could not be prepared.",
        ),
      )
      .finally(() => setPreflightLoading(false));
  };

  const launch = () => {
    if (!preflight?.can_run || !preflight.preview) return;
    setLaunchLoading(true);
    setLaunchError(null);
    launchRunJob({ preflight: request, config_digest: preflight.preview.config_digest })
      .then((job) => onLaunched?.(job.job_id))
      .catch((error: unknown) =>
        setLaunchError(error instanceof Error ? error.message : "The run could not be started."),
      )
      .finally(() => setLaunchLoading(false));
  };

  if (catalog.status === "loading") {
    return (
      <AppShell activePrimary="Test a model">
        <LoadingState
          title="Loading evaluation setup"
          description="Reading configured targets and supported scenarios."
        />
      </AppShell>
    );
  }
  if (catalog.status === "error") {
    return (
      <AppShell activePrimary="Test a model">
        <ErrorState
          title="Could not load evaluation setup"
          description={catalog.message}
          action={<Button onClick={() => setAttempt((value) => value + 1)}>Try again</Button>}
        />
      </AppShell>
    );
  }

  return (
    <TestModelView
      targets={catalog.targets}
      scenarios={catalog.scenarios}
      selection={selection}
      step={step}
      preflight={preflight}
      modelSource={modelSource}
      connection={connection}
      probe={probe}
      probeLoading={probeLoading}
      probeError={probeError}
      preflightLoading={preflightLoading}
      preflightError={preflightError}
      launchLoading={launchLoading}
      launchError={launchError}
      onSelectionChange={(next) => {
        setSelection(next);
        setPreflight(null);
        setLaunchError(null);
      }}
      onModelSourceChange={(source) => {
        setModelSource(source);
        setProbe(null);
        setProbeError(null);
        setPreflight(null);
        setLaunchError(null);
        if (source === "configured") {
          setSelection((current) => ({
            ...current,
            targetId: catalog.targets[0]?.target_id ?? "",
            modelId: "",
          }));
        } else {
          setSelection((current) => ({ ...current, targetId: "", modelId: "" }));
        }
      }}
      onConnectionChange={(next) => {
        setConnection(next);
        setProbe(null);
        setProbeError(null);
        setPreflight(null);
        setSelection((current) => ({ ...current, targetId: "", modelId: "" }));
      }}
      onProbe={connectAndDiscover}
      onStepChange={setStep}
      onReview={prepareReview}
      onLaunch={launch}
    />
  );
}
