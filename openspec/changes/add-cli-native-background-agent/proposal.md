# Explicit native Agent jobs

The native CLI currently owns its engine through foreground pipes, so closing
the terminal cancels the turn. This change adds an explicit bounded background
Agent job with authenticated same-logon attach, durable cursor logs and stop.
The supervisor reuses the existing native engine and never replays accepted
requests, uncertain tools or pending approvals after a disconnect or crash.

## Capabilities

- An explicitly started native Agent can continue after the launching terminal exits.
- One control client and read-only observers attach through Sengoo local IPC.
- Separate operational job metadata and bounded event logs remain inspectable.
- Goal control loss and approval loss cancel and pause instead of continuing.

## Non-Goals

No background Goal, daemon/service, reboot startup, automatic host restart,
managed account background execution, durable child rescheduling, shared-schema
migration, arbitrary PID termination, remote IPC or permission expansion.

## Ownership and dependencies

Core owns job contract/store/host/client/probe modules and isolated fixtures.
The integration owner owns main/frontend entry points and installed acceptance.
Foundation owns generic explicit detached process launch and creation-identity
queries. Existing shared session/workspace OS locks, execution IDs, fencing,
tool ledger and native submit admission remain execution authority. This child
extends add-cli-fullscreen-local-parity without duplicating its UI requirements.
