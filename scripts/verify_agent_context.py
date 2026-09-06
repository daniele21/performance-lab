#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

REQUIRED_ROUTES = {"docs", "bug", "contract", "ui", "integration", "release", "resume"}


def inside(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or not path.is_relative_to(root):
        raise ValueError(f"invalid path {relative}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--route")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--workstream")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--template-mode", action="store_true")
    args = parser.parse_args()

    try:
        root = Path(args.root).resolve()
        policy = json.loads((root / ".engineering/documentation-policy.json").read_text())
        baseline = json.loads((root / ".engineering/baseline.json").read_text())
        if policy.get("schema_version") != 2:
            raise ValueError("documentation policy schema_version must be 2")

        routes = policy.get("context_routes", {})
        missing = REQUIRED_ROUTES - set(routes)
        if missing:
            raise ValueError(f"missing routes {sorted(missing)}")

        characters_per_token = policy.get("estimated_token_characters", 4)
        cache: dict[Path, int] = {}

        def cost(path: Path) -> int:
            if path not in cache:
                if not path.is_file():
                    raise ValueError(f"missing context source: {path.relative_to(root)}")
                cache[path] = math.ceil(len(path.read_text()) / characters_per_token)
            return cache[path]

        excluded = set(policy.get("context_exclude_directories", []))
        scoped_guides: list[Path] = []
        for directory, directories, files in os.walk(root):
            directories[:] = [name for name in directories if name not in excluded]
            directory_path = Path(directory)
            if "AGENTS.md" in files and directory_path != root:
                scoped_guides.append((directory_path / "AGENTS.md").resolve())

        affected = [inside(root, path) for path in args.path]
        scoped = {
            guide
            for guide in scoped_guides
            if affected
            and any(guide.parent == path or guide.parent in path.parents for path in affected)
        }

        workstream = None
        if args.workstream:
            workstream = inside(root, args.workstream)
            if not workstream.is_relative_to(root / "docs/workstreams"):
                raise ValueError("workstream must be under docs/workstreams")

        profiles = set(baseline.get("profiles", []))
        selected_routes = [args.route] if args.route else list(routes)
        reports: list[dict[str, object]] = []
        errors: list[str] = []

        for name in selected_routes:
            route = routes.get(name)
            if route is None:
                raise ValueError(f"unknown route {name}")
            required_profile = route.get("requires_profile")
            if required_profile and required_profile not in profiles and not args.template_mode:
                continue

            sources = {inside(root, path) for path in route.get("files", [])}
            if route.get("include_scoped_guides"):
                sources |= scoped
            if route.get("include_workstream") and workstream:
                sources.add(workstream)

            details = [
                {
                    "path": str(path.relative_to(root)),
                    "estimated_tokens": cost(path),
                }
                for path in sorted(sources)
            ]
            total = sum(int(item["estimated_tokens"]) for item in details)
            budget = int(route.get("max_estimated_tokens", 0))
            if total > budget:
                errors.append(f"route {name} ~{total} exceeds {budget}")
            reports.append(
                {
                    "route": name,
                    "estimated_tokens": total,
                    "budget": budget,
                    "files": details,
                }
            )

        bootstrap = cost(root / "AGENTS.md")
        bootstrap_limit = int(
            policy.get("context_targets", {}).get("bootstrap_max_estimated_tokens", 0)
        )
        if bootstrap > bootstrap_limit:
            errors.append(f"bootstrap ~{bootstrap} exceeds {bootstrap_limit}")

        output = {
            "measurement": "characters/policy-factor, not runtime tokens",
            "bootstrap_estimated_tokens": bootstrap,
            "routes": reports,
            "errors": errors,
            "result": "FAIL" if errors else "PASS",
        }
    except Exception as exc:
        output = {"errors": [str(exc)], "result": "FAIL"}

    if args.format == "json":
        print(json.dumps(output, indent=2))
    else:
        print("Agent context health")
        for report in output.get("routes", []):
            print(f"{report['route']}: ~{report['estimated_tokens']} / {report['budget']}")
        for error in output.get("errors", []):
            print("FAIL:", error)
        print("RESULT:", output["result"])

    return output["result"] != "PASS"


if __name__ == "__main__":
    sys.exit(main())
