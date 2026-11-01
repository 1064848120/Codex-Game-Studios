"""Codex-side event dispatcher for the upstream CCGS hook responsibilities.

Codex does not expose Claude Code's hook transport, so this module accepts the
same logical events as JSON and performs the equivalent action.  The director
calls it at session, tool, compaction and step boundaries; Git hooks call the
same guard for commit and push boundaries.  It is also usable by another
assistant without a Claude installation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
import sys

ROOT = Path(__file__).resolve().parents[2]
EVENTS = {
    "sessionstart": "SessionStart", "session-start": "SessionStart",
    "pretooluse": "PreToolUse", "pre-tool-use": "PreToolUse",
    "posttooluse": "PostToolUse", "post-tool-use": "PostToolUse",
    "instructionsloaded": "InstructionsLoaded", "instructions-loaded": "InstructionsLoaded",
    "notification": "Notification", "precompact": "PreCompact", "pre-compact": "PreCompact",
    "stop": "Stop", "subagentstart": "SubagentStart", "subagent-start": "SubagentStart",
    "subagentstop": "SubagentStop", "subagent-stop": "SubagentStop",
}
BLOCKED_COMMANDS = (
    re.compile(r"(?i)\bgit\s+push\b[^\n]*?(?:--force|-f(?:\s|$))"),
    re.compile(r"(?i)\bgit\s+reset\b[^\n]*?--hard\b"),
    re.compile(r"(?i)\bgit\s+clean\b[^\n]*?(?:-.*[fd]|--force)"),
    re.compile(r"(?i)(?:^|[;&|])\s*(?:rm|remove-item)\b[^\n]*?(?:-rf|-fr|-recurse)"),
)
PROTECTED_PATH = re.compile(r"(?i)(^|/)(?:\.env(?:\..*)?|credentials\.json|secrets\.json|[^/]+\.(?:pem|key))$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_payload(path: str | None) -> dict:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    if not raw.strip():
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Hook payload must be a JSON object")
    return value


def log(root: Path, filename: str, value: dict | str) -> None:
    target = root / "production/session-logs" / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, dict):
        line = json.dumps(value, ensure_ascii=False)
    else:
        line = value
    with target.open("a", encoding="utf-8") as stream:
        stream.write(line + "\n")


def payload_path(root: Path, payload: dict) -> Path | None:
    tool = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else payload
    raw = tool.get("file_path") or tool.get("path") or tool.get("filePath")
    if not isinstance(raw, str) or not raw:
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    try:
        return path.resolve().relative_to(root.resolve()) and path.resolve()
    except ValueError:
        return None


def run_guard(root: Path, profile: str = "fast", scope: str = "changed") -> dict:
    import subprocess
    command = [sys.executable, str(root / "tools/ai/guard.py"), "--profile", profile, "--scope", scope, "--json"]
    p = subprocess.run(command, cwd=root, text=True, capture_output=True)
    try:
        result = json.loads(p.stdout)
    except json.JSONDecodeError:
        result = {"status": "fail", "findings": [{"level": "error", "check": "guard", "message": (p.stdout + p.stderr).strip()}]}
    result["exit_code"] = p.returncode
    return result


def session_start(root: Path, payload: dict) -> dict:
    result = run_guard(root, "fast", "all")
    branch = ""
    try:
        import subprocess
        branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip()
    except Exception:
        pass
    log(root, "events.jsonl", {"at": now(), "event": "SessionStart", "source": payload.get("source", "manual"), "branch": branch, "guard": result["status"]})
    return {"event": "SessionStart", "guard": result, "branch": branch}


def pre_tool(root: Path, payload: dict) -> tuple[dict, int]:
    tool = str(payload.get("tool_name") or payload.get("tool") or "")
    data = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else payload
    command = data.get("command", "") if isinstance(data, dict) else ""
    if command and any(pattern.search(command) for pattern in BLOCKED_COMMANDS):
        message = "Blocked destructive or forceful command; obtain an explicit user decision and use a reversible operation."
        log(root, "events.jsonl", {"at": now(), "event": "PreToolUse", "tool": tool, "blocked": True, "message": message})
        return {"event": "PreToolUse", "decision": "block", "message": message}, 2
    path = payload_path(root, payload)
    if tool.lower() in {"read", "write", "edit"} and path is None and (data.get("file_path") or data.get("path")):
        return {"event": "PreToolUse", "decision": "block", "message": "Path is outside the project root."}, 2
    if path is not None and tool.lower() in {"write", "edit"} and PROTECTED_PATH.search(path.relative_to(root).as_posix()):
        return {"event": "PreToolUse", "decision": "block", "message": "Protected credential path cannot be edited by the studio workflow."}, 2
    if re.search(r"(?i)\bgit\s+commit\b", command):
        result = run_guard(root, "fast", "changed")
        if result.get("status") == "fail":
            return {"event": "PreToolUse", "decision": "block", "guard": result}, 2
    if re.search(r"(?i)\bgit\s+push\b", command):
        result = run_guard(root, "full", "all")
        if result.get("status") == "fail":
            return {"event": "PreToolUse", "decision": "block", "guard": result}, 2
    log(root, "events.jsonl", {"at": now(), "event": "PreToolUse", "tool": tool, "path": str(path) if path else None, "blocked": False})
    return {"event": "PreToolUse", "decision": "allow"}, 0


def post_tool(root: Path, payload: dict) -> tuple[dict, int]:
    path = payload_path(root, payload)
    result = run_guard(root, "fast", "changed")
    log(root, "events.jsonl", {"at": now(), "event": "PostToolUse", "path": str(path) if path else None, "guard": result["status"]})
    # The edit already happened, so this cannot undo it.  Exit 2 feeds the
    # actionable failure back to the assistant, matching PostToolUse semantics.
    return {"event": "PostToolUse", "guard": result}, 2 if result.get("status") == "fail" else 0


def pre_compact(root: Path, payload: dict) -> dict:
    target = root / "production/session-state/active.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    current = ""
    state = root / "production/studio/run.json"
    if state.exists():
        try:
            data = json.loads(state.read_text(encoding="utf-8"))
            pending = next((s["spec"]["id"] for s in data.get("steps", []) if s.get("status") == "pending"), "none")
            current = f"Objective: {data.get('objective', '')}\nStatus: {data.get('status', '')}\nNext step: {pending}\n"
        except Exception as exc:
            current = f"State could not be read: {exc}\n"
    target.write_text("# Codex Studio Checkpoint\n\n" + current + f"Saved: {now()}\nSource: {payload.get('source', 'manual')}\n", encoding="utf-8")
    log(root, "compaction-log.txt", f"Context compaction occurred at {now()}.")
    return {"event": "PreCompact", "checkpoint": target.relative_to(root).as_posix()}


def dispatch(event: str, root: Path, payload: dict) -> tuple[dict, int]:
    canonical = EVENTS.get(event.lower(), event)
    if canonical == "SessionStart": return session_start(root, payload), 0
    if canonical == "PreToolUse": return pre_tool(root, payload)
    if canonical == "PostToolUse": return post_tool(root, payload)
    if canonical == "PreCompact": return pre_compact(root, payload), 0
    if canonical == "InstructionsLoaded":
        log(root, "instructions-loaded.log", {"at": now(), **payload})
        return {"event": canonical, "logged": True}, 0
    if canonical == "Notification":
        message = str(payload.get("message") or "Codex Studio needs your attention")[:200]
        print(f"Notification: {message}")
        return {"event": canonical, "message": message}, 0
    if canonical == "SubagentStop":
        required = payload.get("required_outputs") or payload.get("outputs") or []
        missing = [str(item) for item in required if not (root / str(item)).is_file()]
        if missing:
            result = {"event": canonical, "artifact": "missing", "missing": missing}
            log(root, "events.jsonl", {"at": now(), **result, **payload})
            return result, 2
        log(root, "events.jsonl", {"at": now(), "artifact": "present", **payload})
        return {"event": canonical, "logged": True, "artifact": "present"}, 0
    if canonical in {"SubagentStart", "Stop"}:
        result = run_guard(root, "fast", "changed") if canonical == "Stop" else None
        log(root, "events.jsonl", {"at": now(), "event": canonical, **payload})
        return {"event": canonical, "logged": True, **({"guard": result} if result else {})}, 0
    raise ValueError(f"Unsupported event: {event}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event", choices=sorted(set(EVENTS) | set(EVENTS.values())))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--payload", type=str)
    args = parser.parse_args()
    try:
        result, code = dispatch(args.event, args.root.resolve(), load_payload(args.payload))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"event": args.event, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
