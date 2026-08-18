export interface IdentityDifference {
  path: string;
  baseline: unknown;
  candidate: unknown;
}

interface IdentityDiffProps {
  differences: readonly IdentityDifference[];
}

function readable(value: unknown) {
  if (value === null || value === undefined) return "Unknown";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

export function IdentityDiff({ differences }: IdentityDiffProps) {
  if (!differences.length) {
    return <p className="identity-diff__empty">No identity differences.</p>;
  }
  return (
    <div className="identity-diff">
      {differences.map((difference) => (
        <div className="identity-diff__row" key={difference.path}>
          <code>{difference.path}</code>
          <span>{readable(difference.baseline)}</span>
          <span>{readable(difference.candidate)}</span>
        </div>
      ))}
    </div>
  );
}
