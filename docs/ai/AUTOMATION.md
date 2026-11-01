# Portable automation and hook parity

The original CCGS `.claude/hooks/` files remain available as upstream source
material, but Claude Code's `SessionStart`, `PreToolUse`, `PostToolUse`,
`SubagentStop` and `PreCompact` events are not emitted by Codex. Copying their
JSON protocol would create the appearance of enforcement without enforcement.

This adaptation moves the checks to boundaries Codex and Git can actually run.
`tools/ai/hooks.py` is the event-compatible dispatcher; the complete mapping is
in `HOOK-PARITY.md`:

| Upstream responsibility | Portable equivalent | When it runs |
| --- | --- | --- |
| commit data/design checks | `tools/ai/guard.py` | pre-commit hook or explicit guard |
| push/build/test gate | `tools/ai/guard.py --profile full` | pre-push hook or release review |
| generated skill drift | exporter `--check` inside guard | every guard run |
| asset/data validation | batched JSON and catalog checks | every guard run |
| gap detection | advisory design/code gap scan | every guard run |
| subagent artifact contract | workflow receipts and evidence hashes | director step completion |
| session/compact recovery | `production/studio/run.json` and `active.md` | director resume/continue |
| notifications/status line | Codex commentary and normal host UI | host controlled |

Install the optional Git boundary once:

```text
python tools/ai/install-hooks.py install
```

Check or remove it with `status` and `uninstall`. Installation changes only
the local repository Git config; it does not alter the global Git configuration.
The hooks are deliberately opt-in because a framework must not silently change
a user's repository settings.

Run the same checks manually from Codex or another assistant:

```text
python tools/ai/guard.py --profile fast
python tools/ai/guard.py --profile full --scope all
```

`fast` is the edit/commit gate. `full` also runs the adapter tests and, when a
Godot project and executable are present, a headless import check. Missing
tools are reported as `UNASSESSED`; they are never presented as a pass. Use
`--strict` when a release or CI environment must fail on warnings and
unassessed checks.

This is stronger automation than the previous adaptation while staying honest:
Codex still has no universal per-tool hook API, so the director must run the
guard at the start and end of a bounded objective, and Git hooks cover commits
and pushes when the user opts in.
