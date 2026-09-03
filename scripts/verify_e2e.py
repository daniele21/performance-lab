#!/usr/bin/env python3
"""Validate Performance Lab's E2E fidelity and risk-based UI evidence contract."""
from __future__ import annotations
import argparse, json
from pathlib import Path
FIDELITY=["host_or_fake","simulated_or_emulated","representative_virtual","representative_physical","target_environment"]
MODES=["assertions","screenshots","full_media"]
TRIGGERS={"motion_or_animation","timing_or_progression","navigation_or_transition_sequence","lifecycle_visibility","release_acceptance"}
def main()->int:
 p=argparse.ArgumentParser(); p.add_argument("--root",default="."); p.add_argument("--template-mode",action="store_true"); a=p.parse_args(); errors=[]
 try:data=json.loads((Path(a.root)/".engineering/e2e.json").read_text())
 except Exception as exc: print(f"FAIL: invalid e2e.json: {exc}"); return 1
 if data.get("schema_version")!=1: errors.append("schema_version must be 1")
 if data.get("contract_version")!="0.2.0": errors.append("contract_version must be 0.2.0")
 app=data.get("applicability",{})
 if app.get("status") not in {"required","recommended","n/a"} or not str(app.get("reason","")).strip(): errors.append("invalid applicability")
 principles=data.get("principles",{})
 for k in ("final_environment_should_confirm_not_discover","execution_capability_separate_from_environment_fidelity","lowest_sufficient_test_level","critical_journeys_only","built_artifact_when_material","residual_fidelity_gaps_explicit","ui_evidence_risk_based"):
  if principles.get(k) is not True: errors.append(f"principles.{k} must be true")
 ui=data.get("ui_evidence",{})
 if ui.get("modes")!=MODES: errors.append("ui_evidence.modes invalid")
 if ui.get("default_mode") not in MODES: errors.append("ui_evidence.default_mode invalid")
 if ui.get("assertions_allowed_when_ui_incidental") is not True: errors.append("incidental UI assertions must be allowed")
 if not TRIGGERS.issubset(set(ui.get("full_media_triggers",[]))): errors.append("full_media_triggers incomplete")
 if data.get("fidelity_order")!=FIDELITY: errors.append("fidelity_order invalid")
 targets={x.get("id") for x in data.get("target_environments",[]) if isinstance(x,dict) and x.get("id")}
 envs={x.get("id"):x for x in data.get("execution_environments",[]) if isinstance(x,dict) and x.get("id")}
 if app.get("status")!="n/a" and (not targets or not envs or not data.get("critical_journeys")): errors.append("applicable E2E needs targets, environments and journeys")
 for eid,e in envs.items():
  if e.get("fidelity_class") not in FIDELITY: errors.append(f"environment {eid} fidelity invalid")
  if e.get("automation") not in {"automated","real_environment"}: errors.append(f"environment {eid} automation invalid")
  if not set(e.get("target_environment_refs",[])).issubset(targets): errors.append(f"environment {eid} target refs invalid")
  if not isinstance(e.get("known_gaps"),list): errors.append(f"environment {eid} known_gaps invalid")
 for j in data.get("critical_journeys",[]):
  if not isinstance(j,dict) or not j.get("id"): errors.append("journey id required"); continue
  jid=j["id"]; mode=j.get("minimum_ui_evidence_mode")
  if j.get("ui_surface") is True and mode not in MODES: errors.append(f"journey {jid} UI mode invalid")
  if j.get("ui_surface") is False and mode not in {None,"assertions"}: errors.append(f"journey {jid} non-UI mode invalid")
  if not set(j.get("target_environment_refs",[])).issubset(targets): errors.append(f"journey {jid} target refs invalid")
  refs=j.get("automated_environment_refs",[])
  if not set(refs).issubset(envs): errors.append(f"journey {jid} automated refs invalid")
  if j.get("minimum_automated_fidelity") not in FIDELITY: errors.append(f"journey {jid} minimum fidelity invalid")
  if j.get("real_environment_confirmation") not in {"required","conditional","not_required"}: errors.append(f"journey {jid} real confirmation invalid")
  if not isinstance(j.get("residual_gaps"),list): errors.append(f"journey {jid} residual_gaps invalid")
  if not refs and not str(j.get("automation_gap_reason","")).strip(): errors.append(f"journey {jid} needs automation gap reason")
 print("E2E environment fidelity contract check")
 for x in errors: print("FAIL:",x)
 print("RESULT:","FAIL" if errors else "PASS")
 return 1 if errors else 0
if __name__=="__main__": raise SystemExit(main())
