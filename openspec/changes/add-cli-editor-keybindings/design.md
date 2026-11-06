## Boundaries and lifecycle

`tui_keys.sg` owns keymap parsing, safe composer operations, grapheme-aware Vim
state and a bounded undo ring. `UiApp` owns one instance; no native singleton or
provider state is introduced. The fullscreen command registry alone enables
`/keys` and `/read`. Generic and scrolling hosts keep them disabled.

The default mode retains existing terminal keys. Explicit Vim starts in INSERT;
Escape enters NORMAL. NORMAL supports h/j/k/l, w/b, 0/$, gg/G, i/a/I/A, x/D,
dd/dw/cw and u. It deliberately omits macros, repeat counts, registers, search
commands, ex commands and dot repeat. Pasted events are text and enter INSERT;
they are never interpreted as normal-mode commands. Ctrl+C remains the explicit
running-request cancellation key and is shown while Vim is enabled. Enter still
passes through menu completion and explicit send/save handling.

Modal priority is approval, picker, queue-editor discard/cancel, explicit host
cancel/EOF, reading mode, then composer. Reading cannot be entered from a queue
editor; queue editing keeps its original Escape-to-discard behavior.
Keymaps never apply inside approvals or pickers. Undo state resets on session
clear, submission, history replacement and queued editor transitions, preventing
an edit from restoring another draft or an already-submitted task.

## User configuration

The explicit `SENCODE_KEYMAP` path takes precedence. Otherwise the UI reads
`%APPDATA%/Sencode/cli-keybindings.json` when present. The UI never writes it or
looks for project-controlled keymaps. A fixed 65537-byte read detects growth past
the 64 KiB limit; strict UTF-8 and NUL checks precede JSON parsing. A schema-v1
object accepts only `version`, `mode` and `bindings`, with at most 64 bindings.

Bindings use whitelisted modifier-letter or navigation chords and composer-only
actions. Reserved Enter/Tab/Escape/cancel/EOF/redraw/queue/paste keys and actions
such as submit, approve, shell or permissions are rejected. Unknown fields,
duplicates (including escaped JSON member names), invalid suffixes and
unsupported versions reject the entire file. A schema-specific Sengoo scanner
checks property tokens before the general JSON DOM's last-member-wins behavior;
the JSON parser remains responsible for syntax and escape decoding. Rejection
keeps the built-in default map with a bounded diagnostic. Raw file contents
are not printed. Effective help shows only source and validated operations.

`/keys default|vim` changes the current UI session. `/keys reset` clears custom
bindings and returns to built-ins in memory, without modifying the user file.
`/keys show` explains the schema and effective safe bindings.

## Reading mode

`/read` focuses cached transcript navigation; j/k, PageUp/PageDown, gg/G and arrow
keys change only the scroll anchor. New model output continues and preserves the
anchor. Escape or q returns to the original composer and cursor. Reading never
submits, cancels or approves a task, and pauses automatic queue draining until
focus returns. Approval still takes priority when the host asks for a decision.

### Stable reading position during reflow

The Grok Build reference at
`2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8` separates presenter scheduling,
composer/overlay input ownership and scrollback follow/entry anchoring
(`app/event_loop.rs`, `app/agent_view/input.rs`,
`scrollback/state/selection.rs`). The focused local adaptation is an original
Sengoo reflow anchor, without changing the chosen fullscreen/monochrome layout
or importing its UI implementation.

Before rebuilding wrapped rows, the UI records the stable identity of the
lower visible message, its row within that message and whether that row was
the message end. After reflow it resolves that identity, retaining the end
when applicable or clamping the row to the message's new extent. A user already
following the tail stays at the tail; a reader is not silently put into follow
mode when a live tail shrinks. An evicted message uses a bounded remaining
offset. Starting a new stream accounts for its header before appending deltas,
so an earlier reading entry does not move on the first token. This preserves
the message being read; it does not promise a byte-identical wrapped fragment
inside a long paragraph at a different width. The composer, policy, task
queue and provider state are unchanged by reflow.

The native `tests_tui.sg` suite exercises completed entry/end anchors, a new
stream header and following the tail. The actual Windows console driver
`tests_tui_resize_console.sg` renders synthetic history and a timed stream;
`tests/tui_resize_console_fixture.py` resizes its owned hidden conhost window at
80, 120, 160 and 80 columns and reads the real alternate-buffer cells. Five
checks passed, including preserved entry/draft/focus, explicit focus return,
stream cancellation, double-Enter exit and restored console modes, recorded in
`target/worktree-tui/resize-console-evidence.json`. This is rendering evidence,
independent of production/provider and final installed-candidate checks.

## Limits and evidence

The undo ring retains at most 32 entries and 1 MiB, under the existing 64 KiB
draft bound. All edits reuse Unicode 17 grapheme boundaries. Unit tests cover
parsing, atomic rejection, reserved keys, Unicode, paste, undo and focus. Actual
Windows console tests separately cover explicit entry, visible state, draft
restoration and cancellation. Pure frame cost and four-stream visible latency
remain distinct measurements; an unrun integration gate stays unchecked.
