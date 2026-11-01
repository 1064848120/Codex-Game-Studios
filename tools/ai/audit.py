"""Audit parity between the upstream CCGS surface and the Codex adapter."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
HOOK_MAP = {
    "session-start.sh": "SessionStart",
    "detect-gaps.sh": "SessionStart",
    "update-check.sh": "SessionStart",
    "log-instructions.sh": "InstructionsLoaded",
    "validate-read.sh": "PreToolUse",
    "validate-write.sh": "PreToolUse",
    "validate-commit.sh": "PreToolUse",
    "validate-push.sh": "PreToolUse",
    "validate-registry.sh": "PreToolUse",
    "validate-assets.sh": "PostToolUse",
    "validate-skill-change.sh": "PostToolUse",
    "validate-agent-artifact.sh": "SubagentStop",
    "log-agent.sh": "SubagentStart",
    "log-agent-stop.sh": "SubagentStop",
    "pre-compact.sh": "PreCompact",
    "session-stop.sh": "Stop",
    "notify.sh": "Notification",
    "yaml-helper.sh": "ConfigResolution",
}
ADAPTER_MAP = {
    "SessionStart": "session_start",
    "PreToolUse": "pre_tool",
    "PostToolUse": "post_tool",
    "InstructionsLoaded": "dispatch",
    "Notification": "dispatch",
    "PreCompact": "pre_compact",
    "Stop": "dispatch",
    "SubagentStart": "dispatch",
    "SubagentStop": "dispatch",
    "ConfigResolution": "guard",
}


def source_events(root: Path) -> set[str]:
    settings = json.loads((root / ".claude/settings.json").read_text(encoding="utf-8"))
    return set(settings.get("hooks", {}))


def audit(root: Path) -> dict:
    findings: list[dict] = []
    hook_dir = root / ".claude/hooks"
    parity = (root / "docs/ai/HOOK-PARITY.md").read_text(encoding="utf-8")
    dispatcher = (root / "tools/ai/hooks.py").read_text(encoding="utf-8")
    guard = (root / "tools/ai/guard.py").read_text(encoding="utf-8")
    for filename, event in HOOK_MAP.items():
        path = hook_dir / filename
        if not path.is_file():
            findings.append({"level": "error", "check": "source-hook", "path": f".claude/hooks/{filename}", "message": "source hook missing"})
        if filename not in parity:
            findings.append({"level": "error", "check": "hook-doc", "path": filename, "message": "source hook is absent from HOOK-PARITY.md"})
        implementation = ADAPTER_MAP[event]
        if implementation not in dispatcher and implementation not in guard:
            findings.append({"level": "error", "check": "hook-implementation", "path": filename, "message": f"no adapter implementation for {event}"})
    for event in source_events(root):
        if event not in ADAPTER_MAP:
            findings.append({"level": "error", "check": "event-coverage", "path": event, "message": "configured source event has no adapter mapping"})
    wrapper_count = len(list((root / ".agents/skills").glob("*/SKILL.md")))
    if wrapper_count != 75:
        findings.append({"level": "error", "check": "skill-discovery", "message": f"expected 75 Codex skill wrappers, found {wrapper_count}"})
    return {"status": "fail" if any(x["level"] == "error" for x in findings) else "pass",
            "source_hook_files": len(HOOK_MAP), "configured_events": sorted(source_events(root)),
            "codex_events": sorted(ADAPTER_MAP), "skill_wrappers": wrapper_count,
            "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    result = audit(args.root.resolve())
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"CCGS parity audit: {result['status'].upper()}")
        print(f"Source hooks: {result['source_hook_files']} | configured events: {len(result['configured_events'])} | Codex wrappers: {result['skill_wrappers']}")
        for finding in result["findings"]:
            print(f"[{finding['level'].upper()}] {finding['check']}: {finding['message']}")
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
