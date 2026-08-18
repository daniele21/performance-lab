"""Executable loopback composition root for the local browser product."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import TextIO

from fastapi import FastAPI

from performance_lab.application import UIQueryService
from performance_lab.application.run_jobs import RunJobManager
from performance_lab.datasets import build_general_starter_suite
from performance_lab.domain import Target
from performance_lab.run_config import RunConfigError, StarterRunConfig, load_starter_run_config
from performance_lab.storage import SQLiteRunStore
from performance_lab.ui_api import create_ui_app

UI_SERVER_HOST = "127.0.0.1"
UI_SERVER_PORT = 8765


def build_local_ui_app(config: StarterRunConfig) -> FastAPI:
    """Build the real local UI graph from one versioned starter execution config."""

    bundle = build_general_starter_suite()
    store = SQLiteRunStore(config.store_path)
    target = Target(
        target_id=config.target_id,
        display_name=config.target_id,
        adapter_type="openai-compatible",
        endpoint_profile_id=config.endpoint.profile_id,
        endpoint_identity=config.endpoint_identity,
    )
    queries = UIQueryService(
        store,
        targets=(target,),
        endpoint_profiles=(config.endpoint,),
        suites=(bundle.suite,),
        dataset_snapshots=tuple(dataset.snapshot for dataset in bundle.datasets.values()),
        starter_run_template=config,
    )
    run_jobs = RunJobManager(recovered_runs=store.list_working())
    return create_ui_app(queries, run_jobs=run_jobs)


def serve_local_ui(config: StarterRunConfig, *, port: int = UI_SERVER_PORT) -> None:
    """Serve the UI API on loopback only.

    Built-product/static-asset ownership remains a later release task. During UI
    development Vite proxies `/api` to this fixed local API listener.
    """

    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    try:
        import uvicorn
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised outside dev extra
        raise RuntimeError(
            "UI server dependency missing; install the project with the 'ui' extra"
        ) from exc

    uvicorn.run(
        build_local_ui_app(config),
        host=UI_SERVER_HOST,
        port=port,
        log_level="info",
    )


def build_ui_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="performance-lab-ui")
    parser.add_argument(
        "--config",
        required=True,
        type=str,
        help="Versioned StarterRunConfig JSON defining the local endpoint and evidence store.",
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

    from pathlib import Path

    try:
        config = load_starter_run_config(Path(args.config))
        if not 1 <= args.port <= 65535:
            raise ValueError("port must be between 1 and 65535")
    except (RunConfigError, ValueError) as exc:
        errors.write(f"error: {exc}\n")
        return 2

    output.write(f"Performance Lab UI API: http://{UI_SERVER_HOST}:{args.port}\n")
    try:
        serve_local_ui(config, port=args.port)
    except (RuntimeError, OSError) as exc:
        errors.write(f"error: {exc}\n")
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
