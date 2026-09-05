#!/usr/bin/env python3
"""Validate the repo-template-sw 0.9.2 operating contract."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

CORE_COMMANDS=("setup","doctor","dev","check","test","e2e","build","smoke","package","stop","clean")
STATUSES={"required","recommended","optional","n/a"}

def expect(section,key,value,errors,prefix):
    if section.get(key)!=value: errors.append(f"{prefix}.{key} must be {value!r}")

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--root",default="."); p.add_argument("--template-mode",action="store_true"); a=p.parse_args(); root=Path(a.root).resolve(); errors=[]
    try: data=json.loads((root/".engineering/commands.json").read_text())
    except Exception as exc: print(f"FAIL: invalid .engineering/commands.json: {exc}"); return 1
    expect(data,"schema_version",1,errors,"commands")
    expect(data,"contract_version","0.6.1",errors,"commands")
    commands=data.get("commands",{})
    for name in CORE_COMMANDS:
        entry=commands.get(name)
        if not isinstance(entry,dict): errors.append(f"commands.{name} missing"); continue
        if entry.get("status") not in STATUSES: errors.append(f"commands.{name}.status invalid")
        if name in {"setup","check","test","build","clean"} and entry.get("status")=="n/a": errors.append(f"commands.{name} may not be n/a")
        if entry.get("status")!="n/a" and not str(entry.get("run","")).strip(): errors.append(f"commands.{name}.run required")
    v=data.get("development_velocity",{}); expect(v,"default_stage","iteration",errors,"development_velocity"); expect(v,"stages",["iteration","integration","release"],errors,"development_velocity")
    it=v.get("iteration",{}); integ=v.get("integration",{}); rel=v.get("release",{})
    for key in ("exact_head_required","full_diff_review_required","durable_documentation_current_required","remote_preflight_required"): expect(it,key,False,errors,"development_velocity.iteration")
    expect(it,"e2e_default","risk_only",errors,"development_velocity.iteration")
    for key in ("exact_head_required","full_diff_review_required","durable_documentation_current_required","remote_preflight_when_required_gates_unavailable_local","automated_e2e_required_when_affected","real_environment_deferred_to_release"): expect(integ,key,True,errors,"development_velocity.integration")
    expect(integ,"real_environment_blocking",False,errors,"development_velocity.integration"); expect(integ,"e2e_default","affected_critical_journeys",errors,"development_velocity.integration")
    for key in ("exact_head_required","full_diff_review_required","durable_documentation_current_required","full_validation_required","required_real_environment_blocking"): expect(rel,key,True,errors,"development_velocity.release")
    expect(rel,"e2e_default","release_critical_journeys",errors,"development_velocity.release")
    pub=data.get("publication_gate",{}); expect(pub,"applies_from_stage","integration",errors,"publication_gate")
    for key in ("agent_preflight_required","target_base_freshness_required","full_diff_review_required","automatable_gates_must_not_be_delegated_to_user","remote_automated_fallback_required_when_agent_local_unavailable","exact_head_evidence_required"): expect(pub,key,True,errors,"publication_gate")
    execution=data.get("validation_execution",{}); classes=set(execution.get("classes") or [])
    if not {"agent_local","remote_automated","real_environment"}.issubset(classes): errors.append("validation_execution.classes incomplete")
    e2e=data.get("end_to_end",{}); expect(e2e,"ui_evidence_modes",["assertions","screenshots","full_media"],errors,"end_to_end"); expect(e2e,"ui_evidence_selection","risk_based",errors,"end_to_end")
    print("Project operating contract check"); print(f"root: {root}")
    for error in errors: print("FAIL:",error)
    print("RESULT:","FAIL" if errors else "PASS"); return 1 if errors else 0
if __name__=="__main__": sys.exit(main())
