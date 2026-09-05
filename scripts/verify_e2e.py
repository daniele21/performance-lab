#!/usr/bin/env python3
"""Validate the repo-template-sw 0.9.2 E2E environment contract."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

FIDELITY=["host_or_fake","simulated_or_emulated","representative_virtual","representative_physical","target_environment"]
UI=["assertions","screenshots","full_media"]
TRIGGERS={"material_ui_integration_outcome","motion_or_animation","timing_or_progression","navigation_or_transition_sequence","lifecycle_visibility","release_acceptance"}

def expect(section,key,value,errors,prefix):
    if section.get(key)!=value: errors.append(f"{prefix}.{key} must be {value!r}")
def ids(items,label,errors):
    out={}
    if not isinstance(items,list): errors.append(f"{label} must be a list"); return out
    for item in items:
        if not isinstance(item,dict) or not str(item.get("id","")).strip(): errors.append(f"{label} item id required"); continue
        if item["id"] in out: errors.append(f"duplicate {label} id: {item['id']}")
        out[item["id"]]=item
    return out

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--root",default="."); p.add_argument("--template-mode",action="store_true"); a=p.parse_args(); root=Path(a.root).resolve(); errors=[]
    try: data=json.loads((root/".engineering/e2e.json").read_text()); commands=json.loads((root/".engineering/commands.json").read_text())
    except Exception as exc: print(f"FAIL: invalid engineering JSON: {exc}"); return 1
    expect(data,"schema_version",1,errors,"e2e"); expect(data,"contract_version","0.2.1",errors,"e2e")
    status=(data.get("applicability") or {}).get("status"); cstatus=((commands.get("commands") or {}).get("e2e") or {}).get("status")
    if status not in {"required","recommended","n/a"}: errors.append("applicability.status invalid")
    if status=="required" and cstatus!="required": errors.append("required E2E requires commands.e2e.status=required")
    policy=data.get("stage_policy",{}); integ=policy.get("integration",{}); rel=policy.get("release",{})
    expect(integ,"automated_e2e_before_shared_integration",True,errors,"stage_policy.integration"); expect(integ,"real_environment_blocking",False,errors,"stage_policy.integration"); expect(integ,"real_environment_deferred_to_release",True,errors,"stage_policy.integration"); expect(integ,"material_ui_journey_minimum_evidence_mode","full_media",errors,"stage_policy.integration"); expect(integ,"incidental_ui_may_use_assertions",True,errors,"stage_policy.integration")
    expect(rel,"full_validation_required",True,errors,"stage_policy.release"); expect(rel,"release_critical_e2e_required",True,errors,"stage_policy.release"); expect(rel,"required_real_environment_blocking",True,errors,"stage_policy.release")
    ui=data.get("ui_evidence",{}); expect(ui,"modes",UI,errors,"ui_evidence")
    if not TRIGGERS.issubset(set(ui.get("full_media_triggers") or [])): errors.append("ui_evidence.full_media_triggers incomplete")
    expect(data,"fidelity_order",FIDELITY,errors,"e2e")
    targets=ids(data.get("target_environments"),"target_environments",errors); envs=ids(data.get("execution_environments"),"execution_environments",errors); journeys=ids(data.get("critical_journeys"),"critical_journeys",errors)
    for eid,env in envs.items():
        if env.get("fidelity_class") not in FIDELITY: errors.append(f"execution_environments.{eid}.fidelity_class invalid")
        if env.get("automation") not in {"automated","real_environment"}: errors.append(f"execution_environments.{eid}.automation invalid")
        for ref in env.get("target_environment_refs") or []:
            if ref not in targets: errors.append(f"execution_environments.{eid} unknown target {ref}")
    for jid,j in journeys.items():
        if j.get("ui_surface") is True and j.get("minimum_ui_evidence_mode") not in UI: errors.append(f"critical_journeys.{jid}.minimum_ui_evidence_mode invalid")
        if j.get("real_environment_confirmation") not in {"required","conditional","not_required"}: errors.append(f"critical_journeys.{jid}.real_environment_confirmation invalid")
        for ref in j.get("target_environment_refs") or []:
            if ref not in targets: errors.append(f"critical_journeys.{jid} unknown target {ref}")
        for ref in j.get("automated_environment_refs") or []:
            if ref not in envs: errors.append(f"critical_journeys.{jid} unknown automated environment {ref}")
            elif envs[ref].get("automation")!="automated": errors.append(f"critical_journeys.{jid} automated ref {ref} is not automated")
        if not (j.get("automated_environment_refs") or []) and not str(j.get("automation_gap_reason") or "").strip(): errors.append(f"critical_journeys.{jid} needs automated refs or automation_gap_reason")
    print("E2E environment fidelity contract check"); print(f"root: {root}")
    for error in errors: print("FAIL:",error)
    print("RESULT:","FAIL" if errors else "PASS"); return 1 if errors else 0
if __name__=="__main__": sys.exit(main())
