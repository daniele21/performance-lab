from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HOST = "127.0.0.1"
DEFAULT_PRE_REAL_MANIFEST = ROOT / "build" / "pre-real-e2e" / "manifest.json"
TARGET_ID = "local-llm-server-value02"
TERMINAL_CAMPAIGN_STATES = {"succeeded", "failed", "cancelled", "interrupted"}


def normalize_models(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    models = tuple(dict.fromkeys(value.strip() for value in values if value.strip()))
    if len(models) < 2:
        raise ValueError("VALUE-02 requires at least two unique model ids")
    return models


def build_value02_ui_config(
    *,
    base_url: str,
    models: tuple[str, ...],
    store_path: Path,
) -> dict[str, Any]:
    models = normalize_models(models)
    normalized_base = base_url.rstrip("/")
    first_model = models[0]
    return {
        "schema_version": 1,
        "target_id": TARGET_ID,
        "endpoint_identity": normalized_base,
        "endpoint": {
            "profile_id": TARGET_ID,
            "base_url": f"{normalized_base}/v1/",
            "model_selector": first_model,
            "timeout_seconds": 120.0,
        },
        "model_id": first_model,
        "store_path": str(store_path),
        "evidence_mode": "aggregate_safe",
        "local_llm_server_identity": {
            "base_url": normalized_base,
            "model_id": first_model,
            "timeout_seconds": 5.0,
            "required": True,
        },
        "local_llm_server_telemetry": {
            "base_url": normalized_base,
            "model_id": first_model,
            "sample_interval_seconds": 0.05,
            "timeout_seconds": 5.0,
        },
    }


def _git_revision() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    revision = completed.stdout.strip()
    if completed.returncode != 0 or not revision:
        raise RuntimeError("cannot resolve Performance Lab source revision")
    return revision


def _load_pre_real_manifest(path: Path, *, source_revision: str) -> dict[str, Any]:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"cannot read PRE_REAL manifest: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"PRE_REAL manifest is invalid JSON: {path}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError("PRE_REAL manifest must contain an object")
    if raw.get("gate_id") != "PRE_REAL_E2E":
        raise RuntimeError("PRE_REAL manifest has the wrong gate_id")
    if raw.get("status") != "PASS" or raw.get("ready_for_real_environment") is not True:
        raise RuntimeError("PRE_REAL readiness is not PASS/READY_FOR_REAL_ENVIRONMENT")
    browser_layer = raw.get("browser_layer")
    if not isinstance(browser_layer, dict):
        raise RuntimeError("PRE_REAL manifest is missing browser_layer provenance")
    if browser_layer.get("source_revision") != source_revision:
        raise RuntimeError("PRE_REAL evidence is stale for the current Performance Lab revision")
    return raw


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((HOST, 0))
        return int(listener.getsockname()[1])


def _wait_ready(url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 30.0
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"Performance Lab exited before readiness ({process.returncode}): "
                f"{(stderr or stdout).strip()[:500]}"
            )
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
        time.sleep(0.05)
    raise RuntimeError(f"Performance Lab did not become ready: {last_error}")


def _stop_process(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.wait(timeout=5)
        raise RuntimeError("Performance Lab UI did not stop cleanly") from exc


def _assert_port_released(port: int) -> None:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.2)
            if probe.connect_ex((HOST, port)) != 0:
                return
        time.sleep(0.05)
    raise RuntimeError(f"Performance Lab still owns {HOST}:{port} after shutdown")


def _request_json(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"{method} {url} failed with HTTP {exc.code}: {detail}") from exc
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{method} {url} failed: {exc}") from exc


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _candidate_models(planning: Any, *, target_id: str) -> tuple[str, ...]:
    if not isinstance(planning, dict):
        raise RuntimeError("campaign planning response is not an object")
    targets = planning.get("targets")
    if not isinstance(targets, list):
        raise RuntimeError("campaign planning response is missing targets")
    target = next(
        (
            item
            for item in targets
            if isinstance(item, dict)
            and isinstance(item.get("target"), dict)
            and item["target"].get("target_id") == target_id
        ),
        None,
    )
    if not isinstance(target, dict):
        raise RuntimeError(f"configured target is missing from campaign planning: {target_id}")
    candidates = target.get("candidates")
    if not isinstance(candidates, list):
        raise RuntimeError("configured target candidate inventory is invalid")
    return tuple(
        str(item["model_id"])
        for item in candidates
        if isinstance(item, dict) and isinstance(item.get("model_id"), str)
    )


def _case_from_hash(case_hash: str) -> tuple[str, str] | None:
    marker = "/cases/"
    if marker not in case_hash:
        return None
    remainder = case_hash.split(marker, 1)[1]
    parts = remainder.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return None
    return parts[0], parts[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the VALUE-02 real multi-model decision journey against Local LLM Server."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:1235")
    parser.add_argument("--model", action="append", dest="models", required=True)
    parser.add_argument("--assets", type=Path, default=ROOT / "frontend" / "dist")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".performance-lab/value02-real"),
    )
    parser.add_argument(
        "--pre-real-manifest",
        type=Path,
        default=DEFAULT_PRE_REAL_MANIFEST,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        models = normalize_models(args.models)
    except ValueError as exc:
        print(f"VALUE-02 real multi-model E2E failed: {exc}", file=sys.stderr)
        return 2

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    assets = args.assets.expanduser().resolve()
    if not (assets / "index.html").is_file():
        print(
            "VALUE-02 real multi-model E2E failed: built frontend assets are missing",
            file=sys.stderr,
        )
        return 1

    source_revision = _git_revision()
    try:
        _load_pre_real_manifest(
            args.pre_real_manifest.expanduser().resolve(),
            source_revision=source_revision,
        )
    except RuntimeError as exc:
        print(f"VALUE-02 real multi-model E2E failed: {exc}", file=sys.stderr)
        return 1

    store_path = output_dir / "runs.sqlite3"
    config_path = output_dir / "ui-config.json"
    browser_result_path = output_dir / "browser-result.json"
    browser_report_path = output_dir / "playwright-report.json"
    manifest_path = output_dir / "value02-manifest.json"
    campaign_path = output_dir / "campaign.json"
    case_path = output_dir / "case-comparison.json"
    _write_json(
        config_path,
        build_value02_ui_config(base_url=args.base_url, models=models, store_path=store_path),
    )

    ui_port = _free_port()
    base_ui_url = f"http://{HOST}:{ui_port}"
    product: subprocess.Popen[str] | None = None
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "gate_id": "VALUE-02B",
        "status": "FAIL",
        "source_revision": source_revision,
        "target_id": TARGET_ID,
        "endpoint_identity": args.base_url.rstrip("/"),
        "requested_models": list(models),
        "started_at": datetime.now(UTC).isoformat(),
        "steps": [],
    }

    def step(name: str, status: str, detail: str) -> None:
        manifest["steps"].append({"name": name, "status": status, "detail": detail})

    try:
        product = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "performance_lab.ui_server",
                "--config",
                str(config_path),
                "--assets",
                str(assets),
                "--port",
                str(ui_port),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _wait_ready(f"{base_ui_url}/api/v1/health", product)
        step(
            "ui_ready",
            "PASS",
            "built Performance Lab product is ready on an owned loopback port",
        )

        probe = _request_json(
            "POST",
            f"{base_ui_url}/api/v1/targets/{TARGET_ID}/probe",
            payload={},
        )
        if not isinstance(probe, dict) or probe.get("healthy") is not True:
            raise RuntimeError("configured Local LLM Server target probe is not healthy")
        discovered = {
            item.get("model_id")
            for item in probe.get("models", [])
            if isinstance(item, dict) and isinstance(item.get("model_id"), str)
        }
        missing_probe = [model for model in models if model not in discovered]
        if missing_probe:
            raise RuntimeError(
                f"requested models are not discoverable from /v1/models: {missing_probe}"
            )
        step(
            "target_probe",
            "PASS",
            "all requested models are discoverable from one Local LLM Server target",
        )

        planning = _request_json("GET", f"{base_ui_url}/api/v1/campaign-planning")
        planned_models = set(_candidate_models(planning, target_id=TARGET_ID))
        missing_planning = [model for model in models if model not in planned_models]
        if missing_planning:
            raise RuntimeError(
                "configured-target discovery is not reflected in campaign planning: "
                f"{missing_planning}"
            )
        step(
            "campaign_inventory",
            "PASS",
            "requested discovered models are campaign candidates",
        )

        environment = os.environ.copy()
        environment["PERFORMANCE_LAB_REAL_E2E_BASE_URL"] = base_ui_url
        environment["PERFORMANCE_LAB_VALUE02_MODELS"] = ",".join(models)
        environment["PERFORMANCE_LAB_VALUE02_BROWSER_RESULT"] = str(browser_result_path)
        environment["PERFORMANCE_LAB_REAL_E2E_OUTPUT_DIR"] = str(output_dir / "browser-artifacts")
        environment["PERFORMANCE_LAB_REAL_E2E_REPORT"] = str(browser_report_path)
        completed = subprocess.run(
            [
                "pnpm",
                "--dir",
                "frontend",
                "exec",
                "playwright",
                "test",
                "--config",
                "playwright.value02-real-runtime.config.ts",
            ],
            cwd=ROOT,
            env=environment,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"VALUE-02 real browser Playwright failed with exit {completed.returncode}"
            )
        step(
            "browser_journey",
            "PASS",
            "Find best setup completed a real multi-model Campaign and decision drill-down",
        )

        browser_result = json.loads(browser_result_path.read_text(encoding="utf-8"))
        if not isinstance(browser_result, dict) or not isinstance(
            browser_result.get("campaign_id"), str
        ):
            raise RuntimeError("VALUE-02 browser result did not retain a campaign id")
        campaign_id = browser_result["campaign_id"]
        campaign = _request_json("GET", f"{base_ui_url}/api/v1/campaigns/{campaign_id}")
        if not isinstance(campaign, dict) or campaign.get("status") not in TERMINAL_CAMPAIGN_STATES:
            raise RuntimeError("campaign did not reach a terminal state")
        if campaign.get("status") != "succeeded":
            raise RuntimeError(f"real multi-model campaign ended with {campaign.get('status')!r}")
        _write_json(campaign_path, campaign)

        entries = campaign.get("entries")
        if not isinstance(entries, list) or len(entries) < 2:
            raise RuntimeError("campaign did not retain at least two candidate entries")
        run_ids = [
            item.get("run_id")
            for item in entries
            if isinstance(item, dict) and isinstance(item.get("run_id"), str)
        ]
        if len(run_ids) < 2:
            raise RuntimeError("campaign did not retain at least two immutable Run ids")

        case_identity = _case_from_hash(str(browser_result.get("case_route") or ""))
        if case_identity is None:
            cases = _request_json(
                "GET",
                f"{base_ui_url}/api/v1/campaigns/{campaign_id}/cases",
            )
            if not isinstance(cases, list):
                raise RuntimeError("campaign cases response is invalid")
            selected = next(
                (
                    item
                    for item in cases
                    if isinstance(item, dict)
                    and int(item.get("available_candidate_count") or 0) >= 2
                ),
                None,
            )
            if not isinstance(selected, dict):
                raise RuntimeError("no same-case comparison is available across two candidates")
            case_identity = str(selected["task_id"]), str(selected["sample_id"])
        task_id, sample_id = case_identity
        comparison = _request_json(
            "GET",
            f"{base_ui_url}/api/v1/campaigns/{campaign_id}/cases/"
            f"{urllib.parse.quote(task_id, safe='')}/{urllib.parse.quote(sample_id, safe='')}",
        )
        _write_json(case_path, comparison)

        results = campaign.get("results") if isinstance(campaign.get("results"), dict) else {}
        policy = (
            results.get("decision_policy")
            if isinstance(results.get("decision_policy"), dict)
            else {}
        )
        manifest.update(
            {
                "status": "PASS",
                "campaign_id": campaign_id,
                "run_ids": run_ids,
                "decision_policy": {
                    "policy_id": policy.get("policy_id"),
                    "policy_version": policy.get("policy_version"),
                },
                "recommendation_state": browser_result.get("recommendation_state"),
                "case": {"task_id": task_id, "sample_id": sample_id},
                "store_path": str(store_path),
                "campaign_path": str(campaign_path),
                "case_comparison_path": str(case_path),
                "browser_report_path": str(browser_report_path),
            }
        )
        step(
            "retained_evidence",
            "PASS",
            "campaign, immutable Run ids and same-case comparison are retained",
        )
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        manifest["error"] = {"type": type(exc).__name__, "message": str(exc)[:500]}
        step("value02_operator", "FAIL", str(exc)[:500])
    finally:
        try:
            _stop_process(product)
        finally:
            _assert_port_released(ui_port)

    manifest["completed_at"] = datetime.now(UTC).isoformat()
    _write_json(manifest_path, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if manifest["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
