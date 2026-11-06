# CLI provider list, conversation origin and bundled search

## Capabilities
Start conversations below the workbench header, show every saved supplier and
its configured enabled models in one grouped list, color the effective permission
label, and make ripgrep available to command subprocesses in installed builds.

## Non-Goals
No automatic network requests or credential reads to enumerate models, no silent
provider fallback, no change to active-turn targets, no global PATH modification
for ripgrep and no session/schema migration. Discovery-only models remain opt-in.

## Boundaries
Presentation, catalog selection and child environment logic are Sengoo. Packaging
ships the pinned official ripgrep Windows binary and its upstream licenses.
The shared desktop/config database remains authoritative; each request captures
one connection, model, effort and permission tuple.
