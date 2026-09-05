import { useEffect, useState } from "react";

import { getRunRepeatability } from "../../api";
import type {
  RepeatabilityMetricReadModel,
  RepeatabilityReadModel,
  RepeatabilityState,
} from "../../api";
import { Button, Disclosure, SectionHeader, Status } from "../../components";

function stateTone(state: RepeatabilityState) {
  if (state === "available") return "success" as const;
  if (state === "insufficient_repeats") return "warning" as const;
  return "neutral" as const;
}

function stateLabel(state: RepeatabilityState) {
  if (state === "available") return "Evidence available";
  if (state === "insufficient_repeats") return "Insufficient repeats";
  return "Evidence unavailable";
}

function formatValue(value: number, unit: string | null) {
  const formatted = Number.isInteger(value) ? String(value) : value.toFixed(2);
  return unit ? `${formatted} ${unit}` : formatted;
}

function formatCv(value: number | null) {
  if (value === null) return "Not available";
  return `${(value * 100).toFixed(1)}%`;
}

function percentileLabel(metric: RepeatabilityMetricReadModel, percentile: "p90" | "p95") {
  const estimate = metric.distribution[percentile];
  if (!estimate.qualified || estimate.value === null) {
    return estimate.qualification ?? "Not qualified";
  }
  return formatValue(estimate.value, metric.unit);
}

export function RepeatabilityEvidenceView({ evidence }: { evidence: RepeatabilityReadModel }) {
  return (
    <section className="run-detail__repeatability" aria-label="Repeatability evidence">
      <SectionHeader
        title="Repeatability"
        description="Run-to-run variability across retained executions with this exact fingerprint."
      />

      <div className="run-detail__repeatability-header">
        <Status tone={stateTone(evidence.state)}>{stateLabel(evidence.state)}</Status>
        <span>{evidence.run_count} exact-fingerprint runs</span>
      </div>

      <div className="run-detail__repeatability-counts" aria-label="Repeatability denominators">
        <div>
          <span>Runs</span>
          <strong>{evidence.run_count}</strong>
          <small>
            {evidence.succeeded_run_count} succeeded · {evidence.failed_run_count} failed ·{" "}
            {evidence.cancelled_run_count} cancelled
          </small>
        </div>
        <div>
          <span>Sample attempts</span>
          <strong>{evidence.sample_attempt_count}</strong>
          <small>
            {evidence.succeeded_sample_count} succeeded · {evidence.failed_sample_count} failed ·{" "}
            {evidence.cancelled_sample_count} cancelled
          </small>
        </div>
      </div>

      <p className="run-detail__repeatability-note">{evidence.note}</p>

      {evidence.metrics.length ? (
        <Disclosure summary="Show run-to-run variability">
          <div className="run-detail__repeatability-metrics">
            {evidence.metrics.map((metric) => (
              <article key={metric.metric_id} className="run-detail__repeatability-metric">
                <header>
                  <div>
                    <h3>{metric.label}</h3>
                    <span>{metric.dimension}</span>
                  </div>
                  <strong>{metric.distribution.sample_count} run values</strong>
                </header>
                <dl>
                  <div>
                    <dt>Median</dt>
                    <dd>{formatValue(metric.distribution.median, metric.unit)}</dd>
                  </div>
                  <div>
                    <dt>Range</dt>
                    <dd>
                      {formatValue(metric.distribution.minimum, metric.unit)} –{" "}
                      {formatValue(metric.distribution.maximum, metric.unit)}
                    </dd>
                  </div>
                  <div>
                    <dt>Std. deviation</dt>
                    <dd>{formatValue(metric.distribution.stddev, metric.unit)}</dd>
                  </div>
                  <div>
                    <dt>Coefficient of variation</dt>
                    <dd>{formatCv(metric.distribution.coefficient_of_variation)}</dd>
                  </div>
                  <div>
                    <dt>P90</dt>
                    <dd>{percentileLabel(metric, "p90")}</dd>
                  </div>
                  <div>
                    <dt>P95</dt>
                    <dd>{percentileLabel(metric, "p95")}</dd>
                  </div>
                </dl>
              </article>
            ))}
          </div>
        </Disclosure>
      ) : null}
    </section>
  );
}

type RepeatabilityLoadState =
  | { status: "loading" }
  | { status: "ready"; evidence: RepeatabilityReadModel }
  | { status: "error"; message: string };

export function RunRepeatabilitySection({ runId }: { runId: string }) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<RepeatabilityLoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    getRunRepeatability(runId, { signal: controller.signal })
      .then((evidence) => setState({ status: "ready", evidence }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message:
            error instanceof Error ? error.message : "Repeatability evidence could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt, runId]);

  if (state.status === "loading") {
    return (
      <section className="run-detail__repeatability" aria-label="Repeatability evidence">
        <SectionHeader
          title="Repeatability"
          description="Run-to-run variability across retained executions with this exact fingerprint."
        />
        <p className="run-detail__repeatability-note" role="status">
          Loading repeatability evidence…
        </p>
      </section>
    );
  }

  if (state.status === "error") {
    return (
      <section className="run-detail__repeatability" aria-label="Repeatability evidence">
        <SectionHeader
          title="Repeatability"
          description="Run-to-run variability across retained executions with this exact fingerprint."
        />
        <div className="run-detail__repeatability-error" role="alert">
          <p>{state.message}</p>
          <Button variant="secondary" onClick={() => setAttempt((value) => value + 1)}>
            Try again
          </Button>
        </div>
      </section>
    );
  }

  return <RepeatabilityEvidenceView evidence={state.evidence} />;
}
