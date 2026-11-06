# Architecture and contracts

Source lives under windows/sencode-cli. A single Sengoo coordinator owns typed
application state. Provider, agent, workspace, state, terminal and MCP logic are
Sengoo. Network workers copy bounded bytes and never parse provider events.

Each request captures connection+model; switching affects future requests.
Stable execution/tool/event identifiers prevent replaying side effects.
Global model concurrency defaults to four, per connection to two; children have
one level and may only narrow permission. Write-capable work is queued by
canonical working directory; parents release slots while waiting for children.

Shared store v1 uses the existing SQLite schema plus an additive migration,
cross-process OS locks, owner instance/execution ids and monotonic fences.
Opening a second client does not trigger global recovery. Recovery requires
the released OS lock and proof that tools from the previous execution exited;
timeout alone never authorizes takeover. Anonymous runtime Job Objects currently
cannot provide a cross-process cleanup certificate. Such incomplete executions
retain `cleanup_required` and reject takeover; safe automated cleanup remains a
delivery gate. A model-only CLI turn without a pending tool can recover. Shared
mutations append a durable changelog in the same transaction. Native provider
bindings are engine-scoped. Non-executing clients observe only; handoff is idle.
Secrets remain in Windows Credential Manager under existing connection targets.
Connection edits are serialized. Initial migration is backed up and increases
the schema version so old clients refuse writes. Closing older desktop processes
is an upgrade precondition; automated old-desktop admission exclusion remains
unverified. The CLI rejects an uncoordinated schema 28 database.

Every desktop acceptance path, including edit/resend and shared/managed ACP
fallbacks, claims that lease. The accepted user message retains its fence and
authorizes dispatch, binding persistence, fallback error insertion and terminal
commit. A missing assistant placeholder never authorizes a new insertion by
itself. Legacy state setters are restricted to sessions which have no shared
execution record. Fenced finalization validates and commits before releasing its
lease in the same actor operation, so delayed callbacks from the same instance
cannot release the next turn's lock.

Plan permits builtin read/search/clarification and readonly children; only its
exact plan artifact is writable. Shell and MCP are denied recursively in Plan.
Approving a plan restores execution authority explicitly. Goal is orthogonal:
default 50 model requests, optional token budget, all child/consultation/verify
usage included, no-progress pause after two identical failures, infrastructure
verification failure pauses. Restart and foreground exit never auto-resume.

Permissions require review for edits, commands and MCP by default; explicit
workspace auto-edit/command grants may narrow interactions. Repo instructions,
skills, provider/tool content and MCP annotations cannot grant capabilities.
Renderer escapes terminal control sequences from untrusted content.

Shared v1 supports the same Windows user/logon and local disk. Meeting/Fusion
active tasks are observation-only. CLI previews are sencode-sg.exe. No private
provider endpoint or recovered proprietary source is used.

The terminal follow-up retains normal console scrollback. Sengoo renders a
compact header, tool/assistant sections, a bounded multiline composer and
contextual mode/model hints. Only renderer-owned sequences control the terminal;
model, path, connection and tool text is sanitized first. Redirected and
structured output bypass decorative rendering. Consultation and MCP use the
same bounded queued-input contract as model and command waits; approval readers
read fresh terminal input and never consume that queue. User-level owned command
forwarders complement PATH updates for existing shells and never replace
unrelated executables or scripts.
