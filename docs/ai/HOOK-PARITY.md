# CCGS hook parity in Codex

The table below is the migration contract. Every upstream hook responsibility
has a Codex-side implementation or an explicit host equivalent. The original
`.claude/hooks/` files remain unchanged for upstream comparison and Claude
Code users; they are not silently treated as active Codex hooks.

| Upstream hook | Codex implementation | Boundary | Result |
| --- | --- | --- | --- |
| `session-start.sh` | `hooks.py SessionStart` + director preflight | session start/resume | branch, guard, checkpoint context |
| `detect-gaps.sh` | `guard.py` gap scan + `project-stage-detect` workflow | session/gate | advisory design/code gaps |
| `update-check.sh` | project update workflow and repository review | session | no hidden network request |
| `log-instructions.sh` | `hooks.py InstructionsLoaded` | instruction load | `production/session-logs/instructions-loaded.log` |
| `validate-read.sh` | `hooks.py PreToolUse` path/security check | before read | outside-root/protected path block |
| `validate-write.sh` | `hooks.py PreToolUse` path/security check | before write | outside-root/protected path block |
| `validate-commit.sh` | `guard.py --profile fast --scope staged` | commit | generated, registry, data, secret and whitespace gate |
| `validate-push.sh` | `guard.py --profile full --scope all` | push | full gate, tests, engine import when available |
| `validate-registry.sh` | `validate.py` catalog/reference checks | every guard | registry consistency |
| `validate-assets.sh` | `guard.py` batched data JSON check | after edit/commit | invalid data blocks the gate |
| `validate-skill-change.sh` | exporter `--check` in `guard.py` | after skill edit | generated layer drift blocks |
| `validate-agent-artifact.sh` | workflow receipt required outputs + hashes | step completion | missing artifact cannot pass |
| `log-agent.sh` / `log-agent-stop.sh` | `hooks.py SubagentStart/Stop` | delegation boundary | append-only event log |
| `pre-compact.sh` | `hooks.py PreCompact` | context compaction | checkpoint and compaction log |
| `session-stop.sh` | `hooks.py Stop` | task stop | append-only stop event |
| `notify.sh` | `hooks.py Notification` + Codex commentary | notification | visible message without Claude toast dependency |
| `yaml-helper.sh` | generated config reference + explicit project reads | every workflow | no injected shell assumption |

Use the dispatcher internally:

```text
python tools/ai/hooks.py SessionStart
python tools/ai/hooks.py PreToolUse --payload payload.json
python tools/ai/hooks.py PostToolUse --payload payload.json
python tools/ai/hooks.py PreCompact
```

The Git boundary is opt-in and uses the same implementation:

```text
python tools/ai/install-hooks.py install
```

This is feature parity at the workflow boundary. Claude Code's proprietary
permission prompt UI, toast implementation, model selection and event transport
remain host-specific; the adapter does not claim those private APIs exist in
Codex. Their project-level effects are represented by the dispatcher, guard,
workflow ledger and visible Codex results.
