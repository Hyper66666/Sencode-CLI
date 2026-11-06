# Design

## Responses continuation

`ProviderTurn` records bounded complete output items by output index. The
parser accepts `response.output_item.added`, `response.output_item.done` and
the completed response output as authoritative updates, while still parsing
function-call argument deltas. A completed assistant turn persists the opaque
output items separately from the normalized tool calls. The Responses
request builder emits those items, including assistant phase and encrypted
reasoning, before the function-call output entries on the next turn, preserving output order and
call identifiers. Missing or malformed items fail closed before a tool is
authorized; no automatic replay occurs after an unknown result.

Opaque output is scoped to the captured connection id, endpoint and model.
Switching any of these rebuilds the request from public text and normalized
tool history. Connection ids are non-secret; neither credentials nor their
hashes are persisted in the continuation metadata.

All stored item JSON is bounded, UTF-8/NUL checked and copied into the owned
document arena. The provider never executes fields from a reasoning item.
Fixtures cover a fragmented reasoning item, a reasoning item followed by a
function call, tool output continuation, restart, duplicate call IDs and
malformed item rejection.

## Shell selection

The model `run_command` tool uses a shell resolver on Windows for safe absolute
PATH entries and installed Git Bash locations. Bash is the default; explicit
`shell=powershell` and `shell=cmd` preserve native Windows workflows. An absent
Bash returns a clear diagnostic, never a silent switch to another syntax.
PowerShell is not the default model shell. Each invocation uses a no-profile,
non-interactive mode, the requested workspace as cwd, bounded stdout/stderr,
timeout and the existing process-tree termination/quiescence checks. The
result includes the selected shell family. Empty PATH
or missing Bash must still produce a deterministic diagnostic rather than
running a repository-local shadow executable.

The interactive `/terminal` command remains an explicit user choice and keeps
its existing PowerShell/CMD behavior. Shell selection is part of the validated
tool contract, so Plan and permission policies continue to gate execution.

## Composer cursor and status

The renderer tracks whether the terminal cursor is currently shown. A frame
update moves the cursor without repeatedly emitting hide/show controls; the
visibility escape is emitted only when focus state changes. This prevents each
16 ms repaint from resetting Windows Terminal's native blink timer. Unchanged
frames perform no terminal write. The terminal owns the normal blink cadence,
and exit always restores the terminal's original state.

The composer status row no longer renders the redundant thinking glyph or the
word `Thinking`. Queue, approval, cancellation, reading and error status stay
visible. Compaction phase events remain available to the transcript/event
consumer without reintroducing a second composer animation.

## Validation

The optional `ask_user.options` array contains two to six objects with a bounded
`label` and optional `description`. Host question events preserve these typed
options. The frontend consumes arrow keys and Enter in the question overlay;
a system-provided custom-answer entry switches to separate text input.
Cancellation uses an explicit `cancelled:true` reply, never an answer of `no`.
The host correlates the existing interaction nonce, pauses on cancellation and
never treats a question choice as tool authorization. Invalid options fail
normal tool validation. Legacy questions without options keep free-text input.

Pending insertions use the existing bounded FIFO queue and are displayed above
the composer in grey. Esc belongs to the focused overlay first. At composer
focus it retracts the newest pending entry without cancelling the active turn;
existing draft text must survive. Ctrl+C explicitly cancels the active turn.
Entries are only submitted when the prior turn is quiescent and queue policy
allows dispatch. The UI labels them pending and does not claim the current
provider request has received them. Retraction never repeats a completed tool.

## Original image references

Explicit image-path pastes and CF_HDROP snapshots retain canonical original
PNG/JPEG paths. The composer renders numbered blue chips and keeps a stable
mapping for the UI lifetime; queue, recall and stash retain the mapping. Cursor
movement snaps to chip boundaries. Backspace, Delete and word/Vim deletion
widen intersecting edits to the entire chip. Removing a chip never removes its
source image. At most eight images can be submitted and 128 references can be
created in one UI lifetime. There is no project attachments directory.

Only an explicit user image submission creates session image grants. Persisted
history stores path, MIME, byte length and SHA-256 rather than base64. Request
preflight requires the captured model's explicit visionSupported capability;
hydration reopens a bounded file snapshot and verifies its grant and byte
identity before creating transient protocol parts. Each image and the total
image bytes are limited to 8 MiB, dimensions to 8192 per edge and 16M pixels.
Missing, changed or ungranted files pause transmission. Restoring the original
bytes or starting a new session is necessary when old referenced content is
unavailable. Imported project histories and branches do not inherit grants.

Bitmap-only clipboard data has no source path. An explicit Ctrl+V/Alt+V saves
that data exclusively into a bounded system TEMP PNG, with a visible status.
The generic Sengoo terminal boundary owns OS clipboard snapshots and GDI+
conversion; Sengoo application code owns path recognition, labels and sending.
Alt+V remains available when the terminal intercepts Ctrl+V. Tests never inspect
or overwrite the user's interactive clipboard. Native boundary fixtures and
real provider-format loopback tests are recorded separately from live OS
clipboard integration, which is not qualified by a denied private station.

Streaming render changes follow the reference architecture's separation of
stable message blocks, growing tails, and scheduled redraws. Sengoo owns the
implementation; completed blocks may be cached while new deltas invalidate
only affected content. The renderer batches redundant work within one frame
without delaying provider data through artificial character playback. Draft
edits and cancel events take priority over periodic paints. A growing-answer
fixture verifies intermediate output, input latency and scroll retention.

Run native provider/executor/TUI checks first, then a loopback Responses tool
fixture, a real Git Bash command fixture, and the hidden Windows console
fixture. The final candidate must preserve existing CLI, management, project
history and installation evidence; no real provider endpoint or user project
is used by tests.
