import type { ReactNode } from "react";

import { StateSurface } from "./StateSurface";

interface FeedbackProps {
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState(props: FeedbackProps) {
  return <StateSurface kind="empty" {...props} />;
}

export function ErrorState(props: FeedbackProps) {
  return <StateSurface kind="error" {...props} />;
}

export function LoadingState({
  title = "Loading evidence",
  description = "Performance Lab is reading local evidence.",
}: Partial<FeedbackProps>) {
  return <StateSurface kind="loading" title={title} description={description} />;
}
