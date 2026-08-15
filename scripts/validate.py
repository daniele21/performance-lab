"""Run the same deterministic validation gate locally and in CI."""

from __future__ import annotations

import subprocess
import sys

COMMANDS = (
    (sys.executable, "-m", "ruff", "format", "--check", "."),
    (sys.executable, "-m", "ruff", "check", "."),
    (sys.executable, "-m", "mypy", "src"),
    (sys.executable, "-m", "pytest"),
)


def main() -> int:
    for command in COMMANDS:
        print("+", " ".join(command), flush=True)
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
