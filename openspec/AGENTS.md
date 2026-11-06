# Sencode OpenSpec workflow

Read config.yaml before a cross-layer change. This project uses spec-driven
changes with proposal.md, design.md, tasks.md and capability specs. Requirements
use `### Requirement:` and `#### Scenario:` with WHEN/THEN assertions.

Keep one owner per requirement. An umbrella records dependencies and integration
gates rather than duplicating child implementation requirements. The approved
implementation plan authorizes corresponding edits; mark a task complete only
after its implementation and named checks pass. Record full SHAs and hosts for
evidence. Preserve existing product behavior, data and upstream notices.

Run OpenSpec validation from windows/. Protocol fixtures and state machines
precede broad UI work. Never count an unrun platform, mock or workflow definition
as a successful live or installation check.
