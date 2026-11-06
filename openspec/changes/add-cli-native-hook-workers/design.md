## Baseline and references

Sencode HEAD `a468086401a0d19077b5cf0b6aea3ecff0f04c9a`; Sengoo HEAD
`d46b3f6cd8d6e770734f98edc57aa67cb931e26a`. Both have existing working-tree
changes. Evidence must also identify source/compiler/binary hashes and host.

The existing Rust Sencode hooks event/matcher/plugin-namespace separation and
the reconstructed Claude event architecture inform the behavior. No recovered
implementation is copied. Existing desktop hooks retain their own behavior;
native workers use a distinct versioned contract. Native does not import the
desktop command-string/shell fallback or failure-open semantics.

## Manifest and registry

`sencode-worker.json` schema 1 declares a kebab-case `id`, version, protocol
`sencode.native-worker/1`, language `sengoo`, relative single executable path,
SHA256, timeout 100..30000 ms, and exact tool-name lists under `before_tool` and
`after_tool`. No glob/regex, command string, environment interpolation, dynamic
arguments or executable extension inference is performed. IDs are at most 64
ASCII bytes. Only known built-in workspace tools may match. Coordinator tools,
Plan file writes and extension hooks themselves cannot match.

Reading a manifest is side-effect free. Explicit registration writes a disabled
record. Enabling records the reviewed manifest and executable fingerprints; a
changed byte invalidates trust and must not start a worker. Registration is
not a standing execution grant. Repo discovery, AGENTS/CLAUDE/SKILL content and
provider output cannot register, enable or approve workers. Duplicate IDs with
different source paths fail rather than shadowing one another. Inspection and
listing never spawn a child, fetch anything or compile source.

The operational `<shared-db>.extensions.sqlite3` sidecar has its own schema and
bounded registry/journal. Its creation uses a migration OS lock and rejects
unknown schema versions. Session history, lease/fence checks and shared tool
ledger remain authoritative. Registry paths and metadata are not credentials.

## Tool boundary and scheduling

Only the native engine uses this slice. Captured policy, connection, Goal
counters and the complete persisted assistant turn precede side effects.
Plan and inherited read-only children never launch executable workers, even
when a manifest calls the worker read-only. A matching mandatory before hook
therefore blocks with a precise Plan/interaction-required result; it is not
silently skipped. Workers do not grant access to a denied parent operation.

Each invocation binds the session, parent call ID, phase, worker ID, manifest
fingerprint, execution ID and fence. Its stable ID excludes retry counters and
is claimed durably before process creation. Existing unfinished or completed
claims never execute again. A hash change cannot turn the same parent tool call
into a fresh invocation. Unknown outcomes require inspection and a new user
request, never automatic retry.

Order: validate parent ToolSpec/policy -> fresh worker approval -> revalidate
fingerprints -> enqueue one cwd write permit -> OS workspace lock -> claim and
spawn -> poll/drain -> cleanup -> persist hook result -> release lock/permit.
The parent tool then obtains its own normal permission and FIFO ticket. A
before worker must never run inside a held parent write permit or try to
reacquire that permit. The process is considered effectful regardless of hook
metadata. Queue cancellation releases its ticket. No model slot is held for
worker execution and no model request is charged or hidden by a hook.

After hooks start only after the original tool outcome has been durably saved
and process cleanup is certain. They do not rewrite that outcome. A cancelled,
interrupted or cleanup-unknown tool must not launch an after worker. Hook
timeouts/protocol failures pause Goal and stop continuation; they do not reset
request/token budgets or silently run the original tool. A before `block`
records a truthful blocked result and names the source. A neutral `continue`
still requires ordinary host policy/approval for the parent operation.

## Approval contract

Trust review and execution approval are separate. Every launch uses the normal
nonce/request-bound interaction controller and presents worker ID, canonical
manifest/executable paths, hashes, phase, cwd, target tool and the bounded JSON
input that will be disclosed. It states that a native process has the user's
OS access and that no OS sandbox is provided. `auto-edit` and `allow-commands`
do not authorize hooks. No controller or a stale/prequeued approval denies the
launch. Enabling, startup, listing and resume never fabricate approval.

An executable must remain fingerprint-identical from approval through spawn.
Use the generic pinned process-image guard on Windows, holding a non-reparse
regular-file identity against replacement until cleanup. If the platform lacks
this primitive, execution stays unavailable; repeated pre-spawn hashing alone
does not close the replacement race. This is an integrity guarantee against
path replacement, not confinement from other code running as the same user.

## Wire contract

Protocol `sencode.native-worker/1` is UTF-8 JSONL, no BOM, maximum 262144 bytes
per frame, 524288 buffered bytes and 1048576 aggregate stdout bytes. Tool input
is at most 131072 bytes; oversized input fails before approval/spawn and is
never silently truncated for a security decision. Stderr is drained with a
65536-byte limit and is not copied raw into public events or provider context.
Initialization timeout is 2000 ms; the manifest overall timeout includes all
subsequent I/O. Only one invocation is in flight in a fresh owned process.

Host -> worker `initialize` includes `schema`, `protocol`, `id`, `worker_id`,
`manifest_sha256`. Worker -> host `ready` echoes all identity fields. Host ->
worker `hook` includes the same protocol/id binding, event (`before_tool` or
`after_tool`), session/execution/parent call IDs, cwd, known tool name and input
object; after includes the known result object. Worker -> host `result` echoes
the invocation ID and event, with `decision: continue|block`, bounded `reason`
and `notice`. `block` is valid only before a tool. Unknown frames, fields,
duplicates, invalid UTF-8, wrong IDs/phases/versions, extra output and malformed
JSON fail closed. Worker `host_call`, shell, MCP and model requests receive
explicit `unsupported`; the first slice executes none of them.

After accepting one result, close stdin, drain both streams and require exit 0
and certified tree quiescence. A valid result followed by a crash is failure.
Timeout/cancel/protocol failure closes stdin, terminates the owned tree, reaps
and verifies `tree_quiescent` before any terminal success. A process handle's
Drop remains a final cleanup defense, not evidence of successful quiescence.

## Events and frontend behavior

Events use existing engine envelope IDs and sanitized text. Hook detail carries
`invocation_id`, `worker_id`, `phase`, `parent_call_id`, `status`, bounded reason
and notice, and `cleanup_confirmed`. Statuses are `approval_required`, `queued`,
`running`, `continued`, `blocked`, `failed`, `cancelled`, `interrupted` and
`unsupported`. Persistence precedes terminal event publication. Worker output
is untrusted tool data, never a system/developer instruction or command. A
post-hook error keeps the original tool's outcome visible and stops automatic
continuation. Fullscreen/scrolling/headless share the execution rules; headless
without an interactive controller reports permission required with no launch.

Management entry points are list/inspect/add/enable/disable/remove under
`extensions`; `/hooks` lists subscriptions and `/plugin` projects the same
native registry. The root integration decides exact parser/UI route ownership.
These commands remain disabled until actual handlers and fixtures exist.

## Minimum fixture gates

See `fixture-matrix.md`. Fixtures use isolated databases, local compiled workers
and loopback providers only. No real credentials, user registry, repo hooks,
installed candidate or source tree are mutated. Captured protocol fixtures do
not establish live-service or clean-install acceptance.
