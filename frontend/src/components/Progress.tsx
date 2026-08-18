interface ProgressProps {
  value?: number | null;
  label: string;
}

export function Progress({ value, label }: ProgressProps) {
  const determinate = value !== null && value !== undefined;
  const normalized = determinate ? Math.min(100, Math.max(0, value)) : undefined;
  return (
    <div className="progress">
      <div className="progress__copy">
        <span>{label}</span>
        <span>{determinate ? `${normalized}%` : "In progress"}</span>
      </div>
      <progress aria-label={label} max={100} value={normalized} />
    </div>
  );
}

interface RunProgressProps {
  phase: string;
  completed: number;
  total: number | null;
}

export function RunProgress({ phase, completed, total }: RunProgressProps) {
  const value = total && total > 0 ? (completed / total) * 100 : null;
  const detail = total ? `${completed} of ${total}` : `${completed} completed`;
  return (
    <section className="run-progress" aria-label="Run progress">
      <div className="run-progress__identity">
        <strong>{phase}</strong>
        <span>{detail}</span>
      </div>
      <Progress label={phase} value={value} />
    </section>
  );
}
