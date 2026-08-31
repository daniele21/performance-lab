import { useEffect, useState } from "react";

import { AppShell, Button, StateSurface } from "./components";
import "./foundation.css";
import { BenchmarkDetailPage } from "./pages/benchmark-detail";
import { CampaignPage } from "./pages/campaign";
import { ComparePage } from "./pages/compare";
import { FindBestSetupPage } from "./pages/find-best-setup";
import { LibraryPage } from "./pages/library";
import { LiveRunPage } from "./pages/live-run";
import { OverviewPage } from "./pages/overview";
import { RunDetailPage } from "./pages/run-detail";
import { RunsPage } from "./pages/runs";
import { SampleEvidencePage } from "./pages/sample-evidence";
import { SettingsPage } from "./pages/settings";
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
    return (
      <OverviewPage
        onFindBestSetup={() => navigate("find-best-setup")}
        onTestModel={() => navigate("test-a-model")}
      />
    );
  }

  if (route.kind === "best-setup") {
    return (
      <FindBestSetupPage
        onManualTest={() => navigate("test-a-model")}
        onCampaignStarted={(campaignId) =>
          navigate(`campaigns/${encodeURIComponent(campaignId)}`)
        }
      />
    );
  }

  if (route.kind === "campaign") {
    return (
      <CampaignPage
        campaignId={route.campaignId}
        onOpenRun={(runId) => navigate(`runs/${encodeURIComponent(runId)}`)}
        onNewCampaign={() => navigate("find-best-setup")}
      />
    );
  }

  if (route.kind === "test-model") {
    return (
      <TestModelPage onLaunched={(jobId) => navigate(`live-run/${encodeURIComponent(jobId)}`)} />
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

  if (route.kind === "sample-evidence") {
    return (
      <SampleEvidencePage
        runId={route.runId}
        taskId={route.taskId}
        sampleId={route.sampleId}
        attempt={route.attempt}
      />
    );
  }

  if (route.kind === "benchmark-detail") {
    return <BenchmarkDetailPage suiteId={route.suiteId} suiteVersion={route.suiteVersion} />;
  }

  if (route.kind === "library") return <LibraryPage section={route.section} />;

  if (route.kind === "settings") return <SettingsPage section={route.section} />;

  if (route.kind === "compare") {
    return <ComparePage initialCandidateRunId={route.runId} />;
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
