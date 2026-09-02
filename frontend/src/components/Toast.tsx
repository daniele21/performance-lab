import type { ReactNode } from "react";

interface ToastProps {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "error";
}

export function Toast({ children, tone = "neutral" }: ToastProps) {
  return (
    <div className="toast" data-tone={tone} role={tone === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}
