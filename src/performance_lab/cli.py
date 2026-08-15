"""Developer CLI for probing, evaluation runs and machine-readable regression gates."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import TextIO

from performance_lab.adapters import OpenAICompatibleAdapter
from performance_lab.automation import (
    AutomationErrorReport,
    AutomationExitCode,
    evaluate_regression_gate,
    exit_code_for_decision,
)
from performance_lab.ci import append_ci_summary, build_ci_regression_report, write_ci_artifact
from performance_lab.domain import (
    AuthConfig,
    AuthStrategy,
    EndpointProfile,
    ExecutionFingerprint,
    Run,
    load_json,
)
from performance_lab.engine import ProgressEvent, ProgressPhase
from performance_lab.run_config import RunConfigError, load_starter_run_config
from performance_lab.runner import RunExecutionError, execute_starter_run


def _add_regression_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--baseline-run", required=True)
    parser.add_argument("--candidate-run", required=True)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--baseline-id")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="performance-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe = subparsers.add_parser("probe", help="Probe an OpenAI-compatible endpoint")
    probe.add_argument("--base-url", required=True)
    probe.add_argument("--model")
    auth_group = probe.add_mutually_exclusive_group()
    auth_group.add_argument("--bearer-env", help="Environment variable containing bearer token")
    auth_group.add_argument("--api-key-env", help="Environment variable containing API key")
    probe.add_argument("--json", action="store_true", dest="json_output")

    inspect_parser = subparsers.add_parser(
        "inspect", help="Inspect a Run or ExecutionFingerprint JSON"
    )
    inspect_parser.add_argument("path", type=Path)
    inspect_parser.add_argument("--json", action="store_true", dest="json_output")

    run_parser = subparsers.add_parser(
        "run", help="Run the bundled diagnostic suite from a versioned JSON config"
    )
    run_parser.add_argument("--config", required=True, type=Path)
    run_parser.add_argument("--json", action="store_true", dest="json_output")

    regress = subparsers.add_parser(
        "regress", help="Evaluate an explicit baseline/candidate pair against a policy"
    )
    _add_regression_arguments(regress)
    regress.add_argument("--json", action="store_true", dest="json_output")

    regress_ci = subparsers.add_parser(
        "regress-ci", help="Run a regression gate with conservative CI runner semantics"
    )
    _add_regression_arguments(regress_ci)
    regress_ci.add_argument(
        "--artifact",
        type=Path,
        default=Path("performance-lab-regression.json"),
    )
    regress_ci.add_argument("--runner-identity-controlled", action="store_true")
    regress_ci.add_argument("--json", action="store_true", dest="json_output")
    return parser


def main(argv: list[str] | None = None, *, stdout: TextIO | None = None) -> int:
    output = stdout or sys.stdout
    args = build_parser().parse_args(argv)
    if args.command == "probe":
        return asyncio.run(_probe(args, output))
    if args.command == "inspect":
        return _inspect(args, output)
    if args.command == "run":
        return asyncio.run(_run(args, output))
    if args.command == "regress":
        return _regress(args, output)
    if args.command == "regress-ci":
        return _regress_ci(args, output)
    raise AssertionError(f"unhandled command: {args.command}")


async def _probe(args: argparse.Namespace, output: TextIO) -> int:
    auth = AuthConfig()
    if args.bearer_env:
        auth = AuthConfig(strategy=AuthStrategy.BEARER_ENV, credential_env=args.bearer_env)
    elif args.api_key_env:
        auth = AuthConfig(strategy=AuthStrategy.API_KEY_ENV, credential_env=args.api_key_env)
    profile = EndpointProfile(
        profile_id="cli-probe",
        base_url=args.base_url,
        auth=auth,
        model_selector=args.model,
    )
    adapter = OpenAICompatibleAdapter(profile)
    try:
        result = await adapter.probe()
    finally:
        await adapter.aclose()
    if args.json_output:
        output.write(result.model_dump_json(indent=2) + "\n")
    else:
        state = "healthy" if result.healthy else "unhealthy"
        output.write(f"Endpoint: {state}\n")
        output.write(f"Adapter: {result.adapter_id}\n")
        output.write(f"Models: {', '.join(result.models) if result.models else 'unknown'}\n")
        capabilities = result.capabilities.model_dump(mode="json")
        output.write("Capabilities:\n")
        for name, value in capabilities.items():
            output.write(f"  {name}: {value}\n")
    return 0 if result.healthy else 2


async def _run(args: argparse.Namespace, output: TextIO) -> int:
    try:
        config = load_starter_run_config(args.config)
    except RunConfigError as exc:
        output.write(f"error: {exc}\n")
        return 2

    def progress(event: ProgressEvent) -> None:
        if args.json_output:
            return
        if event.phase == ProgressPhase.RUN_STARTED:
            output.write(f"Run started: {event.run_id} ({event.total_samples} samples)\n")
        elif event.phase == ProgressPhase.SAMPLE_COMPLETED:
            output.write(
                f"Progress: {event.completed_samples}/{event.total_samples} "
                f"[{event.sample_status.value if event.sample_status else 'unknown'}]\n"
            )
        elif event.phase == ProgressPhase.RUN_COMPLETED:
            output.write(f"Run completed: {event.run_id}\n")

    try:
        result = await execute_starter_run(config, progress_sink=progress)
    except RunExecutionError as exc:
        output.write(f"error: {exc}\n")
        return 2

    if args.json_output:
        output.write(
            json.dumps(
                {
                    "run_id": result.run.run_id,
                    "status": result.run.status.value,
                    "fingerprint_id": result.run.fingerprint.fingerprint_id,
                    "store_path": str(result.store_path),
                    "bundle_path": str(result.bundle_path),
                    "sample_count": len(result.run.samples),
                },
                sort_keys=True,
            )
            + "\n"
        )
    else:
        output.write(f"Status: {result.run.status.value}\n")
        output.write(f"Fingerprint: {result.run.fingerprint.fingerprint_id}\n")
        output.write(f"Run store: {result.store_path}\n")
        output.write(f"Portable bundle: {result.bundle_path}\n")
    return 0 if result.run.status.value == "succeeded" else 1


def _evaluate_regression_from_args(args: argparse.Namespace):
    return evaluate_regression_gate(
        store_path=args.store,
        baseline_run_id=args.baseline_run,
        candidate_run_id=args.candidate_run,
        policy_path=args.policy,
        baseline_id=args.baseline_id,
    )


def _regress(args: argparse.Namespace, output: TextIO) -> int:
    try:
        report = _evaluate_regression_from_args(args)
    except (LookupError, RuntimeError, ValueError) as exc:
        if args.json_output:
            error = AutomationErrorReport(
                error_type=type(exc).__name__,
                message=str(exc),
            )
            output.write(error.model_dump_json() + "\n")
        else:
            output.write(f"error: {exc}\n")
        return int(AutomationExitCode.ERROR)

    if args.json_output:
        output.write(report.model_dump_json() + "\n")
    else:
        output.write(f"Decision: {report.decision.value}\n")
        output.write(f"Baseline: {report.baseline_run_id} ({report.baseline_fingerprint_id})\n")
        output.write(f"Candidate: {report.candidate_run_id} ({report.candidate_fingerprint_id})\n")
        output.write(f"Policy: {report.policy_id}@{report.policy_version}\n")
        for rule in report.evaluation.rule_results:
            output.write(
                f"  {rule.rule_id}: {rule.state.value} [{rule.dimension.value}] {rule.metric}\n"
            )
    return int(exit_code_for_decision(report.decision))


def _regress_ci(args: argparse.Namespace, output: TextIO) -> int:
    try:
        regression = _evaluate_regression_from_args(args)
        report = build_ci_regression_report(
            regression,
            runner_identity_controlled=args.runner_identity_controlled,
        )
        write_ci_artifact(report, args.artifact)
        summary_destination = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_destination:
            append_ci_summary(report, Path(summary_destination))
    except (LookupError, OSError, RuntimeError, ValueError) as exc:
        error = AutomationErrorReport(
            error_type=type(exc).__name__,
            message=str(exc),
        )
        args.artifact.parent.mkdir(parents=True, exist_ok=True)
        args.artifact.write_text(error.model_dump_json(indent=2) + "\n", encoding="utf-8")
        summary_destination = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_destination:
            with Path(summary_destination).open("a", encoding="utf-8") as handle:
                handle.write("## Performance Lab regression gate — ERROR\n\n")
                handle.write(f"{type(exc).__name__}: {exc}\n")
        if args.json_output:
            output.write(error.model_dump_json() + "\n")
        else:
            output.write(f"error: {exc}\n")
        return int(AutomationExitCode.ERROR)

    if args.json_output:
        output.write(report.model_dump_json() + "\n")
    else:
        output.write(f"Decision: {report.decision.value}\n")
        output.write(f"Artifact: {args.artifact}\n")
        if not report.runner_identity_controlled:
            output.write("Resource rules: NOT_COMPARABLE unless CI runner identity is controlled\n")
    return int(exit_code_for_decision(report.decision))


def _inspect(args: argparse.Namespace, output: TextIO) -> int:
    try:
        payload = args.path.read_text(encoding="utf-8")
    except OSError as exc:
        output.write(f"error: cannot read {args.path}: {exc}\n")
        return 2

    raw: object
    try:
        raw = json.loads(payload)
    except json.JSONDecodeError as exc:
        output.write(f"error: invalid JSON: {exc}\n")
        return 2
    if not isinstance(raw, dict):
        output.write("error: top-level JSON must be an object\n")
        return 2

    try:
        if "run_id" in raw and "fingerprint" in raw:
            value: Run | ExecutionFingerprint = load_json(Run, payload)
            kind = "run"
        else:
            value = load_json(ExecutionFingerprint, payload)
            kind = "execution_fingerprint"
    except ValueError as exc:
        output.write(f"error: {exc}\n")
        return 2

    if args.json_output:
        output.write(value.model_dump_json(indent=2) + "\n")
        return 0
    if isinstance(value, Run):
        output.write(f"Kind: {kind}\n")
        output.write(f"Run ID: {value.run_id}\n")
        output.write(f"Status: {value.status.value}\n")
        output.write(f"Fingerprint: {value.fingerprint.fingerprint_id}\n")
        output.write(f"Samples: {len(value.samples)}\n")
    else:
        output.write(f"Kind: {kind}\n")
        output.write(f"Fingerprint: {value.fingerprint_id}\n")
        output.write(f"Model: {value.model.model_id}\n")
        output.write(f"Adapter: {value.adapter_type}\n")
        output.write(f"Datasets: {len(value.dataset_snapshots)}\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
