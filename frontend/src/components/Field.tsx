import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  description?: string;
  error?: string;
}

export function Field({ label, description, error, id, ...props }: FieldProps) {
  const inputId = id ?? `field-${label.toLowerCase().replaceAll(" ", "-")}`;
  const descriptionId = description ? `${inputId}-description` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;
  const describedBy = [descriptionId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <label className="field" htmlFor={inputId}>
      <span className="field__label">{label}</span>
      {description ? (
        <span className="field__description" id={descriptionId}>
          {description}
        </span>
      ) : null}
      <input
        className="field__control"
        id={inputId}
        aria-invalid={Boolean(error) || undefined}
        aria-describedby={describedBy}
        {...props}
      />
      {error ? (
        <span className="field__error" id={errorId}>
          {error}
        </span>
      ) : null}
    </label>
  );
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  description?: string;
  children: ReactNode;
}

export function Select({ label, description, children, id, ...props }: SelectProps) {
  const selectId = id ?? `select-${label.toLowerCase().replaceAll(" ", "-")}`;
  const descriptionId = description ? `${selectId}-description` : undefined;
  return (
    <label className="field" htmlFor={selectId}>
      <span className="field__label">{label}</span>
      {description ? (
        <span className="field__description" id={descriptionId}>
          {description}
        </span>
      ) : null}
      <select className="field__control" id={selectId} aria-describedby={descriptionId} {...props}>
        {children}
      </select>
    </label>
  );
}
