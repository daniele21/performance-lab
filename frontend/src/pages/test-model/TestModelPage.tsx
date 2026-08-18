import { useEffect, useMemo, useState } from "react";

import { listScenarios, listTargets, preflightRun } from "../../api";
import type {
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
import "./test-model.css";

type WizardStep = "model" | "scenario" | "test" | "review";

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
  preflightLoading?: boolean;
  preflightError?: string | null;
  onSelectionChange?: (selection: WizardSelection) => void;
  onStepChange?: (step: WizardStep) => void;
  onReview?: () => void;
}

function stepIndex(step: WizardStep) {
  return STEPS.findIndex((item) => item.id === step);
}

export function TestModelView({
  targets,
  scenarios,
  selection,
  step,
  preflight,
  preflightLoading = false,
  preflightError = null,
  onSelectionChange,
  onStepChange,
  onReview,
}: TestModelViewProps) {
  const currentIndex = stepIndex(step);
  const selectedScenario = scenarios.find((item) => item.scenario === selection.scenario);
  const canLeaveModel = Boolean(selection.targetId && selection.modelId.trim());
  const canLeaveScenario = Boolean(selectedScenario?.supported);

  const updateSelection = (patch: Partial<WizardSelection>) => {
    onSelectionChange?.({ ...selection, ...patch });
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
          description="Choose the model and what you want to learn. Performance Lab keeps benchmark internals behind sensible defaults, then freezes the exact execution input before launch."
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
                description="Select a registered local target and the model identifier exposed by that endpoint."
              />
              <div className="test-model-fields">
                <Select
                  label="Target"
                  value={selection.targetId}
                  onChange={(event) => updateSelection({ targetId: event.currentTarget.value })}
                >
                  <option value="">Choose a target</option>
                  {targets.map((target) => (
                    <option key={target.target_id} value={target.target_id}>
                      {target.display_name} · {target.endpoint_identity}
                    </option>
                  ))}
                </Select>
                <Field
                  label="Model ID"
                  description="Use the model identifier accepted by the selected endpoint."
                  value={selection.modelId}
                  onChange={(event) => updateSelection({ modelId: event.currentTarget.value })}
                  placeholder="e.g. local-model"
                />
              </div>
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
                description="The selected scenario supplies the benchmark suite and deterministic defaults. Only supported execution controls are exposed here."
              />
              <Toggle
                label="Collect host telemetry"
                description="Add host-level resource evidence when the local collector is available."
                checked={selection.useHostTelemetry}
                onChange={(event) =>
                  updateSelection({ useHostTelemetry: event.currentTarget.checked })
                }
              />
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
              onRetry={onReview}
            />
          ) : null}
        </section>

        <div className="test-model-actions">
          <Button variant="quiet" disabled={currentIndex === 0} onClick={goBack}>
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
  onRetry,
}: {
  preflight: RunPreflightReadModel | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
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
      <div className="test-model-launch-blocked">
        <Button variant="primary" disabled>
          Run test
        </Button>
        <p>
          Launch remains disabled until the server-owned run lifecycle, progress and cancellation
          contract is integrated.
        </p>
      </div>
    </div>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; targets: TargetSummaryReadModel[]; scenarios: ScenarioSummaryReadModel[] }
  | { status: "error"; message: string };

export function TestModelPage() {
  const [catalog, setCatalog] = useState<LoadState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [step, setStep] = useState<WizardStep>("model");
  const [selection, setSelection] = useState<WizardSelection>({
    targetId: "",
    modelId: "",
    scenario: "general_capability",
    useHostTelemetry: false,
  });
  const [preflight, setPreflight] = useState<RunPreflightReadModel | null>(null);
  const [preflightLoading, setPreflightLoading] = useState(false);
  const [preflightError, setPreflightError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      listTargets({ signal: controller.signal }),
      listScenarios({ signal: controller.signal }),
    ])
      .then(([targets, scenarios]) => {
        setCatalog({ status: "ready", targets, scenarios });
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

  const request = useMemo(
    () => ({
      target_id: selection.targetId,
      model_id: selection.modelId.trim(),
      scenario: selection.scenario,
      use_host_telemetry: selection.useHostTelemetry,
    }),
    [selection],
  );

  const prepareReview = () => {
    setPreflightLoading(true);
    setPreflightError(null);
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

  if (catalog.status === "loading") {
    return (
      <AppShell activePrimary="Test a model">
        <LoadingState
          title="Loading evaluation setup"
          description="Reading registered local targets and supported scenarios."
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
  if (!catalog.targets.length) {
    return (
      <AppShell activePrimary="Test a model">
        <EmptyState
          title="No targets configured"
          description="Register a model endpoint before preparing an evaluation."
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
      preflightLoading={preflightLoading}
      preflightError={preflightError}
      onSelectionChange={(next) => {
        setSelection(next);
        setPreflight(null);
      }}
      onStepChange={setStep}
      onReview={prepareReview}
    />
  );
}
