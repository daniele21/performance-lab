"""Remove project-owned generated validation, build and frontend output."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED_PATHS = (
    ROOT / ".mypy_cache",
    ROOT / ".pytest_cache",
    ROOT / ".ruff_cache",
    ROOT / "htmlcov",
    ROOT / "build",
    ROOT / "frontend" / "dist",
    ROOT / "frontend" / "coverage",
    ROOT / "frontend" / "test-results",
    ROOT / "frontend" / "test-results-pre-real",
    ROOT / "frontend" / "test-results-full-product",
    ROOT / "frontend" / "playwright-report",
    ROOT / "frontend" / "node_modules" / ".vite",
)


def main() -> int:
    for path in GENERATED_PATHS:
        if path.exists():
            shutil.rmtree(path)
            print(f"removed {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
