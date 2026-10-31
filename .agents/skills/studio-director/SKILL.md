---
name: studio-director
description: "Coordinate a complete Game Studios objective inside Codex from natural-language requests: inspect existing work, route planning/design/Godot/UI/balance/development/review workflows, and resume progress without asking the user to select individual skills. Use for creating, changing or continuing a game in this repository."
---

Read docs/ai/STUDIO-DIRECTOR.md and execute its director loop. This is the default
entry for game-production work; the other studio-* skills are internal tools.
Use ai/docs/workflow-catalog.yaml as the phase map and ai/skills/index.json as
the workflow inventory. Read only the relevant role and phase references.
Honor the user's bounded goal. Select and run next steps internally until that
goal is verified complete or a material blocker needs input. Do not turn skill
completion into a user handoff. Save/restore production/studio/run.json and the
upstream session checkpoint. Do not launch other AI tools or CLI sessions.

