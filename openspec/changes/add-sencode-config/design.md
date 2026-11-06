# Boundaries

React uses generated tauri-specta commands. Tauri validates typed input and
launches a pinned app-local Sengoo bridge directly, with JSON over stdin/stdout,
bounded output and a timeout. No shell, listening server or secret in argv.
The bridge validates inputs again and serializes mutations using the CLI's
existing OS locks. Existing API edits retain unrelated config fields and model
capabilities; new model IDs begin with no asserted vision capability.

Secrets go from the password field through IPC and a pipe to Credential Manager.
List/export never exposes them; secret errors are represented by fixed messages.
Edit with an empty key preserves its current credential. Accounts are read-only
apart from choosing them. Duplicate IDs on creation fail rather than overwrite.

The native app uses the same default catalog as `sen`; a process environment
override exists for isolated tests. It never mutates project conversation
history. Refresh on focus/poll reflects changes made by another client. Pending
form drafts are independent of refreshed snapshots. Mutations are serialized
and only commit UI state after bridge success; failures preserve the form.

Model configuration uses the desktop's `enabledModels`, `discoveredModelIds`,
`selectedModelId` and per-model `capabilities.visionSupported`. Discovery is an
explicit, non-mutating GET `/models`: Bearer auth for Chat Completions/Responses,
and x-api-key plus anthropic-version for Messages. A blank key can use an existing
custom API credential. Redirects are not followed; bodies are bounded to 1 MiB,
model ids to 256, with connect/idle/overall deadlines. The form separates
candidates, enabled models and default; probing never changes enablement or
capabilities. Manual model entry remains available for providers without discovery.
At least one enabled model is required, and the default must be enabled. Editing
preserves unknown existing per-model fields. Import/export allowlist model
metadata and never include credential references.

The browser-only `?preview` is an explicitly labelled, in-memory visual fixture.
It does not impersonate a configured installation and never saves API keys.
Imports open a reviewed single-profile editor and require explicit Save. Export
contains metadata for one API profile and excludes credentials.
