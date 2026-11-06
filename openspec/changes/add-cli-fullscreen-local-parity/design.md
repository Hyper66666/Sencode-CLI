## Baseline and provenance

Sencode HEAD: a468086401a0d19077b5cf0b6aea3ecff0f04c9a.
Sengoo HEAD: d46b3f6cd8d6e770734f98edc57aa67cb931e26a.
Both include pre-existing working-tree implementation. Record source hashes using
scripts/record-baseline.ps1; a HEAD alone does not identify this candidate.
Reconstructed Claude Code 2.1.88 informs architecture; public local parity is
frozen at 2.1.318. Reference presence is not proof of public availability.

## Process and event ownership

The frontend owns UiApp, focus, draft, viewport, candidate lists and cell frames.
The execution host owns provider requests, tools, policy, budgets and leases.
An initial owned stdio transport uses bounded JSONL frames, continuously drained
stdout/stderr and explicit shutdown. Durable attach requires the generic local
IPC transport and cannot be claimed from a piped foreground child.
The transport envelope is versioned. Request IDs, execution IDs and monotonically
sequenced events prevent stale/double completion. A complete turn is persisted
before side-effecting tools execute. Unknown tool results are not retried.

## Interaction contract

Fullscreen is the TTY default. Plain and headless modes do not emit screen
controls. Home uses a centered monochrome SENCODE mark, fixed composer and status.
Transcript scrolling never loses a draft; new deltas do not force a scrolled
viewport to the bottom. Completion Enter consumes the key and only fills the
selection. A later Enter submits. Approval requires input generated after that
approval is presented, tagged with its interaction identity.

## Runtime policy

API native uses Sengoo. Managed accounts use pinned official runtime protocols,
never private authentication endpoints. EffectivePolicy is checked rather than
trusting an adapter's no-op success. Unknown strict Plan/budget/edit enforcement
disables that strict mode with an explanation. Switching affects future turns.

## Persistence and failure

No uncoordinated desktop schema bump. Session mutations take the existing lease;
cross-process events are published only after commit. Tool cancellation is a
request until cleanup/quiescence is confirmed. A frontend disconnect pauses a
foreground Goal; explicitly backgrounded ordinary jobs have independent lifetime.
Never inspect real credentials or migrate user state in automated fixtures.

## Rendering and extensions

UiApp reducers consume data; only the renderer writes screen frames. Provider
and tool text is sanitized. Markdown stable blocks and growing tail are separate.
Extensions use Sengoo manifests and explicitly trusted compiled workers, not a
new JS runtime; host tool requests still pass through policy. Worker execution
must not be described as an OS sandbox.
