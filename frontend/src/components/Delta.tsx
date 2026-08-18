interface DeltaProps {
  value: number | null;
  unit?: string;
  higherIsBetter?: boolean | null;
  label?: string;
}

export function Delta({ value, unit, higherIsBetter, label = "Change" }: DeltaProps) {
  if (value === null) {
    return <span className="delta delta--unavailable">{label}: unavailable</span>;
  }

  const direction = value === 0 ? "neutral" : value > 0 ? "increase" : "decrease";
  const favorable =
    value === 0 || higherIsBetter === null || higherIsBetter === undefined
      ? undefined
      : value > 0 === higherIsBetter;
  const sign = value > 0 ? "+" : "";

  return (
    <span className="delta" data-direction={direction} data-favorable={favorable?.toString()}>
      {label}: {sign}
      {value}
      {unit ? ` ${unit}` : ""}
    </span>
  );
}
