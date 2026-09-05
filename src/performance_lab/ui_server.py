"""Executable loopback composition root for the local browser product."""

from __future__ import annotations

import argparse
import socket
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from performance_lab.application import CampaignQueryService, UIQueryService
from performance_lab.application.campaign_jobs import CampaignJobManager
from performance_lab.application.evaluation_capacity import EvaluationCapacity
from performance_lab.application.run_jobs import RunJobManager
from performance_lab.datasets import (
    available_workload_packs,
    build_general_starter_suite,
    build_workload_pack,
)
from performance_lab.domain import EndpointProfile, Target
from performance_lab.regression import (
    RegressionPolicy,
    RegressionPolicyError,
    load_regression_policy,
)
from performance_lab.regression_api import attach_regression_api
from performance_lab.repeatability_api import attach_repeatability_api
from performance_lab.run_config import RunConfigError, StarterRunConfig, load_starter_run_config
from performance_lab.storage import SQLiteCampaignStore, SQLiteRunStore
from performance_lab.ui_api import create_ui_app

UI_SERVER_HOST = "127.0.0.1"
UI_SERVER_PORT = 8765
DEFAULT_STORE_PATH = Path(".performance-lab/runs.sqlite3")


def _validated_assets_dir(assets_dir: Path | None) -> Path | None:
    if assets_dir is None:
        return None
    resolved = assets_dir.resolve()
    if not resolved.is_dir():
        raise ValueError(f"frontend assets directory does not exist: {resolved}")
    if not (resolved / "index.html").is_file():
        raise ValueError(f"frontend assets directory is missing index.html: {resolved}")
    return resolved


def _ensure_port_available(port: int) -> None:
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((UI_SERVER_HOST, port))
        except OSError as exc:
            raise OSError(f"loopback port {port} is already in use") from exc


def build_local_ui_app(
    config: StarterRunConfig | None = None,
    *,
    assets_dir: Path | None = None,
    regression_policies: tuple[RegressionPolicy, ...] = (),
) -> FastAPI:
    """Build the real local UI graph with optional target and regression policies.

    A missing config is a supported first-run state: Performance Lab starts with its canonical
    local evidence store and no inference target. The browser may then register a bounded
    process-lifetime loopback connection through the existing endpoint-probe API.
    """

    bundle = build_general_starter_suite()
    workload_bundles = tuple(
        build_workload_pack(definition.pack_id, version=definition.version)
        for definition in available_workload_packs()
    )
    store_path = config.store_path if config is not None else DEFAULT_STORE_PATH
    store = SQLiteRunStore(store_path)
    campaign_store = SQLiteCampaignStore(store_path)

    targets: tuple[Target, ...] = ()
    endpoint_profiles: tuple[EndpointProfile, ...] = ()
    if config is not None:
        targets = (
            Target(
                target_id=config.target_id,
                display_name=config.target_id,
                adapter_type="openai-compatible",
                endpoint_profile_id=config.endpoint.profile_id,
                endpoint_identity=config.endpoint_identity,
            ),
        )
        endpoint_profiles = (config.endpoint,)

    queries = UIQueryService(
        store,
        targets=targets,
        endpoint_profiles=endpoint_profiles,
        suites=(bundle.suite,),
        dataset_snapshots=tuple(dataset.snapshot for dataset in bundle.datasets.values()),
        policies=regression_policies,
        inspectable_datasets=tuple(bundle.datasets.values()),
        evaluators=tuple(bundle.evaluators.values()),
        starter_run_template=config,
        workload_packs=workload_bundles,
    )
    capacity = EvaluationCapacity()
    recovered_runs = store.list_working()
    for recovered_run in recovered_runs:
        # Resume is intentionally unsupported. Keep bounded run metadata for the interrupted-job
        # surface, but never preserve potentially sensitive raw prompt/output after a hard restart.
        store.delete_working_sample_content(recovered_run.run_id)
    run_jobs = RunJobManager(
        recovered_runs=recovered_runs,
        capacity=capacity,
    )
    campaign_jobs = CampaignJobManager(campaign_store, capacity=capacity)
    campaign_queries = CampaignQueryService(campaign_store, queries)
    app = create_ui_app(
        queries,
        run_jobs=run_jobs,
        campaign_jobs=campaign_jobs,
        campaign_queries=campaign_queries,
    )
    attach_regression_api(app, queries)
    attach_repeatability_api(app, queries)

    built_assets = _validated_assets_dir(assets_dir)
    if built_assets is not None:
        app.mount("/", StaticFiles(directory=str(built_assets), html=True), name="frontend")
    return app


def serve_local_ui(
    config: StarterRunConfig | None = None,
    *,
    port: int = UI_SERVER_PORT,
    assets_dir: Path | None = None,
    regression_policies: tuple[RegressionPolicy, ...] = (),
) -> None:
    """Serve the API and optional built frontend from one loopback-owned process."""

    _ensure_port_available(port)
    try:
        import uvicorn
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised outside ui extra
        raise RuntimeError(
            "UI server dependency missing; install the project with the 'ui' extra"
        ) from exc

    uvicorn.run(
        build_local_ui_app(
            config,
            assets_dir=assets_dir,
            regression_policies=regression_policies,
        ),
        host=UI_SERVER_HOST,
        port=port,
        log_level="info",
    )


def build_ui_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="performance-lab-ui")
    parser.add_argument(
        "--config",
        required=False,
        type=str,
        default=None,
        help=(
            "Optional versioned StarterRunConfig JSON defining a preconfigured endpoint and "
            "evidence store. Omit it to connect a loopback target from the UI."
        ),
    )
    parser.add_argument(
        "--regression-policy",
        action="append",
        default=[],
        help=(
            "Versioned regression policy JSON available to Compare. Repeat the option to expose "
            "multiple explicit policies; no policy or threshold is invented by default."
        ),
    )
    parser.add_argument(
        "--assets",
        type=str,
        default=None,
        help=(
            "Optional built frontend directory. When set, the UI and /api share one loopback "
            "process."
        ),
    )
    parser.add_argument("--port", type=int, default=UI_SERVER_PORT)
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    output = stdout or sys.stdout
    errors = stderr or sys.stderr
    args = build_ui_parser().parse_args(list(argv) if argv is not None else None)

    try:
        config = load_starter_run_config(Path(args.config)) if args.config else None
        policies = tuple(load_regression_policy(Path(path)) for path in args.regression_policy)
        if not 1 <= args.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        assets_dir = _validated_assets_dir(Path(args.assets)) if args.assets else None
    except (RegressionPolicyError, RunConfigError, ValueError) as exc:
        errors.write(f"error: {exc}\n")
        return 2

    mode = "built product" if assets_dir is not None else "UI API"
    first_run = " · connect a local target in the UI" if config is None else ""
    output.write(f"Performance Lab {mode}: http://{UI_SERVER_HOST}:{args.port}{first_run}\n")
    try:
        if policies:
            serve_local_ui(
                config,
                port=args.port,
                assets_dir=assets_dir,
                regression_policies=policies,
            )
        else:
            # Preserve the legacy call shape for callers/fakes that do not configure regression.
            serve_local_ui(config, port=args.port, assets_dir=assets_dir)
    except (RuntimeError, OSError, ValueError) as exc:
        errors.write(f"error: {exc}\n")
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
