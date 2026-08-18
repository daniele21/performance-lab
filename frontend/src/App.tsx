import { useEffect, useState } from "react";

import { AppShell, Button, StateSurface } from "./components";
import "./foundation.css";
import { LiveRunPage } from "./pages/live-run";
import { OverviewPage } from "./pages/overview";
import { RunDetailPage } from "./pages/run-detail";
import { RunsPage } from "./pages/runs";
import { TestModelPage } from "./pages/test-model";
import { navigate, parseHash, type AppRoute } from "./routing";

function currentRoute(): AppRoute {
  return parseHash(window.location.hash);
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

  if (route.kind === "test-model") {
    return (
      <TestModelPage
        onLaunched={(jobId) => navigate(`live-run/${encodeURIComponent(jobId)}`)}
      />
    );
  }

  if (route.kind === "live-run") {
    return (
      <LiveRunPage
        jobId={route.jobId}
        onCompleted={(runId) => navigate(`runs/${encodeURIComponent(runId)}`)}
        onTestAgain={() => navigate("test-a-model")}
        onRuns={() => navigate("runs")}
      />
    );
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

  if (route.kind === "compare") {
    return (
      <AppShell activePrimary="Compare">
        <StateSurface
          kind="empty"
          title="Compare is not active yet"
          description="Comparison will be enabled only with compatibility-first evidence. Invalid metric deltas will remain hidden for non-comparable runs."
          action={<Button onClick={() => navigate("overview")}>Back to Overview</Button>}
        />
      </AppShell>
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
