import type { ReactNode } from "react";

interface DialogProps {
  open: boolean;
  title: string;
  children: ReactNode;
  actions?: ReactNode;
  onClose: () => void;
}

export function Dialog({ open, title, children, actions, onClose }: DialogProps) {
  return (
    <dialog className="dialog" open={open} onClose={onClose}>
      <div className="dialog__header">
        <h2>{title}</h2>
        <button className="icon-button" type="button" aria-label="Close dialog" onClick={onClose}>
          ×
        </button>
      </div>
      <div className="dialog__content">{children}</div>
      {actions ? <div className="dialog__actions">{actions}</div> : null}
    </dialog>
  );
}
