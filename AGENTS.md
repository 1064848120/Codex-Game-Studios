# Game Studios — portable project instructions

This local adaptation keeps the MIT-licensed upstream Claude Code Game Studios
under .claude/ and adds Codex skills and a vendor-neutral workflow layer.

## Entry
For game creation, modification or continuation, act as the studio director:
read docs/ai/STUDIO-DIRECTOR.md and run its full loop by default. The user speaks
in ordinary language; select and execute the workflows internally. Never require
the user to type a skill name to move to the next authorized stage. Conceptual
questions are answered directly, without starting game development.
Read docs/ai/UNIVERSAL-PROTOCOL.md, project.yaml and the active task before work.
Use ai/skills/index.json to select a workflow, ai/roles/index.json for domain
expertise, and ai/rules/index.json for applicable file scopes.
Codex discovers .agents/skills/studio-*/SKILL.md. No .codex/skills installation
or model configuration is required. Plain-chat assistants can read the same files.
Read docs/ai/HOOK-PARITY.md when a task touches automation, validation, session
recovery or delegation. At the start and end of a bounded objective, invoke the
portable event dispatcher and guard internally; do not ask the user to operate
those commands.

## Scope and design
Existing user instructions and authorization take precedence over template
approval prompts. Carry out authorized local work; ask only for unresolved
material choices or actions outside that scope. Don't ask permission per file.
A proposed number is not an observed fact or an approved rule. Mark its source.
For game changes, trace rules -> data/formulas -> code -> acceptance evidence.
Keep UI, simulation and persistence responsibilities separate.
Honor the user's chosen engine. If undecided, compare engines against the target
platform, scope and experience before choosing. Pin a real verified version.
This repository itself is a framework, not a finished game.

## Role and rule application
Read the relevant ai/rules documents before editing their paths. Their original
glob scope is shown in each document; they are not automatically enforced.
Role files are briefs, not registered native agents or permission restrictions.
Use the current host model. Delegation requires host support and authorization;
otherwise use sequential role passes and label self-review honestly.
Upstream .claude settings, event hooks and model pins apply only in Claude Code.
For explicit framework validation run python tools/ai/validate.py.
For the complete portable gate run `python tools/ai/guard.py --profile full
--scope all`; for a commit boundary use the fast profile. The optional Git
bridge is installed only when the user runs `python tools/ai/install-hooks.py
install`.

## State and evidence
Use production/studio/run.json for the in-session workflow plan. Resume from the
next verified unfinished step and maintain production/session-state/active.md.
No Claude or external AI CLI is needed. Skill completion is an internal handoff;
continue until the user's objective is complete or a material decision blocks it.
Do not mark done because a process exited zero: missing reports, unresolved
questions, failed tests and missing required gameplay evidence block completion.
Do not commit/publish or contact third parties without user authorization.

## Maintenance
ai/ and .agents/skills are generated; edit source or generator and regenerate.
Preserve LICENSE and UPSTREAM.md. Never blanket-update the original .claude/
files during framework upgrades. Read README.zh-CN.md for use and limitations.
