# Codex Game Studios

**A structured game-development workflow inside Codex, from an idea to verified implementation.**

[中文](README.md) · [Usage guide](README.zh-CN.md) · [Compatibility](docs/ai/COMPATIBILITY.md) · [Contributing](CONTRIBUTING.md)

An unofficial MIT-licensed adaptation of
[Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios).

Describe your objective in ordinary language. The studio director examines the
project, selects relevant roles and workflows, and continues internally within
the authorized scope. You do not need to invoke every skill or install Claude Code.

## What it does

- Helps explore ideas, intended players, genre, platform, scope and engine options.
- Connects systems design, economy/balance, UI/UX, architecture and production.
- Reuses existing design and code instead of restarting onboarding every time.
- Retains 49 role briefs, 74 upstream workflows and 14 rule groups.
- Adds one Codex director skill and a resumable local workflow ledger.
- Tracks acceptance evidence, blocks failed steps and detects changed evidence.

The upstream seven-stage production map is retained: concept, systems design,
technical setup, pre-production, production, polish and release preparation.
Minimal, design-only, review-only and targeted repair objectives remain scoped.

## Start with Codex

1. Use this repository as a template for your own project.
2. Open its root folder in Codex, where AGENTS.md lives.
3. Describe what you want. For example:

> I want to build a small survival-defense game in Godot, but the idea is vague.
> Guide me through the studio workflow: identify the audience, core loop and
> feasible scope, then plan systems, economy, UI and architecture before building.
> Ask me when a meaningful creative decision needs my input.

For existing work, provide your design documents and code and ask the director to
inspect gaps and continue. Say "continue" after an interruption to resume from
recorded progress. Skills are internal tools rather than a user-operated menu.

Requirements: Codex with project/file/tool access, Python 3.10+, Git, and Bash
when using retained upstream shell helpers. Install the chosen engine for actual
game development. Framework scripts use only the Python standard library.
No additional Claude account or model API key is required by the framework.

Godot, Unity and Unreal documentation is retained. This adaptation has not been
end-to-end tested with all three engines.

## Verification and limitations

Local checks pass: 28 offline tests, 75 skill-format checks and 105 phase-reference
checks, including validation after extracting the distribution archive.
The repository includes local commands for checking the exporter, catalogs,
references and offline tests.

These checks validate workflow/state behavior, not a finished game's quality.
Natural-language routing and all 74 workflows have not been fully exercised
through a complete game production. See docs/ai/VALIDATION.md.

- 49 roles are briefs, not 49 automatically running agents.
- The project-level responsibilities of all 15 Claude event hooks are exposed
  through `tools/ai/hooks.py`, `tools/ai/guard.py` and optional `.githooks/`.
  Codex's private event transport and notification UI remain host-owned; see
  `docs/ai/HOOK-PARITY.md` for the complete mapping.
- Sequential role passes are self-review, not independent review.
- Continuation happens during an active Codex task, not an always-on daemon.
- Missing runtime or visual tools must be reported as unverified, never passed.
- Balancing, assets and fun still need actual implementation and playtesting.

## Maintain and contribute

~~~bash
python tools/ai/export-universal.py --check
python tools/ai/validate.py
python -m unittest discover -s tests/adapter -v
~~~

The .claude source tree is retained. Generated ai/ files and workflow wrappers
have reproducible hashes and edit protection. The studio-director skill is
maintained separately. Review upstream updates before regenerating.

See CONTRIBUTING.md, UPSTREAM.md and docs/ai/STUDIO-DIRECTOR.md.
MIT License. Original copyright belongs to Donchitos; the adaptation retains
that notice. This project is not officially affiliated with OpenAI, Anthropic,
or the upstream author.
