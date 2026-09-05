#!/usr/bin/env python3
"""Verify automated integration and release-gated real-environment semantics."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def expect(section,key,value,errors,prefix):
    if section.get(key)!=value: errors.append(f"{prefix}.{key} must be {value!r}")

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--root",default="."); p.add_argument("--template-mode",action="store_true"); a=p.parse_args(); root=Path(a.root).resolve(); errors=[]
    try: commands=json.loads((root/".engineering/commands.json").read_text()); e2e=json.loads((root/".engineering/e2e.json").read_text())
    except Exception as exc: print(f"FAIL: invalid engineering JSON: {exc}"); return 1
    velocity=commands.get("development_velocity",{}); integ=velocity.get("integration",{}); rel=velocity.get("release",{})
    expect(integ,"automated_e2e_required_when_affected",True,errors,"development_velocity.integration"); expect(integ,"real_environment_blocking",False,errors,"development_velocity.integration"); expect(integ,"real_environment_deferred_to_release",True,errors,"development_velocity.integration"); expect(rel,"required_real_environment_blocking",True,errors,"development_velocity.release")
    policy=e2e.get("stage_policy",{}); ei=policy.get("integration",{}); er=policy.get("release",{})
    expect(ei,"automated_e2e_before_shared_integration",True,errors,"stage_policy.integration"); expect(ei,"real_environment_blocking",False,errors,"stage_policy.integration"); expect(ei,"real_environment_deferred_to_release",True,errors,"stage_policy.integration"); expect(ei,"material_ui_journey_minimum_evidence_mode","full_media",errors,"stage_policy.integration"); expect(er,"required_real_environment_blocking",True,errors,"stage_policy.release")
    print("Stage environment policy check")
    for error in errors: print("FAIL:",error)
    print("RESULT:","FAIL" if errors else "PASS"); return 1 if errors else 0
if __name__=="__main__": sys.exit(main())
