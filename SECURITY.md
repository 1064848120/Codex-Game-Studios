# Security policy

This framework supplies instructions and local scripts that an AI coding tool
may use. Review downloaded instructions and scripts before running them.

## Report privately

Use this repository's [private vulnerability reporting](https://github.com/1064848120/Codex-Game-Studios/security/advisories/new)
for a concrete security issue. If private reporting is unavailable, open an issue
requesting a private contact without exploit details or secrets.
Do not post credentials, tokens, private game files or unredacted account logs.

This is a community project; there is no guaranteed response-time SLA.
This repository's maintainer is responsible for its adaptation, not the upstream
author or the vendors whose tools may execute the workflows.

## In scope

- Scripts writing outside the intended project or silently leaking data.
- Undisclosed external execution or permission bypass.
- Instructions that misrepresent authorization or fabricate verification.
- Unsafe handling of project paths or state files.

Framework instructions are not an OS sandbox. Host permissions remain authoritative.
Bugs in Codex itself should be reported through OpenAI's official channels.
