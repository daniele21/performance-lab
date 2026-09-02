from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile

from performance_lab.domain import MeasurementProvenance, Run, RunStatus, TelemetryLevel
from performance_lab.storage import InvalidRunBundleError, RunNotFoundError, SQLiteRunStore

VALUE01_EVIDENCE_GATE_ID = "VALUE-01B"
LOCAL_LLM_STATUS_COLLECTOR_ID = "local-llm-server-status"
LOCAL_LLM_STATUS_PROTOCOL_VERSION = "local-llm-server-status-v1"


def _check(
    checks: list[dict[str, Any]],
    name: str,
    passed: bool,
    *,
    detail: str,
) -> None:
    checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})


def _identity_summary(run: Run) -> dict[str, Any]:
    fingerprint = run.fingerprint
    return {
        "target_id": fingerprint.target_id,
        "endpoint_identity": fingerprint.endpoint_identity,
        "model": {
            "model_id": fingerprint.model.model_id,
            "revision": fingerprint.model.revision,
            "artifact_digest": fingerprint.model.artifact_digest,
            "quantization": fingerprint.model.quantization,
        },
        "runtime": {
            "name": fingerprint.runtime.name,
            "version": fingerprint.runtime.version,
            "config_digest": fingerprint.runtime.config_digest,
        },
        "hardware": fingerprint.hardware.model_dump(mode="json"),
        "telemetry": fingerprint.telemetry.model_dump(mode="json"),
        "suite": {
            "suite_id": run.suite.suite_id,
            "suite_version": run.suite.suite_version,
        },
    }


def _verify_bundle_round_trip(
    checks: list[dict[str, Any]],
    *,
    bundle_path: Path,
    run: Run,
) -> None:
    if not bundle_path.is_file():
        _check(
            checks,
            "portable_bundle_exists",
            False,
            detail="portable .plab.zip bundle is missing",
        )
        return

    try:
        with ZipFile(bundle_path, "r") as archive:
            names = set(archive.namelist())
    except (OSError, BadZipFile):
        _check(checks, "portable_bundle_shape", False, detail="bundle is not a readable zip")
        return

    unexpected_bundle_detail = (
        "bundle contains unexpected files; local sample sidecar content must not be exported"
    )
    _check(
        checks,
        "portable_bundle_shape",
        names == {"manifest.json", "run.json"},
        detail=(
            "bundle contains only canonical manifest.json + run.json"
            if names == {"manifest.json", "run.json"}
            else unexpected_bundle_detail
        ),
    )

    try:
        with tempfile.TemporaryDirectory(prefix="performance-lab-value01-import-") as directory:
            imported_store = SQLiteRunStore(Path(directory) / "runs.sqlite3")
            imported = imported_store.import_bundle(bundle_path)
    except InvalidRunBundleError:
        _check(
            checks,
            "portable_bundle_round_trip",
            False,
            detail="canonical bundle importer rejected the bundle",
        )
        return

    _check(
        checks,
        "portable_bundle_round_trip",
        imported == run,
        detail=(
            "portable bundle round-trips to the exact canonical completed Run"
            if imported == run
            else "imported Run differs from canonical completed evidence"
        ),
    )


def _verify_identity(checks: list[dict[str, Any]], run: Run) -> None:
    fingerprint = run.fingerprint
    runtime_ok = (
        fingerprint.runtime.name is not None and fingerprint.runtime.config_digest is not None
    )
    hardware_ok = (
        fingerprint.hardware.device_class is not None and fingerprint.hardware.os is not None
    )
    _check(
        checks,
        "first_party_runtime_identity",
        runtime_ok,
        detail=(
            "runtime name + config digest are retained"
            if runtime_ok
            else "required Local LLM Server runtime identity is incomplete"
        ),
    )
    _check(
        checks,
        "first_party_device_identity",
        hardware_ok,
        detail=(
            "device class + OS are retained"
            if hardware_ok
            else "required Local LLM Server hardware identity is incomplete"
        ),
    )


def _verify_telemetry(checks: list[dict[str, Any]], run: Run) -> None:
    descriptor = run.fingerprint.telemetry
    collector_ok = (
        descriptor.level == TelemetryLevel.INSTRUMENTED
        and LOCAL_LLM_STATUS_COLLECTOR_ID in descriptor.collectors
    )
    _check(
        checks,
        "runtime_telemetry_descriptor",
        collector_ok,
        detail=(
            "fingerprint declares instrumented Local LLM Server status telemetry"
            if collector_ok
            else "fingerprint does not declare the required Local LLM Server status collector"
        ),
    )

    runtime_measurements = tuple(
        measurement
        for measurement in run.aggregate_measurements
        if measurement.provenance == MeasurementProvenance.RUNTIME
        and measurement.protocol_version == LOCAL_LLM_STATUS_PROTOCOL_VERSION
    )
    names = {measurement.name for measurement in runtime_measurements}
    measurements_ok = bool(runtime_measurements) and "status_sample_count" in names
    _check(
        checks,
        "runtime_telemetry_measurements",
        measurements_ok,
        detail=(
            "runtime measurements retain provenance/protocol and status sample count"
            if measurements_ok
            else "required Local LLM Server runtime measurements are missing"
        ),
    )


def _verify_sample_content(
    checks: list[dict[str, Any]],
    *,
    store: SQLiteRunStore,
    run: Run,
) -> None:
    if not run.samples:
        _check(
            checks,
            "local_sample_content",
            False,
            detail="completed Run contains no sample execution to inspect",
        )
        return

    retained = False
    for sample in run.samples:
        evidence = store.get_sample_content(
            run.run_id,
            sample.task_id,
            sample.sample_id,
            sample.attempt,
        )
        if evidence is not None:
            retained = True
            break
    _check(
        checks,
        "local_sample_content",
        retained,
        detail=(
            "at least one completed sample has local evidence-rich prompt/output content"
            if retained
            else "no local evidence-rich sample content was retained"
        ),
    )


def verify_value01_evidence(
    *,
    store_path: Path,
    bundle_path: Path,
    run_id: str,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    store = SQLiteRunStore(store_path)
    try:
        run = store.get_completed(run_id)
    except RunNotFoundError:
        _check(
            checks,
            "completed_run",
            False,
            detail="run id is not present as completed immutable evidence",
        )
        return {
            "schema_version": 1,
            "gate_id": VALUE01_EVIDENCE_GATE_ID,
            "status": "FAIL",
            "run_id": run_id,
            "checks": checks,
        }

    assert run is not None
    completed_detail = "run is completed immutable SUCCEEDED evidence"
    if run.status != RunStatus.SUCCEEDED:
        completed_detail = (
            f"run completed with status {run.status.value}; "
            "VALUE-01 requires a successful loop"
        )
    _check(
        checks,
        "completed_run",
        run.status == RunStatus.SUCCEEDED,
        detail=completed_detail,
    )
    _verify_bundle_round_trip(checks, bundle_path=bundle_path, run=run)
    _verify_identity(checks, run)
    _verify_telemetry(checks, run)
    _verify_sample_content(checks, store=store, run=run)

    passed = all(check["status"] == "PASS" for check in checks)
    return {
        "schema_version": 1,
        "gate_id": VALUE01_EVIDENCE_GATE_ID,
        "status": "PASS" if passed else "FAIL",
        "run_id": run.run_id,
        "fingerprint_id": run.fingerprint.fingerprint_id,
        "identity": _identity_summary(run),
        "checks": checks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify retained VALUE-01 real-runtime evidence without inventing missing facts."
        )
    )
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = verify_value01_evidence(
        store_path=args.store.expanduser().resolve(),
        bundle_path=args.bundle.expanduser().resolve(),
        run_id=args.run_id,
    )
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if manifest["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
