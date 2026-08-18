"""Verify the pinned local toolchain required by the repository contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
EXPECTED_NODE = (FRONTEND / ".nvmrc").read_text(encoding="utf-8").strip()
EXPECTED_NPM = "11.17.0"


def _version(command: list[str]) -> str:
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        return "missing"
    if completed.returncode != 0:
        return "unavailable"
    return completed.stdout.strip().removeprefix("v")


def main() -> int:
    node = _version(["node", "--version"])
    npm = _version(["npm", "--version"])
    python = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    checks = {
        "python": (python, sys.version_info >= (3, 12)),
        "node": (node, node == EXPECTED_NODE),
        "npm": (npm, npm == EXPECTED_NPM),
        "frontend/package-lock.json": (
            "present" if (FRONTEND / "package-lock.json").is_file() else "missing",
            (FRONTEND / "package-lock.json").is_file(),
        ),
    }

    failed = False
    for name, (value, ok) in checks.items():
        marker = "OK" if ok else "FAIL"
        print(f"[{marker}] {name}: {value}")
        failed = failed or not ok

    if node != EXPECTED_NODE:
        print(f"Expected Node {EXPECTED_NODE}; use frontend/.nvmrc.")
    if npm != EXPECTED_NPM:
        print(f"Expected npm {EXPECTED_NPM}; run: npm install --global npm@{EXPECTED_NPM}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
