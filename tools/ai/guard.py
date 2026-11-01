"""Portable project guard used by Codex and optional Git hooks.

This is deliberately independent of Claude Code's event API.  It checks the
same failure classes at explicit boundaries: generated drift, catalog and
JSON integrity, repository hygiene, workflow state, and (when requested) the
adapter tests and engine import.  A check that cannot run is reported as
unassessed instead of silently passing.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA_RE = re.compile(r"^(assets|Assets|Content)/(?:.*/)?[Dd]ata/.*\.[Jj][Ss][Oo][Nn]$")
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|secret[_-]?key)\s*[:=]\s*[\"'][^\"']{16,}[\"']"),
)


class Finding:
    def __init__(self, level: str, check: str, message: str, path: str = ""):
        self.level, self.check, self.message, self.path = level, check, message, path

    def as_dict(self):
        return {"level": self.level, "check": self.check, "message": self.message, **({"path": self.path} if self.path else {})}


def run(cmd: list[str], root: Path, timeout: int = 60) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)


def project_files(root: Path, scope: str) -> list[Path]:
    """Return changed files for hook scope, or all files for a full audit."""
    if scope == "all":
        return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts]
    names: set[str] = set()
    diff_args = (("diff", "--name-only", "--cached"),) if scope == "staged" else (("diff", "--name-only", "--cached"), ("diff", "--name-only"))
    for args in diff_args:
        rc, out, _ = run(["git", *args], root)
        if rc == 0:
            names.update(x.strip() for x in out.splitlines() if x.strip())
    if scope != "staged":
        rc, out, _ = run(["git", "status", "--porcelain", "--untracked-files=all"], root)
        if rc == 0:
            for line in out.splitlines():
                if len(line) >= 4:
                    name = line[3:]
                    if " -> " in name:
                        name = name.split(" -> ", 1)[1]
                    names.add(name)
    return [root / n.replace("/", os.sep) for n in sorted(names) if (root / n.replace("/", os.sep)).is_file()]


def rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def check_generated(root: Path, findings: list[Finding]):
    spec = importlib_spec(root / "tools/ai/export-universal.py")
    try:
        spec.run(check=True, root=root)
    except Exception as exc:  # exporter intentionally raises actionable drift errors
        findings.append(Finding("error", "generated", str(exc)))


def importlib_spec(path: Path):
    import importlib.util
    module_spec = importlib.util.spec_from_file_location("ccgs_exporter", path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def check_structure(root: Path, findings: list[Finding]):
    try:
        validate = importlib_spec(root / "tools/ai/validate.py")
        validate.check(root)
    except Exception as exc:
        findings.append(Finding("error", "structure", str(exc)))


def check_hook_parity(root: Path, findings: list[Finding]):
    try:
        audit = importlib_spec(root / "tools/ai/audit.py")
        result = audit.audit(root)
        for item in result["findings"]:
            findings.append(Finding(item["level"], item["check"], item["message"], item.get("path", "")))
    except Exception as exc:
        findings.append(Finding("error", "hook-parity", str(exc)))


def check_json_data(root: Path, findings: list[Finding]):
    for path in root.rglob("*.json"):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if not DATA_RE.match(rel(root, path)):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            findings.append(Finding("error", "data-json", f"Invalid data JSON: {exc}", rel(root, path)))


def check_git_whitespace(root: Path, findings: list[Finding]):
    rc, out, err = run(["git", "diff", "--check", "HEAD"], root)
    if rc != 0:
        findings.append(Finding("error", "git-diff", (out + err).strip() or "git diff --check failed"))


def check_secrets(root: Path, findings: list[Finding], scope: str):
    for path in project_files(root, scope):
        name = rel(root, path)
        if any(part in {".git", "node_modules", "__pycache__", ".scratch", "dist"} for part in path.parts):
            continue
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        # Do not interpret compiled game/editor binaries as source text.  A
        # binary may contain an incidental token-shaped byte sequence.
        if b"\x00" in raw[:8192]:
            continue
        text = raw.decode("utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(Finding("error", "secret-scan", "Possible credential or private key in project file", name))
                break


def check_workflow(root: Path, findings: list[Finding]):
    state = root / "production/studio/run.json"
    if not state.exists():
        return
    try:
        workflow = importlib_spec(root / "tools/ai/workflow.py")
        workflow.load(root)
        result = workflow.next_step(root)
        if result.get("status") == "blocked":
            findings.append(Finding("warning", "workflow", result.get("reason", "workflow is blocked")))
    except Exception as exc:
        findings.append(Finding("error", "workflow", str(exc)))


def check_gaps(root: Path, findings: list[Finding]):
    """Portable approximation of detect-gaps.sh; gaps remain advisory."""
    code_roots = [root / x for x in ("src", "Assets", "Source") if (root / x).is_dir()]
    has_code = any(any(p.suffix in {".gd", ".cs", ".cpp", ".h", ".uasset"} for p in d.rglob("*")) for d in code_roots)
    design = root / "design"
    concepts = list((design / "gdd").glob("*.md")) if (design / "gdd").is_dir() else []
    brief = design / "game-brief.md"
    if has_code and not concepts and not brief.exists():
        findings.append(Finding("warning", "gap-detect", "Code exists without a design brief or GDD"))


def check_tests(root: Path, findings: list[Finding]):
    rc, out, err = run([sys.executable, "-m", "unittest", "discover", "-s", "tests/adapter", "-v"], root, timeout=180)
    if rc != 0:
        findings.append(Finding("error", "adapter-tests", (out + err).strip()[-4000:] or "adapter tests failed"))


def check_engine(root: Path, findings: list[Finding]):
    project = root / "project.godot"
    if not project.exists():
        findings.append(Finding("unassessed", "engine", "No Godot project.godot found; engine check not applicable"))
        return
    godot = shutil.which("godot") or shutil.which("godot4")
    if not godot:
        findings.append(Finding("unassessed", "engine", "Godot executable not found; import check not run"))
        return
    rc, out, err = run([godot, "--headless", "--path", str(root), "--editor", "--quit"], root, timeout=180)
    if rc != 0:
        findings.append(Finding("error", "engine", (out + err).strip()[-4000:] or "Godot import check failed"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--profile", choices=("fast", "full"), default="fast")
    parser.add_argument("--scope", choices=("changed", "staged", "all"), default="changed")
    parser.add_argument("--strict", action="store_true", help="Treat warnings and unassessed checks as failures")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    findings: list[Finding] = []
    check_generated(root, findings)
    check_structure(root, findings)
    check_hook_parity(root, findings)
    check_json_data(root, findings)
    check_git_whitespace(root, findings)
    check_secrets(root, findings, "all" if args.scope == "all" else "changed")
    check_workflow(root, findings)
    check_gaps(root, findings)
    if args.profile == "full":
        check_tests(root, findings)
        check_engine(root, findings)
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level in {"warning", "unassessed"}]
    if args.strict:
        errors.extend(warnings)
    result = {"status": "fail" if errors else ("warn" if warnings else "pass"),
              "profile": args.profile, "scope": args.scope,
              "checks": {"errors": len(errors), "warnings": len(warnings), "strict": args.strict},
              "findings": [f.as_dict() for f in findings]}
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Codex guard: {result['status'].upper()} ({args.profile}/{args.scope})")
        for f in findings:
            print(f"[{f.level.upper()}] {f.check}: {f.message}{' — ' + f.path if f.path else ''}")
        if not findings:
            print("All configured checks passed.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
