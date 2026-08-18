import type { InputHTMLAttributes } from "react";

interface ToggleProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label: string;
  description?: string;
}

export function Toggle({ label, description, id, ...props }: ToggleProps) {
  const inputId = id ?? `toggle-${label.toLowerCase().replaceAll(" ", "-")}`;
  return (
    <label className="toggle" htmlFor={inputId}>
      <span className="toggle__copy">
        <span className="toggle__label">{label}</span>
        {description ? <span className="toggle__description">{description}</span> : null}
      </span>
      <input className="toggle__input" id={inputId} type="checkbox" role="switch" {...props} />
      <span className="toggle__track" aria-hidden="true">
        <span className="toggle__thumb" />
      </span>
    </label>
  );
}
