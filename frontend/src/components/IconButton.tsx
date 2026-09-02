import type { ButtonHTMLAttributes, ReactNode } from "react";

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  children: ReactNode;
}

export function IconButton({ label, children, className = "", ...props }: IconButtonProps) {
  const classes = ["icon-button", className].filter(Boolean).join(" ");
  return (
    <button className={classes} aria-label={label} title={label} {...props}>
      {children}
    </button>
  );
}
