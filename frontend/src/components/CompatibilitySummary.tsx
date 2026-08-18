import { Status } from "./Status";

export interface CompatibilityReason {
  code: string;
  message: string;
}

interface CompatibilitySummaryProps {
  comparable: boolean;
  reasons?: readonly CompatibilityReason[];
}

export function CompatibilitySummary({ comparable, reasons = [] }: CompatibilitySummaryProps) {
  return (
    <section className="compatibility-summary" data-comparable={comparable ? "true" : "false"}>
      <Status tone={comparable ? "success" : "warning"}>
        {comparable ? "Comparable evidence" : "Not comparable"}
      </Status>
      {!comparable ? (
        <div>
          <h3>Metric deltas are hidden for this comparison.</h3>
          {reasons.length ? (
            <ul>
              {reasons.map((reason) => (
                <li key={`${reason.code}:${reason.message}`}>{reason.message}</li>
              ))}
            </ul>
          ) : (
            <p>No compatibility reason was provided.</p>
          )}
        </div>
      ) : null}
    </section>
  );
}
