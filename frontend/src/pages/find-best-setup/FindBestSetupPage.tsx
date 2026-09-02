import { useEffect, useMemo, useState } from "react";

import { getCampaignPlanning, launchCampaign, previewCampaignPlan } from "../../api";
import type {
  CampaignPlanPreviewReadModel,
  CampaignPlanPreviewRequest,
  CampaignPlanningContextReadModel,
  CampaignSearchStrategy,
  CampaignTargetPlanningReadModel,
} from "../../api";
import {
  AppShell,
  Button,
  Disclosure,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  SectionHeader,
  Status,
} from "../../components";
import "./find-best-setup.css";

const SETUP_STEPS = ["Goal", "Models", "Optimization", "Review"] as const;
const PRIMARY_SEARCH_STRATEGIES: CampaignSearchStrategy[] = ["quick", "standard", "thorough"];

interface FindBestSetupPageProps {
  onManualTest?: () => void;
  onCampaignStarted?: (campaignId: string) => void;
}

interface FindBestSetupViewProps extends FindBestSetupPageProps {
  context: CampaignPlanningContextReadModel;
}

function unknown(value: string | null) {
  return value ?? "Unknown";
}

function preferredStrategy(target: CampaignTargetPlanningReadModel | undefined): CampaignSearchStrategy {
  if (!target) return "fixed";
  const standard = target.configuration_search_options.find(
    (option) => option.strategy === "standard" && option.available,
  );
  if (standard) return standard.strategy;
  const fixed = target.configuration_search_options.find(
    (option) => option.strategy === "fixed" && option.available,
  );
  if (fixed) return fixed.strategy;
  return target.configuration_search_options.find((option) => option.available)?.strategy ?? "fixed";
}

function formatDuration(seconds: number | null, reason: string) {
  if (seconds === null) return reason;
  if (seconds < 60) return `~${Math.max(1, Math.round(seconds))} sec`;
  return `~${Math.max(1, Math.round(seconds / 60))} min`;
}

export function FindBestSetupView({
  context,
  onManualTest,
  onCampaignStarted,
}: FindBestSetupViewProps) {
  const firstTarget =
    context.targets.find((item) => item.candidates.length > 0) ?? context.targets[0];
  const [step, setStep] = useState(0);
  const [useCaseId, setUseCaseId] = useState(context.use_cases[0]?.use_case_id ?? "");
  const [targetId, setTargetId] = useState(firstTarget?.target.target_id ?? "");
  const [candidateIds, setCandidateIds] = useState<string[]>(
    firstTarget?.candidates.map((candidate) => candidate.candidate_id) ?? [],
  );
  const [strategy, setStrategy] = useState<CampaignSearchStrategy>(preferredStrategy(firstTarget));
  const [preview, setPreview] = useState<CampaignPlanPreviewReadModel | null>(null);
  const [previewState, setPreviewState] = useState<"idle" | "loading" | "error">("idle");
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [launchState, setLaunchState] = useState<"idle" | "loading" | "error">("idle");
  const [launchError, setLaunchError] = useState<string | null>(null);

  const target = useMemo(
    () => context.targets.find((item) => item.target.target_id === targetId) ?? null,
    [context.targets, targetId],
  );
  const useCase = useMemo(
    () => context.use_cases.find((item) => item.use_case_id === useCaseId) ?? null,
    [context.use_cases, useCaseId],
  );
  const selectedStrategy = useMemo(
    () => target?.configuration_search_options.find((option) => option.strategy === strategy) ?? null,
    [strategy, target],
  );

  const currentPlanRequest = (): CampaignPlanPreviewRequest => ({
    use_case_id: useCaseId,
    target_id: targetId,
    candidate_ids: candidateIds,
    configuration_strategy: strategy,
  });

  const invalidatePreview = () => {
    setPreview(null);
    setPreviewState("idle");
    setPreviewError(null);
    setLaunchState("idle");
    setLaunchError(null);
  };

  const selectTarget = (nextTargetId: string) => {
    const nextTarget = context.targets.find((item) => item.target.target_id === nextTargetId);
    setTargetId(nextTargetId);
    setCandidateIds(nextTarget?.candidates.map((candidate) => candidate.candidate_id) ?? []);
    setStrategy(preferredStrategy(nextTarget));
    invalidatePreview();
  };

  const toggleCandidate = (candidateId: string) => {
    setCandidateIds((current) =>
      current.includes(candidateId)
        ? current.filter((item) => item !== candidateId)
        : [...current, candidateId],
    );
    invalidatePreview();
  };

  const selectStrategy = (nextStrategy: CampaignSearchStrategy) => {
    setStrategy(nextStrategy);
    invalidatePreview();
  };

  const buildPreview = async () => {
    if (!useCase || !target || candidateIds.length === 0 || !selectedStrategy?.available) return;
    setPreviewState("loading");
    setPreviewError(null);
    try {
      const result = await previewCampaignPlan(currentPlanRequest());
      if (!result.can_plan) {
        setPreview(null);
        setPreviewState("error");
        setPreviewError(result.issues.map((issue) => issue.message).join(" · "));
        return;
      }
      setPreview(result);
      setPreviewState("idle");
      setStep(3);
    } catch (error: unknown) {
      setPreview(null);
      setPreviewState("error");
      setPreviewError(error instanceof Error ? error.message : "Evaluation plan could not be built.");
    }
  };

  const startCampaign = async () => {
    if (!preview?.execution_available || !preview.plan_digest) return;
    setLaunchState("loading");
    setLaunchError(null);
    try {
      const campaign = await launchCampaign({
        plan: currentPlanRequest(),
        plan_digest: preview.plan_digest,
      });
      setLaunchState("idle");
      onCampaignStarted?.(campaign.campaign_id);
    } catch (error: unknown) {
      setLaunchState("error");
      setLaunchError(
        error instanceof Error ? error.message : "The evaluation campaign could not be started.",
      );
    }
  };

  if (context.use_cases.length === 0) {
    return (
      <AppShell activePrimary="Find best setup">
        <EmptyState
          title="No use cases available"
          description="Performance Lab has no versioned benchmark mapping available for campaign planning."
        />
      </AppShell>
    );
  }

  if (context.targets.length === 0) {
    return (
      <AppShell activePrimary="Find best setup">
        <EmptyState
          title="No model target connected"
          description="Connect or configure a model target before building a best-setup plan."
          action={<Button onClick={onManualTest}>Test a model</Button>}
        />
      </AppShell>
    );
  }

  const primaryOptions =
    target?.configuration_search_options.filter((option) =>
      PRIMARY_SEARCH_STRATEGIES.includes(option.strategy),
    ) ?? [];
  const fixedOption = target?.configuration_search_options.find((option) => option.strategy === "fixed");
  const customOption = target?.configuration_search_options.find(
    (option) => option.strategy === "custom",
  );
  const showFixedFallback = Boolean(
    fixedOption?.available && primaryOptions.every((option) => !option.available),
  );
  const setupStatus =
    step === 3 && preview
      ? preview.execution_available
        ? { label: "Ready to evaluate", tone: "success" as const }
        : { label: "Needs attention", tone: "warning" as const }
      : { label: "Draft", tone: "neutral" as const };

  return (
    <AppShell activePrimary="Find best setup">
      <div className="best-setup-page">
        <PageHeader
          title="Find best setup"
          description="Tell Performance Lab what the model needs to do and where it will run. We'll compare eligible models and configurations, then explain the best evidence-backed fit."
          actions={
            <Button variant="quiet" onClick={onManualTest}>
              Test one model instead
            </Button>
          }
        />

        <ol className="best-setup-steps" aria-label="Best setup progress">
          {SETUP_STEPS.map((label, index) => (
            <li
              aria-current={index === step ? "step" : undefined}
              data-active={index === step ? "true" : undefined}
              data-complete={index < step ? "true" : undefined}
              key={label}
            >
              <span>{index + 1}</span>
              <strong>{label}</strong>
            </li>
          ))}
        </ol>

        <div className="best-setup-workspace">
          <section className="best-setup-panel" aria-live="polite">
            {step === 0 ? (
              <>
                <SectionHeader
                  title="What do you want to optimize?"
                  description="Choose the use case that best describes the decision you need to make."
                />
                <div className="best-setup-choice-list">
                  {context.use_cases.map((item) => (
                    <label
                      className="best-setup-choice"
                      data-selected={item.use_case_id === useCaseId}
                      key={item.use_case_id}
                    >
                      <input
                        type="radio"
                        name="use-case"
                        value={item.use_case_id}
                        checked={item.use_case_id === useCaseId}
                        onChange={() => {
                          setUseCaseId(item.use_case_id);
                          invalidatePreview();
                        }}
                      />
                      <span>
                        <strong>{item.title}</strong>
                        <small>{item.description}</small>
                      </span>
                    </label>
                  ))}
                </div>

                <div className="best-setup-device-block">
                  <SectionHeader
                    title="Where will it run?"
                    description="Candidates and evidence stay scoped to this target/device."
                  />
                  <label className="best-setup-field">
                    <span>Target / device</span>
                    <select value={targetId} onChange={(event) => selectTarget(event.target.value)}>
                      {context.targets.map((item) => (
                        <option key={item.target.target_id} value={item.target.target_id}>
                          {item.target.display_name}
                          {item.hardware_device_id
                            ? ` · ${item.hardware_device_id}`
                            : item.hardware_device_class
                              ? ` · ${item.hardware_device_class}`
                              : ""}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <div className="best-setup-actions best-setup-actions--forward">
                  <Button
                    variant="primary"
                    onClick={() => setStep(1)}
                    disabled={!useCaseId || !targetId}
                  >
                    Continue
                  </Button>
                </div>
              </>
            ) : null}

            {step === 1 ? (
              <>
                <SectionHeader
                  title="Select models to compare"
                  description="Eligible models on this target are selected by default. Keep the broad comparison or narrow it when you have a specific reason."
                />
                {target?.candidates.length ? (
                  <>
                    <div className="best-setup-selection-summary">
                      <strong>{target.candidates.length} eligible models found</strong>
                      <span>{candidateIds.length} selected for comparison</span>
                    </div>
                    <div className="best-setup-model-list">
                      {target.candidates.map((candidate) => (
                        <label
                          className="best-setup-model-row"
                          data-selected={candidateIds.includes(candidate.candidate_id)}
                          key={candidate.candidate_id}
                        >
                          <input
                            type="checkbox"
                            checked={candidateIds.includes(candidate.candidate_id)}
                            onChange={() => toggleCandidate(candidate.candidate_id)}
                          />
                          <strong>{candidate.model_id}</strong>
                          <span>{candidate.quantization ?? "Quantization unknown"}</span>
                        </label>
                      ))}
                    </div>
                  </>
                ) : (
                  <EmptyState
                    title="No candidate models on this target"
                    description="Use Test a model to connect a runtime that supports model discovery, or configure a model for this target."
                    action={<Button onClick={onManualTest}>Test a model</Button>}
                  />
                )}
                <div className="best-setup-actions">
                  <Button variant="quiet" onClick={() => setStep(0)}>
                    Back
                  </Button>
                  <Button
                    variant="primary"
                    onClick={() => setStep(2)}
                    disabled={candidateIds.length === 0}
                  >
                    Continue
                  </Button>
                </div>
              </>
            ) : null}

            {step === 2 && target ? (
              <>
                <SectionHeader
                  title="How thoroughly should we search?"
                  description="Choose a search depth. Performance Lab only uses parameter ranges explicitly owned by the runtime/backend contract."
                />
                <div className="best-setup-optimization-list">
                  {primaryOptions.map((option) => (
                    <label
                      className="best-setup-optimization"
                      data-selected={option.strategy === strategy}
                      data-disabled={!option.available ? "true" : undefined}
                      key={option.strategy}
                    >
                      <input
                        type="radio"
                        name="search-strategy"
                        value={option.strategy}
                        checked={option.strategy === strategy}
                        disabled={!option.available}
                        onChange={() => selectStrategy(option.strategy)}
                      />
                      <span>
                        <strong>
                          {option.title}
                          {option.strategy === "standard" && option.available ? " · Recommended" : ""}
                        </strong>
                        <small>{option.description}</small>
                        {option.blocked_reason ? <small>{option.blocked_reason}</small> : null}
                      </span>
                    </label>
                  ))}

                  {showFixedFallback && fixedOption ? (
                    <label
                      className="best-setup-optimization"
                      data-selected={strategy === "fixed"}
                    >
                      <input
                        type="radio"
                        name="search-strategy"
                        value="fixed"
                        checked={strategy === "fixed"}
                        onChange={() => selectStrategy("fixed")}
                      />
                      <span>
                        <strong>Single configuration</strong>
                        <small>
                          This target has no evidence-backed sweep ranges, so Performance Lab can run
                          the authored benchmark configuration without inventing parameter domains.
                        </small>
                      </span>
                    </label>
                  ) : null}
                </div>

                <Disclosure summary="Customize parameters (advanced)">
                  <div className="best-setup-advanced-stack">
                    {customOption ? (
                      <label
                        className="best-setup-advanced-option"
                        data-disabled={!customOption.available ? "true" : undefined}
                      >
                        <input
                          type="radio"
                          name="search-strategy"
                          value="custom"
                          checked={strategy === "custom"}
                          disabled={!customOption.available}
                          onChange={() => selectStrategy("custom")}
                        />
                        <span>
                          <strong>{customOption.title}</strong>
                          <small>{customOption.description}</small>
                          {customOption.blocked_reason ? <small>{customOption.blocked_reason}</small> : null}
                        </span>
                      </label>
                    ) : null}
                    {!showFixedFallback && fixedOption ? (
                      <label className="best-setup-advanced-option">
                        <input
                          type="radio"
                          name="search-strategy"
                          value="fixed"
                          checked={strategy === "fixed"}
                          disabled={!fixedOption.available}
                          onChange={() => selectStrategy("fixed")}
                        />
                        <span>
                          <strong>Single configuration</strong>
                          <small>{fixedOption.description}</small>
                        </span>
                      </label>
                    ) : null}
                    <div className="best-setup-parameter-note">
                      <strong>Runtime-reported request controls</strong>
                      <p>
                        {target.supported_generation_parameters.length
                          ? target.supported_generation_parameters.join(", ")
                          : "No request-level parameter capability list was reported for this target."}
                      </p>
                      <p>
                        Bounded search ranges:{" "}
                        {target.bounded_generation_parameter_ranges.length
                          ? target.bounded_generation_parameter_ranges.join(", ")
                          : "None reported"}
                      </p>
                    </div>
                  </div>
                </Disclosure>

                {previewState === "error" && previewError ? (
                  <div className="best-setup-inline-error" role="alert">
                    {previewError}
                  </div>
                ) : null}
                <div className="best-setup-actions">
                  <Button variant="quiet" onClick={() => setStep(1)}>
                    Back
                  </Button>
                  <Button
                    variant="primary"
                    onClick={() => void buildPreview()}
                    disabled={previewState === "loading" || !selectedStrategy?.available}
                  >
                    {previewState === "loading" ? "Preparing review…" : "Continue"}
                  </Button>
                </div>
              </>
            ) : null}

            {step === 3 && preview?.estimate && preview.configuration_search && preview.benchmark_plan ? (
              <>
                <SectionHeader
                  title="Review your evaluation"
                  description="Confirm the decision scope before execution. Benchmark and technical detail stays available without competing with the launch decision."
                />

                <div className="best-setup-review-metrics">
                  <article>
                    <span>Models</span>
                    <strong>{preview.estimate.candidate_count}</strong>
                  </article>
                  <article>
                    <span>Configurations / model</span>
                    <strong>{preview.estimate.configuration_count_per_candidate}</strong>
                  </article>
                  <article>
                    <span>Immutable runs</span>
                    <strong>{preview.estimate.planned_run_count}</strong>
                  </article>
                  <article>
                    <span>Estimated time</span>
                    <strong>
                      {formatDuration(
                        preview.estimate.estimated_duration_seconds,
                        preview.estimate.duration_reason,
                      )}
                    </strong>
                  </article>
                </div>

                <div className="best-setup-measurement-block">
                  <strong>How results will be organized</strong>
                  <div className="best-setup-dimension-grid">
                    <article data-dimension="quality">
                      <span>Quality</span>
                      <small>Benchmark evaluator evidence.</small>
                    </article>
                    <article data-dimension="performance">
                      <span>Performance</span>
                      <small>Runtime performance evidence when available.</small>
                    </article>
                    <article data-dimension="resources">
                      <span>Resources</span>
                      <small>Resource and telemetry evidence when available.</small>
                    </article>
                  </div>
                </div>

                <Disclosure summary="Benchmark & evaluator details">
                  <dl className="best-setup-detail-list">
                    <div>
                      <dt>Benchmark suite</dt>
                      <dd>
                        {preview.benchmark_plan.suite.suite_id} · v
                        {preview.benchmark_plan.suite.suite_version}
                      </dd>
                    </div>
                    <div>
                      <dt>Cases per run</dt>
                      <dd>{preview.benchmark_plan.case_count_per_run}</dd>
                    </div>
                    <div>
                      <dt>Datasets</dt>
                      <dd>
                        {preview.benchmark_plan.datasets.map((item) => item.dataset_id).join(", ") ||
                          "None"}
                      </dd>
                    </div>
                    <div>
                      <dt>Evaluators</dt>
                      <dd>{preview.benchmark_plan.evaluator_ids.join(", ") || "None"}</dd>
                    </div>
                  </dl>
                </Disclosure>

                <Disclosure summary="Technical details (advanced)">
                  <div className="best-setup-technical-details">
                    <dl className="best-setup-detail-list">
                      <div>
                        <dt>Target endpoint</dt>
                        <dd>{preview.target?.endpoint_identity ?? target.target.endpoint_identity}</dd>
                      </div>
                      <div>
                        <dt>Search strategy</dt>
                        <dd>{preview.configuration_search.title}</dd>
                      </div>
                      <div>
                        <dt>Decision policy</dt>
                        <dd>
                          {preview.decision_policy
                            ? `${preview.decision_policy.policy_id}@${preview.decision_policy.policy_version}`
                            : "Unavailable"}
                        </dd>
                      </div>
                      <div>
                        <dt>Plan digest</dt>
                        <dd className="best-setup-digest">{preview.plan_digest}</dd>
                      </div>
                    </dl>
                    {preview.decision_policy ? (
                      <p>
                        {preview.decision_policy.description} No hidden metric weights or universal
                        score.
                      </p>
                    ) : null}
                  </div>
                </Disclosure>

                {launchState === "error" && launchError ? (
                  <div className="best-setup-inline-error" role="alert">
                    {launchError}
                  </div>
                ) : null}
                <div className="best-setup-actions">
                  <Button variant="quiet" onClick={() => setStep(2)}>
                    Back
                  </Button>
                  <Button
                    variant="primary"
                    disabled={!preview.execution_available || launchState === "loading"}
                    onClick={() => void startCampaign()}
                  >
                    {launchState === "loading" ? "Starting evaluation…" : "Start evaluation"}
                  </Button>
                  {preview.execution_blocked_reason ? (
                    <p>{preview.execution_blocked_reason}</p>
                  ) : null}
                </div>
              </>
            ) : null}
          </section>

          <aside className="best-setup-context" aria-label="Your setup">
            <div className="best-setup-context-heading">
              <strong>Your setup</strong>
              <Status tone={setupStatus.tone}>{setupStatus.label}</Status>
            </div>
            <dl className="best-setup-context-list">
              <div>
                <dt>Goal</dt>
                <dd>{useCase?.title ?? "Not selected"}</dd>
                {step > 0 ? (
                  <Button variant="quiet" onClick={() => setStep(0)}>
                    Change
                  </Button>
                ) : null}
              </div>
              <div>
                <dt>Device</dt>
                <dd>{target?.target.display_name ?? "Not selected"}</dd>
                {step > 0 ? (
                  <Button variant="quiet" onClick={() => setStep(0)}>
                    Change
                  </Button>
                ) : null}
              </div>
              <div>
                <dt>Models</dt>
                <dd>{candidateIds.length ? `${candidateIds.length} selected` : "Not selected"}</dd>
                {step > 1 ? (
                  <Button variant="quiet" onClick={() => setStep(1)}>
                    Change
                  </Button>
                ) : null}
              </div>
              <div>
                <dt>Optimization</dt>
                <dd>{selectedStrategy?.title ?? unknown(strategy)}</dd>
                {step > 2 ? (
                  <Button variant="quiet" onClick={() => setStep(2)}>
                    Change
                  </Button>
                ) : null}
              </div>
              <div>
                <dt>Estimated</dt>
                <dd>
                  {preview?.estimate
                    ? `${preview.estimate.planned_run_count} runs · ${formatDuration(
                        preview.estimate.estimated_duration_seconds,
                        preview.estimate.duration_reason,
                      )}`
                    : "Available at review"}
                </dd>
              </div>
            </dl>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; context: CampaignPlanningContextReadModel }
  | { status: "error"; message: string };

export function FindBestSetupPage({ onManualTest, onCampaignStarted }: FindBestSetupPageProps) {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    getCampaignPlanning({ signal: controller.signal })
      .then((context) => setState({ status: "ready", context }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message:
            error instanceof Error ? error.message : "Campaign planning could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt]);

  if (state.status === "loading") {
    return (
      <AppShell activePrimary="Find best setup">
        <LoadingState
          title="Loading campaign planning"
          description="Reading use cases, model candidates and runtime capabilities from Performance Lab."
        />
      </AppShell>
    );
  }

  if (state.status === "error") {
    return (
      <AppShell activePrimary="Find best setup">
        <ErrorState
          title="Could not load campaign planning"
          description={state.message}
          action={<Button onClick={() => setAttempt((value) => value + 1)}>Try again</Button>}
        />
      </AppShell>
    );
  }

  return (
    <FindBestSetupView
      context={state.context}
      onManualTest={onManualTest}
      onCampaignStarted={onCampaignStarted}
    />
  );
}
