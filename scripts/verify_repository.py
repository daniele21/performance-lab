#!/usr/bin/env python3
"""Zero-dependency structural checks for Performance Lab."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = (
    "plan-workstream",
    "structured-change",
    "design-product-experience",
    "validate-change",
    "preflight-change",
    "remote-preflight",
    "finalize-workstream",
    "review-reference-quality",
)
REQUIRED = (
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    ".editorconfig",
    ".gitignore",
    ".engineering/baseline.json",
    ".engineering/documentation-policy.json",
    ".engineering/commands.json",
    ".engineering/e2e.json",
    ".github/pull_request_template.md",
    ".github/workflows/repository-health.yml",
    "docs/README.md",
    "docs/architecture.md",
    "docs/current-state.md",
    "docs/features/README.md",
    "docs/adr/README.md",
    "docs/workstreams/README.md",
    "scripts/verify_operations.py",
    "scripts/verify_e2e.py",
    "scripts/verify_product_experience.py",
)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--template-mode", action="store_true")
    a = p.parse_args()
    root = Path(a.root).resolve()
    errors = []
    warnings = []
    for r in REQUIRED:
        if not (root / r).is_file():
            errors.append(f"missing required file: {r}")
    for n in CORE:
        if not (root / "skills" / n / "SKILL.md").is_file():
            errors.append(f"missing core skill: skills/{n}/SKILL.md")
    try:
        b = json.loads((root / ".engineering/baseline.json").read_text())
    except Exception as exc:
        errors.append(f"invalid baseline.json: {exc}")
        b = {}
    s = b.get("standard", {})
    if b.get("schema_version") != 1:
        errors.append("baseline schema_version must be 1")
    if s.get("source") != "daniele21/repo-template-sw":
        errors.append("baseline source invalid")
    if s.get("version") != "0.9.1":
        errors.append("baseline standard.version must be 0.9.1")
    if s.get("revision") != "3c6f7aaf48c47595596d1aa4854af8727e9273a7":
        errors.append("baseline revision must match canonical 0.9.1")
    if b.get("target_level") not in {"L0", "L1", "L2"}:
        errors.append("target_level invalid")
    for n in CORE:
        e = b.get("skills", {}).get(n)
        if (
            not isinstance(e, dict)
            or not e.get("source_version")
            or not isinstance(e.get("customized"), bool)
        ):
            errors.append(f"baseline skill metadata invalid: {n}")
    present = [
        x for x in ("node_modules", ".venv", "build", "dist", "__pycache__") if (root / x).exists()
    ]
    if present:
        warnings.append("generated/local directories present: " + ", ".join(present))
    print("Repository baseline check")
    for x in warnings:
        print("WARN:", x)
    for x in errors:
        print("FAIL:", x)
    print("RESULT:", "FAIL" if errors else "PASS")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
