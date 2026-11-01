"""Install or inspect the portable Game Studios Git hook bridge."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]

def git(*args: str) -> tuple[int, str, str]:
    p = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("install", "uninstall", "status"), nargs="?", default="status")
    args = p.parse_args()
    if args.action == "install":
        rc, _, err = git("config", "core.hooksPath", ".githooks")
        if rc:
            print(err or "Could not configure Git hooks path", file=sys.stderr); return rc
        print("Installed portable hooks from .githooks/.")
        return 0
    if args.action == "uninstall":
        rc, current, err = git("config", "--get", "core.hooksPath")
        if rc == 0 and current == ".githooks":
            rc, _, err = git("config", "--unset", "core.hooksPath")
            if rc not in (0, 5):
                print(err, file=sys.stderr); return rc
            print("Removed the local .githooks override.")
        else:
            print("No .githooks override was installed.")
        return 0
    rc, current, err = git("config", "--get", "core.hooksPath")
    if rc == 0:
        print(f"core.hooksPath={current}")
    else:
        print("core.hooksPath is not configured (hooks are inactive).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
