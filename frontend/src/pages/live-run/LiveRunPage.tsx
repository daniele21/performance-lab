import { useEffect, useState } from "react";

import { cancelRunJob, getRunJob, subscribeRunJob } from "../../api";
import type { RunJobSnapshot } from "../../api";
import {
  AppShell,
  Button,
  Disclosure,
  ErrorState,
  LoadingState,
  PageHeader,
  RunProgress,
  SectionHeader,
  Status,
} from "../../components";
import "./live-run.css";

interface LiveRunPageProps {
  jobId: string;
  onCompleted?: (runId: string) => void;
  onTestAgain?: () => void;
  onRuns?: () => void;
}

type ConnectionState = "connecting" | "live" | "reconnecting";

function isTerminal(snapshot: RunJobSnapshot) {
  return ["succeeded", "failed", "cancelled", "interrupted"].includes(snapshot.state);
}

function formatLabel(value: string | null) {
  if (!value) return "Preparing";
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function stateTone(state: RunJobSnapshot["state"]): "neutral" | "success" | "warning" | "error" {
  if (state === "succeeded") return "success";
  if (state === "failed") return "error";
  if (state === "cancelled" || state === "interrupted" || state === "cancelling") return "warning";
  return "neutral";
}

export function LiveRunPage({ jobId, onCompleted, onTestAgain, onRuns }: LiveRunPageProps) {
  const [snapshot, setSnapshot] = useState<RunJobSnapshot | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadAttempt, setReloadAttempt] = useState(0);
  const [connection, setConnection] = useState<ConnectionState>("connecting");
  const [cancelLoading, setCancelLoading] = useState(false);
  const [cancelError, setCancelError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    let disposed = false;
    let closeStream: () => void = () => undefined;

    setLoadError(null);
    setSnapshot(null);
    setConnection("connecting");

    const applySnapshot = (next: RunJobSnapshot) => {
      if (disposed) return;
      setSnapshot(next);
      setConnection("live");
      if (next.state === "succeeded" && next.run_id) onCompleted?.(next.run_id);
    };

    getRunJob(jobId, { signal: controller.signal })
      .then((initial) => {
        applySnapshot(initial);
        if (disposed || isTerminal(initial)) return;
        closeStream = subscribeRunJob(jobId, {
          afterRevision: initial.revision,
          onSnapshot: applySnapshot,
          onDisconnect: () => {
            if (!disposed) setConnection("reconnecting");
          },
          onMalformedEvent: () => {
            if (!disposed) setConnection("reconnecting");
          },
        });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted || disposed) return;
        setLoadError(error instanceof Error ? error.message : "Run state could not be loaded.");
      });

    return () => {
      disposed = true;
      controller.abort();
      closeStream();
    };
  }, [jobId, onCompleted, reloadAttempt]);

  const cancel = () => {
    if (!snapshot || isTerminal(snapshot)) return;
    setCancelLoading(true);
    setCancelError(null);
    cancelRunJob(jobId)
      .then(setSnapshot)
      .catch((error: unknown) =>
        setCancelError(error instanceof Error ? error.message : "The run could not be cancelled."),
      )
      .finally(() => setCancelLoading(false));
  };

  if (loadError) {
    return (
      <AppShell activePrimary="Runs">
        <ErrorState
          title="Could not reconnect to this run"
          description={`${loadError} The server-owned job may still be running. Reconnect to read its latest state before starting another evaluation.`}
          action={
            <div className="live-run-recovery-actions">
              <Button variant="primary" onClick={() => setReloadAttempt((value) => value + 1)}>
                Reconnect to run
              </Button>
              <Button variant="quiet" onClick={onRuns}>
                Back to Runs
              </Button>
            </div>
          }
        />
      </AppShell>
    );
  }

  if (!snapshot) {
    return (
      <AppShell activePrimary="Runs">
        <LoadingState
          title="Connecting to run"
          description="Reading the latest server-owned job state."
        />
      </AppShell>
    );
  }

  if (snapshot.state === "failed") {
    return (
      <AppShell activePrimary="Runs">
        <ErrorState
          title="The evaluation failed"
          description={
            snapshot.error_message ?? "The run stopped before completed evidence was published."
          }
          action={<Button onClick={onTestAgain}>Test a model</Button>}
        />
      </AppShell>
    );
  }

  if (snapshot.state === "cancelled" || snapshot.state === "interrupted") {
    const interrupted = snapshot.state === "interrupted";
    return (
      <AppShell activePrimary="Runs">
        <div className="live-run-page">
          <PageHeader
            eyebrow="Evaluation stopped"
            title={interrupted ? "Run interrupted" : "Run cancelled"}
            description={
              interrupted
                ? "The local process restarted or could not finish shutdown. Retained working state is not presented as completed evidence."
                : "Cancellation completed. Partial working state is not presented as an immutable completed run."
            }
          />
          <Status tone="warning">{interrupted ? "Interrupted" : "Cancelled"}</Status>
          <div className="live-run-actions">
            <Button variant="primary" onClick={onTestAgain}>
              Test again
            </Button>
            <Button variant="quiet" onClick={onRuns}>
              View Runs
            </Button>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell activePrimary="Runs">
      <div className="live-run-page">
        <PageHeader
          eyebrow="Live evaluation"
          title={snapshot.model_id ?? "Running evaluation"}
          description="This job is owned by the local Performance Lab process. Leaving or refreshing this page does not cancel it."
        />

        <div className="live-run-status-row">
          <Status tone={stateTone(snapshot.state)}>{formatLabel(snapshot.state)}</Status>
          {connection === "reconnecting" ? (
            <Status tone="warning">Reconnecting to progress</Status>
          ) : (
            <Status tone="neutral">Live progress connected</Status>
          )}
        </div>

        <dl className="live-run-identity">
          <div>
            <dt>Model</dt>
            <dd>{snapshot.model_id ?? "Resolving"}</dd>
          </div>
          <div>
            <dt>Target</dt>
            <dd>{snapshot.target_id ?? "Resolving"}</dd>
          </div>
          <div>
            <dt>Scenario</dt>
            <dd>{formatLabel(snapshot.scenario)}</dd>
          </div>
          <div>
            <dt>Job</dt>
            <dd>
              <code>{snapshot.job_id}</code>
            </dd>
          </div>
        </dl>

        <section className="live-run-progress-section">
          <SectionHeader
            title="Progress"
            description="Sample progress is emitted by the canonical evaluation orchestrator."
          />
          <RunProgress
            phase={formatLabel(snapshot.phase)}
            completed={snapshot.completed_samples}
            total={snapshot.total_samples || null}
          />
        </section>

        <div className="live-run-actions">
          <Button
            variant="quiet"
            disabled={cancelLoading || snapshot.state === "cancelling"}
            onClick={cancel}
          >
            {snapshot.state === "cancelling" || cancelLoading ? "Cancelling…" : "Cancel run"}
          </Button>
          <span>Closing this page does not cancel the server-owned job.</span>
        </div>
        {cancelError ? (
          <p className="live-run-error" role="alert">
            {cancelError}
          </p>
        ) : null}

        <Disclosure summary="Activity and lifecycle details">
          <dl className="live-run-diagnostics">
            <div>
              <dt>Revision</dt>
              <dd>{snapshot.revision}</dd>
            </div>
            <div>
              <dt>Phase</dt>
              <dd>{snapshot.phase ?? "not started"}</dd>
            </div>
            <div>
              <dt>Run ID</dt>
              <dd>{snapshot.run_id ?? "assigned at execution"}</dd>
            </div>
            <div>
              <dt>Frozen config</dt>
              <dd>
                <code>{snapshot.config_digest ?? "unavailable"}</code>
              </dd>
            </div>
          </dl>
        </Disclosure>
      </div>
    </AppShell>
  );
}
