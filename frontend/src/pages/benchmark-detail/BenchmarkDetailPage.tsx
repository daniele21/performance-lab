import { useEffect, useState } from "react";

import { getBenchmark } from "../../api";
import type { BenchmarkCaseReadModel, BenchmarkDetailReadModel } from "../../api";
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
import "../evidence-drilldown.css";

function renderValue(value: unknown) {
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

function CaseCard({
  benchmark,
  item,
}: {
  benchmark: BenchmarkDetailReadModel;
  item: BenchmarkCaseReadModel;
}) {
  const task = benchmark.tasks.find((candidate) => candidate.task_id === item.task_id);
  const evaluator = task?.evaluator;

  return (
    <Disclosure summary={`${item.case_id} · ${item.task_id}`}>
      <div className="evidence-drilldown__metadata-grid">
        <div>
          <dl>
            <dt>Sample</dt>
            <dd>{item.sample_id}</dd>
          </dl>
        </div>
        <div>
          <dl>
            <dt>Dataset snapshot</dt>
            <dd>
              {item.dataset_id} · {item.dataset_version}
            </dd>
          </dl>
        </div>
        <div>
          <dl>
            <dt>Evaluator</dt>
            <dd>
              {item.evaluator_id} · {item.evaluator_version}
            </dd>
          </dl>
        </div>
      </div>
      <div className="evidence-drilldown__content-grid">
        <div className="evidence-drilldown__panel">
          <span className="evidence-drilldown__panel-label">Prompt / input</span>
          <pre className="evidence-drilldown__pre">{renderValue(item.input)}</pre>
        </div>
        <div className="evidence-drilldown__panel">
          <span className="evidence-drilldown__panel-label">Expected output</span>
          <pre className="evidence-drilldown__pre">{renderValue(item.expected)}</pre>
        </div>
      </div>
      <div className="evidence-drilldown__notice">
        <strong>Evaluator rules</strong>
        <p>{evaluator?.rule_summary ?? "Evaluator rule summary unavailable."}</p>
        <p>Metrics: {item.metric_names.join(", ")}</p>
      </div>
    </Disclosure>
  );
}

export function BenchmarkDetailView({ benchmark }: { benchmark: BenchmarkDetailReadModel }) {
  const { summary } = benchmark;

  return (
    <AppShell activeSecondary="Benchmarks">
      <div className="evidence-drilldown">
        <a className="evidence-drilldown__back" href="#benchmarks">
          ← Back to benchmarks
        </a>
        <PageHeader
          eyebrow="Benchmark definition"
          title={summary.suite_id}
          description={`Version ${summary.suite_version} · ${summary.task_count} tasks. This surface describes the benchmark definition, not a model result.`}
        />

        <div className="evidence-drilldown__summary-grid" aria-label="Benchmark definition summary">
          <div>
            <span>Version</span>
            <strong>{summary.suite_version}</strong>
          </div>
          <div>
            <span>Tasks</span>
            <strong>{summary.task_count}</strong>
          </div>
          <div>
            <span>Inspectable cases</span>
            <strong>{benchmark.cases.length}</strong>
          </div>
        </div>

        {benchmark.definition_issues.length ? (
          <div className="evidence-drilldown__notice" role="status">
            <Status tone="warning">Definition partially inspectable</Status>
            <ul>
              {benchmark.definition_issues.map((issue) => (
                <li key={issue}>{issue}</li>
              ))}
            </ul>
          </div>
        ) : null}

        <section className="evidence-drilldown__section">
          <SectionHeader
            title="Tasks, datasets & evaluators"
            description="Dataset snapshot and evaluator identity come from the backend-owned benchmark definition."
          />
          <div className="evidence-drilldown__stack">
            {benchmark.tasks.map((task) => (
              <article className="evidence-drilldown__card" key={task.task_id}>
                <div className="evidence-drilldown__card-header">
                  <div>
                    <h3>{task.task_id}</h3>
                    <p>{task.metric_names.join(", ")}</p>
                  </div>
                  <Status tone={task.case_content_available ? "success" : "unknown"}>
                    {task.case_content_available ? "Cases inspectable" : "Case content unavailable"}
                  </Status>
                </div>
                <div className="evidence-drilldown__metadata-grid">
                  <div>
                    <dl>
                      <dt>Dataset</dt>
                      <dd>{task.dataset?.dataset_id ?? task.dataset_snapshot_id}</dd>
                    </dl>
                  </div>
                  <div>
                    <dl>
                      <dt>Snapshot / split</dt>
                      <dd>
                        {task.dataset
                          ? `${task.dataset.dataset_version} · ${task.dataset.split}`
                          : "Snapshot metadata unavailable"}
                      </dd>
                    </dl>
                  </div>
                  <div>
                    <dl>
                      <dt>Evaluator</dt>
                      <dd>
                        {task.evaluator.evaluator_id} · {task.evaluator.version}
                      </dd>
                    </dl>
                  </div>
                </div>
                <p className="evidence-drilldown__muted">
                  {task.evaluator.rule_summary ?? "Evaluator rule summary unavailable."}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="evidence-drilldown__section">
          <SectionHeader
            title="Test cases"
            description="Inspect authored input, expected output and evaluator rules before trusting aggregate execution evidence."
          />
          {benchmark.cases.length ? (
            <div className="evidence-drilldown__stack">
              {benchmark.cases.map((item) => (
                <CaseCard benchmark={benchmark} item={item} key={item.case_id} />
              ))}
            </div>
          ) : (
            <EmptyState
              title="Test case content unavailable"
              description="The benchmark definition is known, but case content is not exposed under the current dataset inspection policy."
            />
          )}
        </section>

        <Disclosure summary="Show generation configuration">
          <pre className="evidence-drilldown__pre">
            {JSON.stringify(benchmark.generation, null, 2)}
          </pre>
        </Disclosure>
      </div>
    </AppShell>
  );
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; benchmark: BenchmarkDetailReadModel }
  | { status: "error"; message: string };

export function BenchmarkDetailPage({
  suiteId,
  suiteVersion,
}: {
  suiteId: string;
  suiteVersion: string;
}) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    getBenchmark(suiteId, suiteVersion, { signal: controller.signal })
      .then((benchmark) => setState({ status: "ready", benchmark }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: "error",
          message:
            error instanceof Error ? error.message : "Benchmark definition could not be loaded.",
        });
      });
    return () => controller.abort();
  }, [attempt, suiteId, suiteVersion]);

  if (state.status === "loading") {
    return (
      <AppShell activeSecondary="Benchmarks">
        <LoadingState
          title="Loading benchmark definition"
          description="Reading tasks, dataset snapshots, evaluator rules and inspectable cases."
        />
      </AppShell>
    );
  }

  if (state.status === "error") {
    return (
      <AppShell activeSecondary="Benchmarks">
        <ErrorState
          title="Could not load this benchmark"
          description={state.message}
          action={<Button onClick={() => setAttempt((value) => value + 1)}>Try again</Button>}
        />
      </AppShell>
    );
  }

  return <BenchmarkDetailView benchmark={state.benchmark} />;
}
