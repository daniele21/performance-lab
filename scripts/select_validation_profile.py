#!/usr/bin/env python3
"""Select validation profile, risk dimensions and concrete CI gates."""
from __future__ import annotations
import argparse, json, subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

PROFILE_RANK={"lean":0,"scoped":1,"strong":2,"full":3}
STAGES=("iteration","integration","release")
EXECUTABLE_SUFFIXES={".py",".js",".jsx",".ts",".tsx",".toml",".json",".yml",".yaml"}
FULL_PREFIXES=(".engineering/",".github/workflows/")
FULL_FILES={"pyproject.toml","uv.lock",".python-version","frontend/package.json","frontend/pnpm-lock.yaml","frontend/.nvmrc","scripts/select_validation_profile.py","scripts/verify_repository.py","scripts/verify_operations.py","scripts/verify_e2e.py","scripts/verify_product_experience.py","scripts/verify_docs.py","scripts/verify_agent_context.py"}
STRONG_PREFIXES=("src/performance_lab/application/","src/performance_lab/adapters/","src/performance_lab/storage/","src/performance_lab/regression/","frontend/src/","frontend/e2e/","tests/e2e/","tests/real_runtime/","design/")
STRONG_FILES={"src/performance_lab/ui_api.py","src/performance_lab/ui_server.py","src/performance_lab/runner.py","src/performance_lab/engine.py","src/performance_lab/release_artifacts.py","scripts/package_release.py","scripts/smoke_release.py","scripts/full_product_e2e.py","frontend/playwright.config.ts","frontend/playwright.full-product.config.ts"}
SCOPED_PREFIXES=("src/","tests/","frontend/")
LEAN_PREFIXES=("docs/","skills/")
LEAN_FILES={"README.md","AGENTS.md","BRANCHING.md","CONTRIBUTING.md","SECURITY.md",".github/pull_request_template.md"}

@dataclass(frozen=True)
class Selection:
    stage:str; profile:str; reason:str; changed_paths:tuple[str,...]; risk_dimensions:tuple[str,...]; required_gates:tuple[str,...]
    run_python:bool; run_frontend:bool; run_product_e2e:bool; run_browser_e2e:bool; run_built_product:bool
    def as_dict(self): return {"stage":self.stage,"profile":self.profile,"reason":self.reason,"changed_paths":list(self.changed_paths),"risk_dimensions":list(self.risk_dimensions),"required_gates":list(self.required_gates),"run_python":self.run_python,"run_frontend":self.run_frontend,"run_product_e2e":self.run_product_e2e,"run_browser_e2e":self.run_browser_e2e,"run_built_product":self.run_built_product}

def _normalize(paths:Iterable[str])->tuple[str,...]: return tuple(sorted({p.strip().replace('\\','/') for p in paths if p.strip()}))
def _has_prefix(path,prefixes): return any(path.startswith(x) for x in prefixes)
def _is_executable(path): return Path(path).suffix.lower() in EXECUTABLE_SUFFIXES

def select(paths:Iterable[str],*,stage:str="integration",promotion:bool=False,force_full:bool=False)->Selection:
    changed=_normalize(paths); risks=[]
    if force_full: profile,reason="full","explicit full validation requested"; risks=["global_validation"]
    elif promotion or stage=="release": profile,reason="full","promotion/release target requires FULL validation"; risks=["release_boundary"]
    elif not changed: profile,reason="full","no changed paths resolved; fail-safe FULL validation"; risks=["unknown_scope"]
    elif any(p in FULL_FILES or _has_prefix(p,FULL_PREFIXES) for p in changed): profile,reason="full","validation/build/dependency contract changed"; risks=["global_validation_build_dependency"]
    elif any(p in STRONG_FILES or _has_prefix(p,STRONG_PREFIXES) for p in changed): profile,reason="strong","cross-boundary, user-facing, persistence, E2E or release-sensitive surface changed"; risks=["cross_product_user_persistence_e2e"]
    elif all(p in LEAN_FILES or _has_prefix(p,LEAN_PREFIXES) or p.endswith('.md') for p in changed): profile,reason="lean","documentation/governance-only change"; risks=["governance"]
    elif any(_has_prefix(p,SCOPED_PREFIXES) for p in changed): profile,reason="scoped","contained implementation surface changed"; risks=["contained_implementation"]
    elif any(_is_executable(p) for p in changed): profile,reason="full","unknown executable/configuration path; fail-safe FULL validation"; risks=["unknown_executable"]
    else: profile,reason="lean","non-executable repository metadata change"; risks=["governance"]
    python_affected=any(p.startswith(("src/","tests/","scripts/")) or p in {"pyproject.toml","uv.lock",".python-version"} for p in changed)
    frontend_affected=any(p.startswith(("frontend/","design/")) for p in changed)
    cross_product=any(p.startswith(("src/performance_lab/application/","src/performance_lab/adapters/","src/performance_lab/storage/","src/performance_lab/regression/","tests/e2e/")) or p in {"src/performance_lab/ui_api.py","src/performance_lab/ui_server.py","src/performance_lab/runner.py","src/performance_lab/engine.py"} for p in changed)
    browser=frontend_affected or any(p.startswith("src/performance_lab/application/") or p in {"src/performance_lab/ui_api.py","src/performance_lab/ui_server.py"} for p in changed)
    package=frontend_affected or any(p in STRONG_FILES or p.startswith(("src/performance_lab/application/","src/performance_lab/storage/")) for p in changed)
    if profile=="full": python_affected=frontend_affected=cross_product=browser=package=True
    if stage=="iteration": cross_product=browser=package=False
    if stage=="release": python_affected=frontend_affected=cross_product=browser=package=True
    gates=["repository-guards"]
    if python_affected: gates.append("python-validation")
    if frontend_affected: gates.append("frontend-validation")
    if cross_product: gates.append("product-e2e")
    if browser: gates.append("browser-e2e")
    if package: gates.append("built-product")
    if stage=="release": gates.append("release-critical")
    return Selection(stage,profile,reason,changed,tuple(risks),tuple(gates),python_affected,frontend_affected,cross_product,browser,package)

def changed_paths(base,head):
    c=subprocess.run(["git","diff","--name-only",f"{base}...{head}"],check=True,text=True,capture_output=True); return _normalize(c.stdout.splitlines())
def write_github_output(path:Path,s:Selection):
    vals={"stage":s.stage,"profile":s.profile,"reason":s.reason,"risk_dimensions":','.join(s.risk_dimensions),"required_gates":','.join(s.required_gates),"run_python":str(s.run_python).lower(),"run_frontend":str(s.run_frontend).lower(),"run_product_e2e":str(s.run_product_e2e).lower(),"run_browser_e2e":str(s.run_browser_e2e).lower(),"run_built_product":str(s.run_built_product).lower(),"affected_scope":','.join(s.changed_paths)}
    with path.open('a') as h:
        for k,v in vals.items(): h.write(f"{k}={v}\n")
def self_test():
    for paths,expected in ((("docs/README.md",),"lean"),(("src/performance_lab/domain/models.py",),"scoped"),(("frontend/src/pages/Overview.tsx",),"strong"),((".engineering/commands.json",),"full"),(("unknown/tool.py",),"full")):
        assert select(paths).profile==expected
    assert select(("frontend/src/App.tsx",),stage="iteration").run_browser_e2e is False
    assert select(("docs/README.md",),stage="release").profile=="full"
    print("validation-profile selector self-test: PASS")
def main():
    p=argparse.ArgumentParser(); p.add_argument("--base"); p.add_argument("--head"); p.add_argument("--paths",nargs="*"); p.add_argument("--stage",choices=STAGES,default="integration"); p.add_argument("--promotion",action="store_true"); p.add_argument("--full",action="store_true"); p.add_argument("--github-output",type=Path); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test: self_test(); return 0
    paths=tuple(a.paths) if a.paths is not None else (() if a.full else changed_paths(a.base,a.head) if a.base and a.head else None)
    if paths is None: raise SystemExit("provide --base/--head, --paths, --full or --self-test")
    s=select(paths,stage=a.stage,promotion=a.promotion,force_full=a.full); print(json.dumps(s.as_dict(),sort_keys=True))
    if a.github_output: write_github_output(a.github_output,s)
    return 0
if __name__=="__main__": raise SystemExit(main())
