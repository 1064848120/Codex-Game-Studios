# Codex execution protocol

## Default flow
AGENTS.md routes game-production requests to docs/ai/STUDIO-DIRECTOR.md.
The user describes a goal in ordinary language. Codex selects the required
workflows internally, runs them and continues to the next step within the scope.
Do not ask users to select skills or type commands to advance the workflow.
This explicit director rule overrides manual handoff instructions in adapted
start/help/other skills. It does not override host instructions or user scope.

## Authorization
Host system/developer instructions and user choices govern execution.
Reuse existing answers and authorization. Do not ask "May I write?" for every
file of an already authorized task. Ask about genuinely unresolved material
choices or actions outside scope. A proposal is not human approval.
Record assumptions and provenance; no invented game numbers or evidence.
Status-only questions and framework questions do not initiate game work.

## Runtime mapping
| Source notation | Codex interpretation |
|---|---|
| Read/Glob/Grep | Available file tools or local search |
| Write/Edit | Codex editing tools within scope |
| Bash | Terminal; Git Bash for original .sh helpers |
| ask_user/AskUserQuestion | Available question tool or normal chat |
| Agent/TeamCreate/team_create | Authorized native subagents or sequential role passes |
| TaskCreate/task_create, task_read/list/update | Host task tools or local workflow ledger |
| Skill, /skill-name, $studio-name | Internally read ai/skills/name/SKILL.md; no user command needed |
| TASK_ARGUMENTS | Director-selected arguments from the user's task/active step |
| Claude model/maxTurns/tools fields | Original metadata; use current Codex settings |
| CLAUDE.md @ imports | Read relevant files explicitly |
| Injected shell command | Execute explicitly and inspect actual output |
| Hooks | Original Claude-only events; not automatically active in Codex |
| Memory/context indicators | Saved checkpoints; never invent context percentages |

Role files are not native agents or permission restrictions. If independent
review is required and unavailable, disclose it. Self-review is not independent.
No external AI processes, bridges, Claude Code login or second product is needed.

## Shared source and checks
The original .claude/ tree and CLAUDE.md stay unchanged for attribution/upgrades.
Use ai/ generated prompts inside Codex. ai/docs/config-resolution.md documents
explicit config resolution through the original Bash helper. Verify Python works;
a Windows Store alias may silently produce no useful result.
Retained .claude/scripts/ utilities are not proof that event hooks are installed.
Apply matching ai/rules from their index before edits.
python tools/ai/validate.py runs the implemented structural checks only.

## Progress and evidence
production/studio/run.json is the director's scoped plan and receipts.
tools/ai/workflow.py records state; it never executes skills or calls models.
Codex performs the selected step and continues in the active session.
Keep production/session-state/active.md compatible with its source template.
Steps need actual outputs, checked acceptance and evidence; no file-count-only
gate passes. Missing tests or required gameplay inspection remain unassessed.
Visible changes need a running game observation and retained evidence.
A blocked plan resumes only when the user input or technical resolution exists.
A changed rule invalidates affected review/evidence and is routed for rechecking.

## Practical limits
Automatic continuation means within an active Codex task, not an always-running
background service. After interruption, "continue" restores progress from disk.
Do not claim that 49 prompts are 49 simultaneous agents or that all 15 Claude
event hooks have been reproduced. The complete upstream production flow is
available; execution still depends on the host's tools, context and decisions.

