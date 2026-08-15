"""Minimal developer CLI for endpoint probing and evidence inspection."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import TextIO

from performance_lab.adapters import OpenAICompatibleAdapter
from performance_lab.domain import (
    AuthConfig,
    AuthStrategy,
    EndpointProfile,
    ExecutionFingerprint,
    Run,
    load_json,
)


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
    return parser


def main(argv: list[str] | None = None, *, stdout: TextIO | None = None) -> int:
    output = stdout or sys.stdout
    args = build_parser().parse_args(argv)
    if args.command == "probe":
        return asyncio.run(_probe(args, output))
    if args.command == "inspect":
        return _inspect(args, output)
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
