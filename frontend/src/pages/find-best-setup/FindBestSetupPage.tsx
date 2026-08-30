import { useEffect, useMemo, useState } from "react";

import { getCampaignPlanning, previewCampaignPlan } from "../../api";
import type {
  CampaignPlanPreviewReadModel,
  CampaignPlanningContextReadModel,
  CampaignSearchStrategy,
} from "../../api";
import {
  AppShell,
  Button,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  SectionHeader,
  Status,
} from "../../components";
import "./find-best-setup.css";

const CAMPAIGN_STEPS = [
  "Use case",
  "Candidate models",
  "Configuration search",
  "Benchmark plan",
  "Campaign review / estimate",
  "Campaign",
  "Results",
] as const;

interface FindBestSetupPageProps {
  onManualTest?: () => void;
}

interface FindBestSetupViewProps extends FindBestSetupPageProps {
  context: CampaignPlanningContextReadModel;
}

function unknown(value: string | null) {
  return value ?? "Unknown";
}

export function FindBestSetupView({ context, onManualTest }: FindBestSetupViewProps) {
  const firstTarget =
    context.targets.find((item) => item.candidates.length > 0) ?? context.targets[0];
  const [step, setStep] = useState(0);
  const [useCaseId, setUseCaseId] = useState(context.use_cases[0]?.use_case_id ?? "");
  const [targetId, setTargetId] = useState(firstTarget?.target.target_id ?? "");
  const [candidateIds, setCandidateIds] = useState<string[]>(
    firstTarget?.candidates.map((candidate) => candidate.candidate_id) ?? [],
  );
  const [strategy, setStrategy] = useState<CampaignSearchStrategy>("fixed");
  const [preview, setPreview] = useState<CampaignPlanPreviewReadModel | null>(null);
  const [previewState, setPreviewState] = useState<"idle" | "loading" | "error">("idle");
  const [previewError, setPreviewError] = useState<string | null>(null);

  const target = useMemo(
    () => context.targets.find((item) => item.target.target_id === targetId) ?? null,
    [context.targets, targetId],
  );
  const useCase = useMemo(
    () => context.use_cases.find((item) => item.use_case_id === useCaseId) ?? null,
    [context.use_cases, useCaseId],
  );

  const invalidatePreview = () => {
    setPreview(null);
    setPreviewState("idle");
    setPreviewError(null);
  };

  const selectTarget = (nextTargetId: string) => {
    const nextTarget = context.targets.find((item) => item.target.target_id === nextTargetId);
    setTargetId(nextTargetId);
    setCandidateIds(nextTarget?.candidates.map((candidate) => candidate.candidate_id) ?? []);
    setStrategy("fixed");
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

  const buildPreview = async () => {
    if (!useCase || !target || candidateIds.length === 0) return;
    setPreviewState("loading");
    setPreviewError(null);
    try {
      const result = await previewCampaignPlan({
        use_case_id: useCase.use_case_id,
        target_id: target.target.target_id,
        candidate_ids: candidateIds,
        configuration_strategy: strategy,
      });
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
      setPreviewError(error instanceof Error ? error.message : "Campaign plan could not be built.");
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

  return (
    <AppShell activePrimary="Find best setup">
      <div className="best-setup-page">
        <PageHeader
          eyebrow="Use-case optimization"
          title="Find best setup"
          description="Choose the workload first, select model candidates on one target, then review the exact benchmark plan Performance Lab would execute."
          actions={
            <Button variant="quiet" onClick={onManualTest}>
              Manual test
            </Button>
          }
        />

        <ol className="best-setup-steps" aria-label="Automatic evaluation campaign flow">
          {CAMPAIGN_STEPS.map((label, index) => (
            <li
              data-active={index === step ? "true" : undefined}
              data-complete={index < step ? "true" : undefined}
              key={label}
            >
              <span>{index + 1}</span>
              <strong>{label}</strong>
            </li>
          ))}
        </ol>

        <section className="best-setup-panel" aria-live="polite">
          {step === 0 ? (
            <>
              <SectionHeader
                title="Choose the use case"
                description="The selected use case determines the versioned benchmark suite, datasets and evaluators."
              />
              <div className="best-setup-choice-grid">
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
                      <small>
                        {item.source === "workload_pack"
                          ? "Versioned workload pack"
                          : "Starter diagnostic"}{" "}
                        · {item.suite_id}
                      </small>
                    </span>
                  </label>
                ))}
              </div>
              <div className="best-setup-actions">
                <Button variant="primary" onClick={() => setStep(1)} disabled={!useCaseId}>
                  Continue
                </Button>
              </div>
            </>
          ) : null}

          {step === 1 ? (
            <>
              <SectionHeader
                title="Choose candidate models"
                description="Candidates are scoped to one endpoint/device target. Different quantizations remain distinct only when the runtime reports them as distinct identity."
              />
              <label className="best-setup-field">
                <span>Target / device</span>
                <select value={targetId} onChange={(event) => selectTarget(event.target.value)}>
                  {context.targets.map((item) => (
                    <option key={item.target.target_id} value={item.target.target_id}>
                      {item.target.display_name} · {item.target.endpoint_identity}
                    </option>
                  ))}
                </select>
              </label>
              {target ? (
                <div className="best-setup-target-context">
                  <span>
                    Device: {target.hardware_device_id ?? target.hardware_device_class ?? "Unknown"}
                  </span>
                  <span>Endpoint: {target.target.endpoint_identity}</span>
                </div>
              ) : null}
              {target?.candidates.length ? (
                <div className="best-setup-choice-grid">
                  {target.candidates.map((candidate) => (
                    <label
                      className="best-setup-choice"
                      data-selected={candidateIds.includes(candidate.candidate_id)}
                      key={candidate.candidate_id}
                    >
                      <input
                        type="checkbox"
                        checked={candidateIds.includes(candidate.candidate_id)}
                        onChange={() => toggleCandidate(candidate.candidate_id)}
                      />
                      <span>
                        <strong>{candidate.model_id}</strong>
                        <small>Quantization: {unknown(candidate.quantization)}</small>
                        <small>
                          Revision: {unknown(candidate.revision)} · Runtime:{" "}
                          {unknown(candidate.runtime_name)}
                        </small>
                      </span>
                    </label>
                  ))}
                </div>
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
                title="Choose configuration search"
                description="Performance Lab only searches parameter domains owned by the backend/runtime contract. Support alone is not treated as a range."
              />
              <div className="best-setup-choice-grid">
                {target.configuration_search_options.map((option) => (
                  <label
                    className="best-setup-choice"
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
                      onChange={() => {
                        setStrategy(option.strategy);
                        invalidatePreview();
                      }}
                    />
                    <span>
                      <strong>{option.title}</strong>
                      <small>{option.description}</small>
                      {option.blocked_reason ? <small>{option.blocked_reason}</small> : null}
                    </span>
                  </label>
                ))}
              </div>
              <div className="best-setup-parameter-note">
                <strong>Reported request parameters</strong>
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
                  disabled={previewState === "loading"}
                >
                  {previewState === "loading" ? "Building plan…" : "Build benchmark plan"}
                </Button>
              </div>
            </>
          ) : null}

          {step === 3 && preview?.benchmark_plan ? (
            <>
              <SectionHeader
                title="Benchmark plan"
                description="This plan comes from the selected versioned use case. Dataset and evaluator relevance is backend-owned."
              />
              <div className="best-setup-summary-grid">
                <article>
                  <span>Suite</span>
                  <strong>{preview.benchmark_plan.suite.suite_id}</strong>
                  <small>v{preview.benchmark_plan.suite.suite_version}</small>
                </article>
                <article>
                  <span>Cases per run</span>
                  <strong>{preview.benchmark_plan.case_count_per_run}</strong>
                  <small>{preview.benchmark_plan.suite.task_count} benchmark tasks</small>
                </article>
                <article>
                  <span>Datasets</span>
                  <strong>{preview.benchmark_plan.datasets.length}</strong>
                  <small>
                    {preview.benchmark_plan.datasets.map((item) => item.dataset_id).join(", ")}
                  </small>
                </article>
                <article>
                  <span>Evaluators</span>
                  <strong>{preview.benchmark_plan.evaluator_ids.length}</strong>
                  <small>{preview.benchmark_plan.evaluator_ids.join(", ")}</small>
                </article>
              </div>
              <div className="best-setup-actions">
                <Button variant="quiet" onClick={() => setStep(2)}>
                  Back
                </Button>
                <Button variant="primary" onClick={() => setStep(4)}>
                  Review campaign
                </Button>
              </div>
            </>
          ) : null}

          {step === 4 && preview?.estimate && preview.configuration_search ? (
            <>
              <SectionHeader
                title="Campaign review / estimate"
                description="Review the frozen planning identity before execution. Duration stays unavailable until Performance Lab has an evidence-backed timing model for this target."
              />
              <div className="best-setup-status">
                <div>
                  <strong>Plan frozen</strong>
                  <p className="best-setup-digest">{preview.plan_digest}</p>
                </div>
                <Status tone="warning">Engine pending</Status>
              </div>
              <div className="best-setup-summary-grid">
                <article>
                  <span>Candidates</span>
                  <strong>{preview.estimate.candidate_count}</strong>
                  <small>
                    {preview.candidates.map((candidate) => candidate.model_id).join(", ")}
                  </small>
                </article>
                <article>
                  <span>Configurations / candidate</span>
                  <strong>{preview.estimate.configuration_count_per_candidate}</strong>
                  <small>{preview.configuration_search.title}</small>
                </article>
                <article>
                  <span>Planned immutable runs</span>
                  <strong>{preview.estimate.planned_run_count}</strong>
                  <small>One run per model + frozen configuration</small>
                </article>
                <article>
                  <span>Estimated requests</span>
                  <strong>{preview.estimate.estimated_request_count}</strong>
                  <small>{preview.estimate.duration_reason}</small>
                </article>
              </div>
              <div className="best-setup-actions">
                <Button variant="quiet" onClick={() => setStep(3)}>
                  Back
                </Button>
                <Button variant="primary" disabled>
                  Start evaluation campaign
                </Button>
                <p>{preview.execution_blocked_reason}</p>
              </div>
            </>
          ) : null}
        </section>
      </div>
    </AppShell>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; context: CampaignPlanningContextReadModel }
  | { status: "error"; message: string };

export function FindBestSetupPage({ onManualTest }: FindBestSetupPageProps) {
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

  return <FindBestSetupView context={state.context} onManualTest={onManualTest} />;
}
