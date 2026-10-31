# Internal workflow state contract

This document is for Codex, not a sequence the user must operate.
Use tools/ai/workflow.py to track one bounded objective at a time. Python 3.10+
and the standard library are enough; no model accounts, API keys or CLI bridges.
All commands are executed from the project root by Codex.

## Establish the plan
Build a JSON plan based on the actual artifacts, user's objective, effective rigor
and ai/docs/workflow-catalog.yaml. Never infer completion from file existence.
This example illustrates one design-only task, not the complete game route:

~~~json
{
  "objective": "Complete the requested combat design and balance review",
  "rigor": "standard",
  "steps": [
    {
      "id": "combat-design",
      "workflow": "design-system",
      "role": "game-designer",
      "arguments": "combat",
      "phase": "systems-design",
      "outputs": ["design/gdd/combat.md"],
      "acceptance": ["Damage rules, formulas, edge cases and dependencies are specified"]
    },
    {
      "id": "combat-balance",
      "workflow": "balance-check",
      "role": "economy-designer",
      "arguments": "combat",
      "phase": "systems-design",
      "outputs": ["design/balance/combat-review.md"],
      "acceptance": ["TTK and income assumptions have calculations and unresolved items are explicit"]
    }
  ]
}
~~~

Write the task-specific plan into production/studio/plan.json, then execute
python tools/ai/workflow.py init --plan production/studio/plan.json.
Use distinct step IDs for each system/story/review. Outputs must be meaningful
task artifacts; don't claim a gameplay gate from a prose report alone.
Record captured screenshots/test logs as additional evidence for visible work.

## Internal execution
next returns the first pending step, its workflow path, role path and arguments.
Read those files, then execute the work. The user's next action is not typing a
command. Completion immediately returns the next step, so continue internally.

Write a receipt after verification:

~~~json
{
  "step_id": "combat-design",
  "verdict": "pass",
  "checks": {
    "Damage rules, formulas, edge cases and dependencies are specified": true
  },
  "evidence": ["design/gdd/combat.md"],
  "questions": [],
  "summary": "Describe the inspection and actual results, including provenance."
}
~~~

python tools/ai/workflow.py complete --receipt production/studio/receipt.json

Every planned criterion must have a boolean passing check; all expected outputs
must exist, be nonempty and appear in evidence. Files are hashed. The helper can
verify integrity and order, not truth or gameplay quality; Codex must inspect.
Use versioned evidence reports when later steps will legitimately edit shared
source files. Changed evidence blocks a stale completion claim.

## Recovery
- Technical/decision blocker: block --reason "specific obstacle".
- User reply or fix: write a real resolution note, then resume --resolution <path>.
  A file is a record of the resolution, not proof of user authorization; verify it.
- Missing prerequisite: insert --step <JSON step>. Insertion preserves all other
  pending work and does not clear an unanswered blocker.
- Changed or invalid evidence: reopen --step-id <earliest affected step> --reason
  <change>. This reopens that step and its dependent suffix, preserving old
  receipts in history. Re-run affected work, don't blindly reapprove.
- Completed objective: archive preserves the run before a new init. Never
  archive unfinished work just to avoid a failure.

Run state lives in production/studio/run.json. The upstream active.md checkpoint
records current goal, phase, pending decision, work-in-progress and next action.
No file is an automatic background watcher. Resume checks the actual artifacts.
Only the director writes the ledger; concurrent independent writers are unsupported.

