# Approved local native hook workers

Add an explicitly registered, hash-reviewed compiled Sengoo worker at the
native tool boundary. A before-tool worker may block an operation; it never
grants permission. An after-tool worker may report a notice after a known,
persisted and quiescent outcome. Every launch requires a fresh user approval.

## Capabilities

- Inspectable local JSON manifests, disabled registration and fingerprint-bound trust.
- Versioned bounded JSONL initialization, hook input and result contracts.
- Existing Plan, fresh approvals, canonical-directory FIFO, OS workspace lock,
  execution fence, durable no-replay ledger and owned-process cleanup.
- A minimal Sengoo worker example and isolated executable protocol fixtures.

## Non-Goals

No automatic silent shell, command-string execution, recovered JS/TS modules,
HTTP hooks, remote downloads, marketplaces, dynamic in-process libraries,
model/provider calls, arbitrary host-tool calls, lifecycle hooks on startup,
worker permission grants, unattended hook execution, complete plugin SDK or
OS sandbox. Project instructions and skills cannot enable executable code.

## Ownership and dependencies

This P4 child of `add-cli-fullscreen-local-parity` owns native hook contracts,
registry/journal/client modules, controller integration and isolated fixtures.
Root owns main/frontend/state/scripts and installed acceptance. Foundation owns
generic process image integrity and process-tree primitives. Shared schema 29
and storage contract 1 remain unchanged; extension operational metadata uses an
independent schema-1 sidecar and never grants shared execution authority.

CLI management and slash presentation are capability gated until root connects
real handlers and installed evidence. Completing this slice does not close P4,
all plugins, the SDK, remote MCP, search or memory.
