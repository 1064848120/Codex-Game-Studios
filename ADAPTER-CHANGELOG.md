# Codex adaptation changelog

## 0.1.0 — 2026-11-01

- Adapt the upstream 49 role briefs, 74 workflows and 14 rules for Codex.
- Add a default director for natural-language goals and internal continuation.
- Add checkpoint/resume, acceptance receipts and changed-evidence detection.
- Preserve upstream source, Git history, copyright and MIT license.
- Provide 24 offline tests, structural validation and a Windows/Linux CI matrix.
- Add Chinese/English introductions, contribution guidance and public attribution.

This first public version validates framework state and structure. Full model
behavior and complete game production across engines remain unverified.

The original CHANGELOG.md records upstream releases, not adaptation versions.

## 0.2.0 — 2026-11-02

- Add a Codex-side event dispatcher for the upstream SessionStart, PreToolUse,
  PostToolUse, PreCompact, Stop, Subagent and notification responsibilities.
- Add the portable guard for generated-layer drift, catalogs, data JSON,
  secrets, workflow state, gaps, tests and optional Godot import checks.
- Add opt-in Git pre-commit and pre-push gates using the same guard logic.
- Add a parity audit covering all 18 upstream hook files and all 75 Codex skill
  wrappers.
- Add `tools/ai/studio.py` as one portable maintenance entry point for audits,
  gates, events, skill discovery and workflow status.
- Add four regression tests; the adapter suite now has 32 passing tests.
- Update the English, Chinese and Codex usage documentation with the new
  parity boundary and diagnostics commands.

The project-level behavior is now available without Claude Code. Claude's
private event transport, permission prompt UI, notification UI and model
runtime remain host-specific and are documented as such; they are not claimed
to be reproduced by the adapter.
