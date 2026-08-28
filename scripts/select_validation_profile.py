#!/usr/bin/env python3
"""Select the narrowest safe validation profile and affected CI jobs from changed paths."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PROFILE_RANK = {"lean": 0, "scoped": 1, "strong": 2, "full": 3}
EXECUTABLE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".toml", ".json", ".yml", ".yaml"}

FULL_PREFIXES = (
    ".engineering/",
    ".github/workflows/",
)
FULL_FILES = {
    "pyproject.toml",
    "requirements/ci-constraints.txt",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/.nvmrc",
    "scripts/select_validation_profile.py",
    "scripts/validate_ci_constraints.py",
    "scripts/verify_repository.py",
    "scripts/verify_operations.py",
    "scripts/verify_e2e.py",
    "scripts/verify_product_experience.py",
    "scripts/verify_docs.py",
    "scripts/verify_agent_context.py",
}
STRONG_PREFIXES = (
    "src/performance_lab/application/",
    "src/performance_lab/adapters/",
    "src/performance_lab/storage/",
    "src/performance_lab/regression/",
    "frontend/src/",
    "frontend/e2e/",
    "tests/e2e/",
    "tests/real_runtime/",
    "design/",
)
STRONG_FILES = {
    "src/performance_lab/ui_api.py",
    "src/performance_lab/ui_server.py",
    "src/performance_lab/runner.py",
    "src/performance_lab/engine.py",
    "src/performance_lab/release_artifacts.py",
    "scripts/package_release.py",
    "scripts/smoke_release.py",
    "scripts/full_product_e2e.py",
    "frontend/playwright.config.ts",
    "frontend/playwright.full-product.config.ts",
}
SCOPED_PREFIXES = (
    "src/",
    "tests/",
    "frontend/",
)
LEAN_PREFIXES = (
    "docs/",
    "skills/",
)
LEAN_FILES = {
    "README.md",
    "AGENTS.md",
    "BRANCHING.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    ".github/pull_request_template.md",
}


@dataclass(frozen=True)
class Selection:
    profile: str
    reason: str
    changed_paths: tuple[str, ...]
    run_python: bool
    run_frontend: bool
    run_product_e2e: bool
    run_browser_e2e: bool
    run_built_product: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "reason": self.reason,
            "changed_paths": list(self.changed_paths),
            "run_python": self.run_python,
            "run_frontend": self.run_frontend,
            "run_product_e2e": self.run_product_e2e,
            "run_browser_e2e": self.run_browser_e2e,
            "run_built_product": self.run_built_product,
        }


def _normalize(paths: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted({path.strip().replace("\\", "/") for path in paths if path.strip()}))


def _has_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def _is_executable(path: str) -> bool:
    return Path(path).suffix.lower() in EXECUTABLE_SUFFIXES


def select(paths: Iterable[str], *, promotion: bool = False, force_full: bool = False) -> Selection:
    changed = _normalize(paths)
    if force_full:
        profile = "full"
        reason = "explicit full validation requested"
    elif promotion:
        profile = "full"
        reason = "promotion/release target requires FULL validation"
    elif not changed:
        profile = "full"
        reason = "no changed paths resolved; fail-safe FULL validation"
    elif any(path in FULL_FILES or _has_prefix(path, FULL_PREFIXES) for path in changed):
        profile = "full"
        reason = "validation/build/dependency contract changed"
    elif any(path in STRONG_FILES or _has_prefix(path, STRONG_PREFIXES) for path in changed):
        profile = "strong"
        reason = "cross-boundary, user-facing, persistence, E2E or release-sensitive surface changed"
    elif all(path in LEAN_FILES or _has_prefix(path, LEAN_PREFIXES) or path.endswith(".md") for path in changed):
        profile = "lean"
        reason = "documentation/governance-only change"
    elif any(_has_prefix(path, SCOPED_PREFIXES) for path in changed):
        profile = "scoped"
        reason = "contained implementation surface changed"
    elif any(_is_executable(path) for path in changed):
        profile = "full"
        reason = "unknown executable/configuration path; fail-safe FULL validation"
    else:
        profile = "lean"
        reason = "non-executable repository metadata change"

    python_affected = any(
        path.startswith(("src/", "tests/", "scripts/", "requirements/")) or path == "pyproject.toml"
        for path in changed
    )
    frontend_affected = any(path.startswith(("frontend/", "design/")) for path in changed)
    cross_product_affected = any(
        path.startswith(
            (
                "src/performance_lab/application/",
                "src/performance_lab/adapters/",
                "src/performance_lab/storage/",
                "src/performance_lab/regression/",
                "tests/e2e/",
            )
        )
        or path in {"src/performance_lab/ui_api.py", "src/performance_lab/ui_server.py", "src/performance_lab/runner.py", "src/performance_lab/engine.py"}
        for path in changed
    )
    browser_affected = frontend_affected or any(
        path.startswith("src/performance_lab/application/")
        or path in {"src/performance_lab/ui_api.py", "src/performance_lab/ui_server.py"}
        for path in changed
    )
    package_affected = frontend_affected or any(
        path in STRONG_FILES
        or path.startswith(("src/performance_lab/application/", "src/performance_lab/storage/"))
        for path in changed
    )

    if profile == "full":
        return Selection(profile, reason, changed, True, True, True, True, True)
    return Selection(
        profile,
        reason,
        changed,
        python_affected,
        frontend_affected,
        profile == "strong" and cross_product_affected,
        profile == "strong" and browser_affected,
        profile == "strong" and package_affected,
    )


def changed_paths(base: str, head: str) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        check=True,
        text=True,
        capture_output=True,
    )
    return _normalize(completed.stdout.splitlines())


def write_github_output(path: Path, selection: Selection) -> None:
    values = {
        "profile": selection.profile,
        "reason": selection.reason,
        "run_python": str(selection.run_python).lower(),
        "run_frontend": str(selection.run_frontend).lower(),
        "run_product_e2e": str(selection.run_product_e2e).lower(),
        "run_browser_e2e": str(selection.run_browser_e2e).lower(),
        "run_built_product": str(selection.run_built_product).lower(),
        "affected_scope": ",".join(selection.changed_paths),
    }
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def self_test() -> None:
    cases = (
        (("docs/README.md",), "lean"),
        (("src/performance_lab/domain/models.py",), "scoped"),
        (("frontend/src/pages/Overview.tsx",), "strong"),
        (("src/performance_lab/ui_api.py",), "strong"),
        ((".engineering/commands.json",), "full"),
        (("unknown/tool.py",), "full"),
    )
    for paths, expected in cases:
        actual = select(paths).profile
        if actual != expected:
            raise AssertionError(f"selector case {paths!r}: expected {expected}, got {actual}")
    if select(("docs/README.md",), promotion=True).profile != "full":
        raise AssertionError("promotion must force FULL validation")
    print("validation-profile selector self-test: PASS")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--paths", nargs="*")
    parser.add_argument("--promotion", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.paths is not None:
        paths = tuple(args.paths)
    elif args.full:
        paths = ()
    elif args.base and args.head:
        paths = changed_paths(args.base, args.head)
    else:
        raise SystemExit("provide --base/--head, --paths, --full or --self-test")

    selection = select(paths, promotion=args.promotion, force_full=args.full)
    print(json.dumps(selection.as_dict(), sort_keys=True))
    if args.github_output is not None:
        write_github_output(args.github_output, selection)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
