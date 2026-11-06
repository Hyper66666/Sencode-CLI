## Why

The current Sengoo CLI has a verified scrolling console candidate, but direct
stdout writes and blocking turn ownership prevent a fixed composer and responsive
command/picker interactions. The approved scope adds a fullscreen local coding
workbench and broad local capability parity while preserving Sencode routing and
shared execution authority.

## What Changes

- Separate the Sengoo TUI projection from the Sengoo execution host.
- Introduce a unified command registry, tool contract and negotiated capabilities.
- Deliver local capabilities in P0-P6 with explicit executable evidence.
- Keep API-native and managed-account engine coverage distinct.

## Capabilities

- New: cli-fullscreen-workbench, cli-engine-session-protocol.
- Follow-on child changes: workspace recovery/PTY/media/IDE; extension/MCP host;
  durable collaboration/workflows/background jobs; managed-account policy.
- Generic terminal and IPC requirements belong to the sibling Sengoo change.

## Non-Goals

Cloud execution, mobile handoff, voice, browser/computer control, and direct
execution of Claude JS/TS Mods are excluded. Foreground Goals pause on exit.
No new public package registry is required.

## Impact

Sengoo owns UI and agent logic; native bridges provide generic OS capabilities.
SQLite, desktop fencing, OS credential stores, captured connections and existing
headless schema v1 remain authoritative. Existing working-tree changes remain.
