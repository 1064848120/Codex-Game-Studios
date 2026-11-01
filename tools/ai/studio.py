"""One portable entry point for the Codex Game Studios adapter."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit
import hooks
import workflow


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit", "guard", "event", "skills", "next"))
    parser.add_argument("value", nargs="?")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--profile", choices=("fast", "full"), default="fast")
    parser.add_argument("--scope", choices=("changed", "staged", "all"), default="changed")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "audit":
        result = audit.audit(root)
    elif args.command == "guard":
        from guard import main as guard_main
        return guard_main(["--root", str(root), "--profile", args.profile, "--scope", args.scope] + (["--json"] if args.as_json else []))
    elif args.command == "event":
        if not args.value:
            parser.error("event requires an event name")
        result, code = hooks.dispatch(args.value, root, {})
        if args.as_json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return code
    elif args.command == "skills":
        result = json.loads((root / "ai/skills/index.json").read_text(encoding="utf-8"))
        result = [{"name": x["name"], "description": x.get("description", "")} for x in result]
    else:
        result = workflow.next_step(root) if (root / workflow.STATE).exists() else {"status": "not-started", "message": "No active studio run."}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.as_json or args.command != "skills" else "\n".join(f"{x['name']}: {x['description']}" for x in result))
    return 1 if isinstance(result, dict) and result.get("status") == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
