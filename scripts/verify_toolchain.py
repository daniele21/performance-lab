#!/usr/bin/env python3
"""Verify the repository-owned uv/pnpm toolchain and reject legacy dependency paths."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_UV = "0.12.5"
EXPECTED_PYTHON_LINE = "3.12"
EXPECTED_NODE = "24.18.0"
EXPECTED_PNPM = "11.24.0"

REQUIRED_FILES = (
    "uv.lock",
    ".python-version",
    "frontend/pnpm-lock.yaml",
    "frontend/.nvmrc",
    "frontend/package.json",
)
FORBIDDEN_FILES = (
    "frontend/package-lock.json",
    "requirements/ci-constraints.txt",
    "scripts/validate_ci_constraints.py",
)
TEXT_OWNERS = (
    "README.md",
    "docs/getting-started.md",
    "docs/ci-reproducibility.md",
    ".engineering/README.md",
    ".engineering/commands.json",
    "CONTRIBUTING.md",
    "frontend/README.md",
    "frontend/AGENTS.md",
    "frontend/playwright.config.ts",
    "frontend/playwright.pre-real.config.ts",
    ".github/workflows/validate.yml",
    ".github/workflows/browser-acceptance.yml",
    ".github/workflows/built-product.yml",
)
FORBIDDEN_MARKERS = (
    "frontend/package-lock.json",
    "requirements/ci-constraints.txt",
    "python -m pip install -e",
    "npm --prefix frontend",
    "npm run build",
    "npm run preview",
)


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        path = ROOT / rel
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty canonical toolchain file: {rel}")

    for rel in FORBIDDEN_FILES:
        if (ROOT / rel).exists():
            errors.append(f"legacy dependency owner must not exist: {rel}")

    python_line = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
    if python_line != EXPECTED_PYTHON_LINE:
        errors.append(f".python-version must be {EXPECTED_PYTHON_LINE}, got {python_line!r}")

    node = (ROOT / "frontend/.nvmrc").read_text(encoding="utf-8").strip()
    if node != EXPECTED_NODE:
        errors.append(f"frontend/.nvmrc must be {EXPECTED_NODE}, got {node!r}")

    package = json.loads((ROOT / "frontend/package.json").read_text(encoding="utf-8"))
    if package.get("packageManager") != f"pnpm@{EXPECTED_PNPM}":
        errors.append(f"frontend packageManager must be pnpm@{EXPECTED_PNPM}")
    engines = package.get("engines", {})
    if engines.get("node") != "24.18.x":
        errors.append("frontend engines.node must be 24.18.x")
    if engines.get("pnpm") != "11.24.x":
        errors.append("frontend engines.pnpm must be 11.24.x")

    commands = json.loads((ROOT / ".engineering/commands.json").read_text(encoding="utf-8"))
    setup = str(commands.get("commands", {}).get("setup", {}).get("run", ""))
    required_setup_fragments = (
        "uv python install 3.12",
        "uv sync --extra dev --locked",
        f"corepack install --global pnpm@{EXPECTED_PNPM}",
        "pnpm --dir frontend install --frozen-lockfile",
    )
    for fragment in required_setup_fragments:
        if fragment not in setup:
            errors.append(f"canonical setup missing: {fragment}")

    for rel in TEXT_OWNERS:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing toolchain text owner: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_MARKERS:
            if marker in text:
                errors.append(f"legacy toolchain marker in {rel}: {marker}")

    print("Toolchain contract check")
    print(f"uv: {EXPECTED_UV}")
    print(f"python default: {EXPECTED_PYTHON_LINE}")
    print(f"node: {EXPECTED_NODE}")
    print(f"pnpm: {EXPECTED_PNPM}")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
