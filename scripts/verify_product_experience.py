#!/usr/bin/env python3
"""Validate the adopted repo-template-sw 0.5 product-ui contract."""

from __future__ import annotations

import json
from pathlib import Path
import sys

REQUIRED_STATES = {"loading", "empty", "error", "disabled"}
REQUIRED_PRINCIPLES = {
    "user_task_model_over_internal_architecture",
    "progressive_disclosure",
    "sensible_defaults",
    "clear_primary_action_hierarchy",
    "platform_appropriate",
    "bounded_information_density",
    "actionable_error_recovery",
}
REQUIRED_DECISIONS = {
    "user_outcome_first",
    "task_model_before_layout",
    "hierarchy_before_visual_polish",
    "states_before_motion",
    "motion_requires_purpose",
    "evidence_before_completion",
}
REQUIRED_ACCESSIBILITY = {
    "keyboard_when_applicable",
    "focus_visibility_order",
    "assistive_semantics",
    "text_scaling_when_applicable",
    "no_color_only_critical_meaning",
    "reduced_motion_when_applicable",
}
REQUIRED_MOTION_FLAGS = {
    "purpose_required",
    "frequent_interactions_are_restrained",
    "gesture_motion_tracks_input",
    "performance_over_decorative_complexity",
    "reduced_motion",
}
REQUIRED_MOTION_PURPOSES = {
    "feedback",
    "continuity",
    "spatial_relationship",
    "state_transition",
    "progress",
    "attention",
}
REQUIRED_GRAPHICS_FLAGS = {
    "functional_before_decorative",
    "ui_understandable_without_decorative_imagery",
}
REQUIRED_EVIDENCE = {
    "bounded_ci_retention",
    "identity_with_source_build_environment",
    "zero_residue_after_ui_e2e",
}
REQUIRED_COLORS = {
    "surface",
    "surface_elevated",
    "text_primary",
    "text_secondary",
    "primary",
    "success",
    "warning",
    "error",
    "border",
    "focus",
}
PLACEHOLDERS = ("<REPLACE", "<PROJECT_")


def load_object(path: Path, errors: list[str]) -> dict:
    if not path.is_file():
        errors.append(f"missing required file: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{path} must contain a JSON object")
        return {}
    return value


def require_true_keys(section: object, keys: set[str], prefix: str, errors: list[str]) -> None:
    if not isinstance(section, dict):
        errors.append(f"{prefix} must be an object")
        return
    for key in sorted(keys):
        if section.get(key) is not True:
            errors.append(f"{prefix}.{key} must be true")


def require_nonempty_list(section: object, key: str, prefix: str, errors: list[str]) -> None:
    if not isinstance(section, dict):
        errors.append(f"{prefix} must be an object")
        return
    value = section.get(key)
    if not isinstance(value, list) or not value:
        errors.append(f"{prefix}.{key} must be a non-empty list")


def find_placeholders(value: object, path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            found.extend(find_placeholders(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_placeholders(child, f"{path}[{index}]"))
    elif isinstance(value, str) and any(marker in value for marker in PLACEHOLDERS):
        found.append(path or "<root>")
    return found


def main() -> int:
    root = Path(".").resolve()
    errors: list[str] = []
    baseline = load_object(root / ".engineering/baseline.json", errors)
    profiles = baseline.get("profiles", []) if baseline else []

    print("Product experience contract check")
    print(f"root: {root}")

    if "product-ui" not in profiles:
        print("SKIP: product-ui profile not adopted")
        print("RESULT: PASS (not applicable)")
        return 0

    ux = load_object(root / "design/ux-contract.json", errors)
    brand = load_object(root / "design/brand-kit.json", errors)

    if ux:
        if ux.get("schema_version") != 1:
            errors.append("ux-contract.schema_version must be 1")
        if ux.get("contract_version") != "0.5.0":
            errors.append("ux-contract.contract_version must be 0.5.0")
        if ux.get("applicable") is not True:
            errors.append("ux-contract.applicable must be true")

        context = ux.get("experience_context")
        for key in ("primary_users", "primary_jobs", "primary_surfaces"):
            require_nonempty_list(context, key, "experience_context", errors)

        require_true_keys(ux.get("decision_model"), REQUIRED_DECISIONS, "decision_model", errors)
        require_true_keys(ux.get("principles"), REQUIRED_PRINCIPLES, "principles", errors)
        require_true_keys(
            ux.get("accessibility"),
            REQUIRED_ACCESSIBILITY,
            "accessibility",
            errors,
        )
        require_true_keys(ux.get("motion"), REQUIRED_MOTION_FLAGS, "motion", errors)
        require_true_keys(ux.get("graphics"), REQUIRED_GRAPHICS_FLAGS, "graphics", errors)
        require_true_keys(ux.get("evidence"), REQUIRED_EVIDENCE, "evidence", errors)

        states = set(ux.get("critical_states") or [])
        if missing := sorted(REQUIRED_STATES - states):
            errors.append("critical_states missing: " + ", ".join(missing))

        motion = ux.get("motion") if isinstance(ux.get("motion"), dict) else {}
        purposes = set(motion.get("supported_purposes") or [])
        if missing := sorted(REQUIRED_MOTION_PURPOSES - purposes):
            errors.append("motion.supported_purposes missing: " + ", ".join(missing))

        graphics = ux.get("graphics")
        require_nonempty_list(graphics, "supported_roles", "graphics", errors)

        journeys = ux.get("critical_journeys")
        if not isinstance(journeys, list) or not journeys:
            errors.append("critical_journeys must be a non-empty list")

        if not isinstance(ux.get("reference_views"), list) or not ux.get("reference_views"):
            errors.append("reference_views must be a non-empty list")

    if brand:
        if brand.get("schema_version") != 1:
            errors.append("brand-kit.schema_version must be 1")
        if brand.get("contract_version") != "0.5.0":
            errors.append("brand-kit.contract_version must be 0.5.0")

        tokens = brand.get("tokens") if isinstance(brand.get("tokens"), dict) else {}
        colors = tokens.get("colors") if isinstance(tokens.get("colors"), dict) else {}
        if missing := sorted(REQUIRED_COLORS - set(colors)):
            errors.append("brand-kit.tokens.colors missing: " + ", ".join(missing))

        motion_tokens = brand.get("motion_tokens")
        if not isinstance(motion_tokens, dict):
            errors.append("brand-kit.motion_tokens must be an object")
        else:
            for key, required in {
                "durations": {"instant", "fast", "standard", "large"},
                "easing": {"enter", "exit", "move"},
                "spring": {"default", "bounce"},
            }.items():
                values = motion_tokens.get(key)
                if not isinstance(values, dict) or not required.issubset(values):
                    errors.append(f"brand-kit.motion_tokens.{key} is incomplete")
            strategy = motion_tokens.get("reduced_motion_strategy")
            if not isinstance(strategy, str) or not strategy.strip():
                errors.append("brand-kit.motion_tokens.reduced_motion_strategy is required")

    for label, payload in (("ux-contract", ux), ("brand-kit", brand)):
        for path in find_placeholders(payload):
            errors.append(f"unresolved placeholder in {label}.{path}")

    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        print(f"RESULT: FAIL ({len(errors)} error(s))")
        return 1

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
