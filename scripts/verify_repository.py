#!/usr/bin/env python3
import json
import sys
from pathlib import Path

root = Path(".")
errors: list[str] = []
required_paths = [
    "AGENTS.md",
    ".engineering/baseline.json",
    ".engineering/commands.json",
    ".engineering/e2e.json",
    ".engineering/documentation-policy.json",
    "scripts/verify_operations.py",
    "scripts/verify_agent_context.py",
]

for path in required_paths:
    if not (root / path).is_file():
        errors.append(f"missing {path}")

try:
    baseline = json.loads((root / ".engineering/baseline.json").read_text())
except Exception as exc:
    errors.append(str(exc))
    baseline = {}

standard = baseline.get("standard", {})
if standard.get("source") != "daniele21/repo-template-sw":
    errors.append("baseline source mismatch")
if standard.get("version") != "0.10.0":
    errors.append("baseline version must be 0.10.0")

print("Repository baseline check")
for error in errors:
    print("FAIL:", error)
print("RESULT:", "FAIL" if errors else "PASS")
sys.exit(bool(errors))
