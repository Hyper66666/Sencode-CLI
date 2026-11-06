## Why

The fullscreen parity umbrella leaves images/PDF open. Current CLI Provider
requests flatten user content to text, while desktop already retains ordered
image blocks and durable asset references. A local capture and shared-history
contract is needed before a UI affordance can truthfully promise media support.

## What Changes

- Draft explicit local capture, bounded metadata, session-scoped assets and
  restart semantics with a Sengoo foundation dependency.
- Specify capability-aware ordered image encoding for the three API protocols.
- Preserve desktop attachment compatibility and fenced public-history writes.
- Keep PDF engine/native submission and full multimodal acceptance as named
  open gates rather than counting header detection as their completion.

## Capabilities

- New proposal: `cli-local-attachments`, application integration owner.
- Dependency: Sengoo `add-bounded-file-media-inspection` for regular-file bytes
  and generic PNG/JPEG/PDF header facts.
- Related: `add-cli-fullscreen-local-parity`, existing shared-store fencing,
  desktop image assets and per-engine capability negotiation.

## Non-Goals

This draft adds no source implementation. It does not download dependencies,
install a PDF engine, inspect the real clipboard, fetch remote media, provide
OCR or terminal image protocols, or claim managed-account media parity.

## Impact

Asset/state/Provider/TUI boundaries and proposed fixtures are documented in
`sencode-cli/docs/local-attachments-design.md`. CLI JSON/SQLite/agent ownership
stays in Sengoo. Native code exposes only generic OS operations. Shared schema
or asset-loader changes require compatibility/version gates and desktop tests;
existing `attachments_json` is not an undocumented CLI extension point.
