# Codex adaptation: capability and verification boundary

The original .claude tree is retained, but the supported execution path here is
Codex inside this project. No cross-AI bridge is included in this revision.

| Capability | Codex behavior |
|---|---|
| Single natural-language entry | AGENTS.md -> studio director |
| Full production map | Original seven phases and minimal path, reused from catalog |
| Workflow selection | Codex chooses internally; user does not type each skill |
| Roles/workflows | 49 source roles, 74 source workflows + one Codex director |
| Progress | In-session ledger, next-step dispatch, evidence hashes, saved checkpoint |
| Reviews | Actual reviewer required; sequential passes explicitly self-review |
| Original 15 event hooks | Not registered as Codex hooks |
| Path rules | Explicit matching/reading from the adapted rules index |
| Model settings | Current Codex host settings; original Claude pins ignored |
| Long work | Continue during active turn; resume from disk after interruption |
| Game UI verification | Requires available game runtime/observation tools |

The upstream start skill explicitly hands commands to the user. The Codex
director intentionally replaces that handoff with internal continuation while
retaining onboarding, design decisions, documents and verification requirements.
This is an unofficial adaptation, not an upstream feature or endorsement.

Offline tests verify dispatch/state/evidence failure and recovery behavior.
Skill/frontmatter checks verify discovery format and reference integrity.
Neither proves that every model choice is correct or that a game is balanced.
A complete real game has not been built/played to validate all 74 workflows.

Official Codex discovery reference:
https://developers.openai.com/codex/skills/
Source attribution and license: UPSTREAM.md and LICENSE.

