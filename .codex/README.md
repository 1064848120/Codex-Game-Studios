# Codex-only studio
Open this repository as the Codex project and describe the game objective.
AGENTS.md automatically routes production work to docs/ai/STUDIO-DIRECTOR.md.
Codex selects the roles/workflows and continues internally; users never need
to type each studio-* skill. The skills are implementation tools, not the UI.

No Claude Code installation, multi-AI CLI bridge or API key setup is needed.
Native subagents are optional when permitted; sequential passes are self-review.
See README.zh-CN.md for normal use and docs/ai/COMPATIBILITY.md for exact limits.

For adapter diagnostics only, `python tools/ai/studio.py audit --json` checks
the upstream hook inventory and Codex wrapper coverage. `studio.py skills`
lists the internal workflows; users normally do not need to invoke them.

