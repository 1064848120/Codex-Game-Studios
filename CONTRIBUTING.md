# Contributing to Codex Game Studios

Thank you for helping make structured game production usable inside Codex.
This repository is an unofficial adaptation; report adaptation issues here,
not to the original author unless the problem is independently reproduced there.

## Useful contributions

- Reproducible workflow bugs: routing, handoffs, interrupted work and gate checks.
- Real examples of Codex using the framework, with permission to share artifacts.
- Godot, Unity or Unreal validation evidence, clearly identifying tested versions.
- Improvements to design, economy, UI/UX and verification guidance.
- Documentation, localization and accessibility fixes.

Do not submit private games, credentials, account logs or large generated assets.
The repository contains the framework, not every game made with it.

## Where to edit

- Default coordination: AGENTS.md and docs/ai/STUDIO-DIRECTOR.md.
- Native director skill: .agents/skills/studio-director/SKILL.md.
- Source role/workflow content: .claude/ (preserved upstream baseline; keep changes
  focused and note divergence).
- Conversion logic: tools/ai/export-universal.py.
- State transitions and evidence tracking: tools/ai/workflow.py.
- Generated ai/ and the other 74 .agents/skills entries: regenerate, do not
  hand-edit. The generator refuses to overwrite locally edited generated files.

Keep the original LICENSE and upstream attribution. Do not pin paid models,
require another AI product, or reintroduce a per-skill manual user workflow.

## Before submitting

~~~bash
python tools/ai/export-universal.py
python tools/ai/validate.py
python -m unittest discover -s tests/adapter -v
git diff --check
~~~

For changes to instructions, test realistic requests when possible and report
what was actually observed. A synthetic state test is not evidence that the
model made the right creative decisions or that a game was played.
Preserve user scope, existing authorization and meaningful decision points.

Open pull requests against this repository. Explain the problem, changed
behavior, tests and limitations. Include no secrets or identifying local paths.
