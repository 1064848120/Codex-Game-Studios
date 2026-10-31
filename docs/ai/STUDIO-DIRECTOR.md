# Codex Studio Director — default conversational workflow

This is the default behavior for game-production requests in this repository.
The user describes the outcome in ordinary language. Codex owns workflow selection,
role routing, prerequisite checks, continuity and verification within the session.
Do not turn the user into an operator of 74 commands.

## Routing priority
1. Follow host instructions and the user's scope, including "only design", "pause",
   existing engine choices and previously settled decisions.
2. Read this document and docs/ai/UNIVERSAL-PROTOCOL.md.
3. Read project.yaml, any project.local.yaml, production/studio/run.json if present,
   and production/session-state/active.md. Check the branch and actual artifacts.
4. Consult ai/docs/workflow-catalog.yaml and only the workflows/roles relevant now.
   The catalog is the source of phase order; workflow-specific requirements and
   effective rigor decide whether a step is required. File count is not completion.

Conceptual questions about the framework are answered directly. Do not create a
game or a new plan merely because a user asks how the framework works.
For actual creation/modification/continuation, use the director loop below.

## Director loop
A. Establish the current bounded objective, such as a game design baseline,
   playable vertical slice, next milestone or specific bug fix. Do not expand
   "make a demo" into shipping a commercial game. Reuse provided answers.
B. Inspect existing material. If needed, run project-stage-detect and adopt
   internally. Read artifacts and identify gaps before deciding the route.
C. Propose meaningful unresolved game choices concisely, with a recommendation.
   Continue independent work. Do not ask which skill to run or whether to perform
   routine handoffs. Existing user authorization covers the named objective.
D. Record an ordered work plan in production/studio/run.json using the internal
   workflow.py helper. Each step names workflow, role, arguments, phase, output
   expectations and observable acceptance criteria. Use the catalog, not a new
   homemade production methodology. Repeated systems/stories get distinct IDs.
E. Ask the helper for the next step. Read ai/skills/<workflow>/SKILL.md and its
   required phase references; read the relevant ai/roles brief and path rules.
   Execute it with its argument string, using Codex's native tools.
F. Validate its output, record evidence and resolve questions. Complete the step
   using a receipt. Immediately select and execute the next eligible step within
   the same authorized objective. Completion of a skill is not completion of the
   user's task. Do not end with "type /..." or "run $... next".
G. If a required choice, failed test or missing capability blocks progress, record
   the blocker and present the user-facing issue, not a command menu. For a
   repairable issue, insert scoped prerequisite/fix work before the blocked step
   and continue. Never skip or forge a failing gate.
H. Stop at the bounded objective, an actual blocker needing user input, or an
   explicit user pause. Save the next action and evidence before a context handoff.
   On "continue", resume from the saved step after rechecking artifacts, not from
   onboarding. Do not promise execution after the host ends the active turn.

No other AI, external CLI session or local message bridge is needed. All steps
are work by Codex in this project. Native subagents are optional and require
host support/authorization; sequential role passes must be labeled self-review.
Never claim an independent review if the host cannot provide one.

## Route families (internal implementation details)
Use these as routing guidance, not a checklist to present for manual invocation.

| Situation | Internal route |
|---|---|
| New concept | start intake -> setup-engine/brainstorm in the suitable order -> required catalog steps at the effective rigor |
| Existing GDD/prototype/code | project-stage-detect -> adopt -> repair only missing/invalid prerequisites; retain valid decisions |
| Systems design | map-systems -> design-system per dependency-ordered MVP system -> required design-review -> review-all-gdds; balance-check for numeric systems |
| Technical setup | create-architecture -> needed architecture-decision -> architecture-review -> create-control-manifest -> test-setup and UX foundations |
| Pre-production | asset/UX work for required screens -> ux-review -> create-epics/create-stories/sprint-plan as rigor requires; prototype/vertical-slice when required or needed |
| Production | story-readiness -> dev-story -> code-review when required -> story-done -> next ready story within scope |
| Rule change | propagate-design-change -> affected GDD, balance, UX and architecture updates -> scoped stories -> regression/acceptance |
| Bug fix | bug-triage (bug-report if needed) -> reproduce -> affected dev-story/fix -> regression-suite/smoke-check -> story-done |
| Polish/release request | applicable catalog gates, balance and playtest evidence -> release-readiness report; publishing still needs authorization |
| Narrow "review only" | selected review workflow -> findings; no implementation or project-wide onboarding |

minimal follows paths.minimal in the catalog; standard/full follow phases with
the corresponding workflow rules. Preserve configured rigor. If not configured,
recommend a level from the game's scope and user's preference and record the
choice; don't silently downgrade systems/economy/UI work to a jam prototype.
Missing engine version must be resolved from installation/docs, never invented.
Missing evidence is "not assessed", not a completed step.
A design-only objective finishes after its design gates, without scaffolding code.

## Overrides to upstream manual handoff behavior
The upstream /start and /help are orientation tools, not an automatic runner.
This Codex director intentionally adds automatic continuation to them:
- start's "never run the next step", "returning user: stop", Phase 7 "Type ..."
  and equivalent command handoff lines do not govern this director.
- help is used as a read-only stage inventory, then the director proceeds.
- "Next: /x", "run /x first" and missing-prerequisite hints route internally to
  ai/skills/x/SKILL.md with the appropriate arguments; no user typing is needed.
- Fresh review requirements stay real. Use an independent permitted native
  reviewer when required; otherwise disclose that gate is not independently met.
- Do not fabricate approval receipts, config outputs, tool results or checks.
- Per-write permission boilerplate is interpreted using existing authorization.
  Genuine unresolved game-design decisions still go to the user.

## Persistent state, not an autonomous daemon
tools/ai/workflow.py manages an ordered in-session plan, evidence hashes,
blockers, repairs and the next step. It never calls a model or executes a skill.
Codex reads its next-step output and performs the work. It is not a background
scheduler. production/studio/run.json is the authoritative director checkpoint.
Preserve the original active.md STATUS/CHECKPOINT regions for upstream helpers.

The next-step output includes a workflow path and continuation instruction for
Codex, not a command for the user. Commands below are internal agent operations:
- init --plan <JSON>: establish a bounded plan, refusing to overwrite an active run.
- next/status: inspect next work, rechecking completed evidence for changes.
- complete --receipt <JSON>: pass the current step with acceptance/evidence.
- block --reason <text>: record a real obstacle.
- resume --resolution <file>: record resolved input and re-open the blocked step.
- insert --step <JSON>: place prerequisite/repair work before current work.
- archive: preserve a completed run before starting another objective.

Receipt format and examples are in docs/ai/WORKFLOW-STATE.md.

