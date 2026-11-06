# Read-only CLI configuration and instruction views

## Why
The fullscreen menu advertises diagnostics and configuration inspection but had
no executable host implementation. Users need effective settings and sources
without exposing raw connection secrets.

## Capabilities
Root owns fullscreen `/config`, `/doctor` and `/memory` projection. Reuse the
same doctor builder for the existing headless `doctor` command.

## Non-Goals
No configuration edits, learned-memory writes, network probe, auth file reads,
classifier enabling or broad desktop/extension config introspection.
