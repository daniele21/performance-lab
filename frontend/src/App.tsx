import { useEffect, useState } from "react";

import { AppShell, Button, StateSurface } from "./components";
import "./foundation.css";
import { OverviewPage } from "./pages/overview";
import { RunDetailPage } from "./pages/run-detail";
import { RunsPage } from "./pages/runs";
import { navigate, parseHash, type AppRoute } from "./routing";

function currentRoute(): AppRoute {
  return parseHash(window.location.hash);
}

function Placeholder({
  activePrimary,
  title,
  description,
}: {
  activePrimary: "Test a model" | "Compare";
  title: string;
  description: string;
}) {
  return (
    <AppShell activePrimary={activePrimary}>
      <StateSurface
        kind="empty"
        title={title}
        description={description}
        action={<Button onClick={() => navigate("overview")}>Back to Overview</Button>}
      />
    </AppShell>
  );
}

export function App() {
  const [route, setRoute] = useState<AppRoute>(currentRoute);

  useEffect(() => {
    const handleHashChange = () => setRoute(currentRoute());
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  if (route.kind === "overview") {
    return <OverviewPage onTestModel={() => navigate("test-a-model")} />;
  }

  if (route.kind === "runs") return <RunsPage />;

  if (route.kind === "run-detail") {
    return (
      <RunDetailPage
        runId={route.runId}
        onCompare={(runId) => navigate(`compare?run=${encodeURIComponent(runId)}`)}
      />
    );
  }

  if (route.kind === "test-model") {
    return (
      <Placeholder
        activePrimary="Test a model"
        title="Test a model is the next product slice"
        description="The read-only evidence surfaces are active. Model → Scenario → Test → Review will be enabled only after its preflight and frozen-execution API contract is complete."
      />
    );
  }

  if (route.kind === "compare") {
    return (
      <Placeholder
        activePrimary="Compare"
        title="Compare is not active yet"
        description="Comparison will be enabled only with compatibility-first evidence. Invalid metric deltas will remain hidden for non-comparable runs."
      />
    );
  }

  return (
    <AppShell activePrimary="Overview">
      <StateSurface
        kind="error"
        title="Unknown product route"
        description={`No Performance Lab surface exists for #${route.path}.`}
        action={<Button onClick={() => navigate("overview")}>Go to Overview</Button>}
      />
    </AppShell>
  );
}
