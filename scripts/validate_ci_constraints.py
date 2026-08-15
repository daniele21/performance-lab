"""Validate that CI constraints cover direct dependencies and match the installed environment."""

from __future__ import annotations

import re
import sys
import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

_EXACT_PIN = re.compile(r"^==([^,;\s]+)$")


def _direct_dependency_names(pyproject_path: Path) -> set[str]:
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = payload["project"]
    requirements = list(project.get("dependencies", []))
    requirements.extend(project.get("optional-dependencies", {}).get("dev", []))
    return {canonicalize_name(Requirement(item).name) for item in requirements}


def _constraint_pins(path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        requirement = Requirement(line)
        specs = list(requirement.specifier)
        if len(specs) != 1:
            raise ValueError(f"constraint must contain one exact pin: {line}")
        match = _EXACT_PIN.fullmatch(str(specs[0]))
        if match is None:
            raise ValueError(f"constraint must use == exact pin: {line}")
        name = canonicalize_name(requirement.name)
        if name in pins:
            raise ValueError(f"duplicate constraint: {name}")
        pins[name] = match.group(1)
    return pins


def validate(pyproject_path: Path, constraints_path: Path) -> list[str]:
    errors: list[str] = []
    pins = _constraint_pins(constraints_path)
    direct = _direct_dependency_names(pyproject_path)

    missing = sorted(direct - set(pins))
    if missing:
        errors.append(f"direct dependencies missing exact CI constraints: {', '.join(missing)}")

    for name, expected in sorted(pins.items()):
        try:
            installed = version(name)
        except PackageNotFoundError:
            errors.append(f"constrained package is not installed: {name}=={expected}")
            continue
        if installed != expected:
            errors.append(
                f"constraint drift for {name}: installed {installed}, expected {expected}"
            )
    return errors


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    if len(args) != 1:
        print("usage: validate_ci_constraints.py <constraints-file>", file=sys.stderr)
        return 2
    constraints_path = Path(args[0])
    errors = validate(Path("pyproject.toml"), constraints_path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"CI constraints validated: {constraints_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
