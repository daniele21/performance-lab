"""Verify the pinned local toolchain and isolated environment required by the repository."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
EXPECTED_PYTHON = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
EXPECTED_NODE = (FRONTEND / ".nvmrc").read_text(encoding="utf-8").strip()
EXPECTED_UV = "0.12.5"
EXPECTED_PNPM = "11.24.0"


def _version(command: list[str]) -> str:
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        return "missing"
    if completed.returncode != 0:
        return "unavailable"
    return completed.stdout.strip().removeprefix("v")


def main() -> int:
    python = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    node = _version(["node", "--version"])
    uv_output = _version(["uv", "--version"])
    uv = (
        uv_output.removeprefix("uv ").split()[0]
        if uv_output not in {"missing", "unavailable"}
        else uv_output
    )
    pnpm = _version(["pnpm", "--version"])
    expected_venv = (ROOT / ".venv").resolve()
    active_venv = Path(sys.prefix).resolve()

    checks = {
        "python": (python, python.startswith(f"{EXPECTED_PYTHON}.")),
        "uv": (uv, uv == EXPECTED_UV),
        ".venv": (str(active_venv), active_venv == expected_venv),
        "uv.lock": (
            "present" if (ROOT / "uv.lock").is_file() else "missing",
            (ROOT / "uv.lock").is_file(),
        ),
        "node": (node, node == EXPECTED_NODE),
        "pnpm": (pnpm, pnpm == EXPECTED_PNPM),
        "frontend/pnpm-lock.yaml": (
            "present" if (FRONTEND / "pnpm-lock.yaml").is_file() else "missing",
            (FRONTEND / "pnpm-lock.yaml").is_file(),
        ),
    }

    failed = False
    for name, (value, ok) in checks.items():
        marker = "OK" if ok else "FAIL"
        print(f"[{marker}] {name}: {value}")
        failed = failed or not ok

    if uv != EXPECTED_UV:
        print(f"Expected uv {EXPECTED_UV}.")
    if active_venv != expected_venv:
        print("Expected the repository-owned .venv; run: uv sync --extra dev --locked")
    if node != EXPECTED_NODE:
        print(f"Expected Node {EXPECTED_NODE}; use frontend/.nvmrc.")
    if pnpm != EXPECTED_PNPM:
        print(
            f"Expected pnpm {EXPECTED_PNPM}; enable Corepack and use the version pinned in "
            "frontend/package.json."
        )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
