# Agent event projection

The supplied Claude snapshot's `components/AgentProgressLine.tsx` separates
the Agent's label, latest tool/activity, tool count and resolved/error state.
Its transcript does not print the underlying task transport event for each
text delta. Grok Build's `xai-grok-pager/src/acp/tracker.rs` routes task/plumbing
tools separately from ordinary scrollback entries; its stable entry identity
allows progress to replace an existing entry. These were read as behavior
references. The implementation here is Sengoo and contains no copied TS/Rust
agent or renderer code.

`src/tui_agents.sg` consumes the existing bounded `{"agent": ...}` envelope.
The frontend owns `UiAgents`; session IDs and tool-call IDs are private keys.
One child session/Agent ID yields one summary card across model requests.
The request counter is a monotone watermark, and terminal states absorb late
updates. Text deltas update a sanitized bounded preview; they do not append
messages or reflow the entire transcript. Child tools update the same card,
with bounded call deduplication and readable paths/activity. Unparseable,
unknown and malformed envelopes never fall back to visible raw JSON.

`src/tests_tui_agents.sg` verifies 1000 deltas in a single card, readable model
and role metadata, no opaque transport IDs, parent-stream isolation, child-tool
deduplication, newer-request watermarks, Agent ID reuse across sessions,
cancellation, success proof, missing outcomes, unknown side effects and parent
completion. Canonical child `turn.tool_calls` and `tool_completed` events also
update the card without requiring outer host-tool events: child JSON-mode
controllers do not emit those outer events. It is a pure native projection
regression; it does not qualify
host routing or a real terminal by itself. The integration owner separately
checks the final host/TUI event route and final executable.

`tests/workbench_controls_fixture.py` exercises the public executable in an
owned hidden Windows console, a disposable project and an isolated catalog.
It uses a loopback provider, real child Agent execution and a real file read;
it checks bounded Agent display, editable draft, model/effort requests,
Shift+Tab policy cycling, current-request policy capture and approval focus.
It never contacts a paid service or accesses user API configuration. Its
baseline evidence must remain distinct from the new executable's evidence.

Run with the configured Sengoo standard library/runtime:

```text
sgc --runtime-mode source-development build src/tests_tui_agents.sg --force-rebuild -O 0 -o target/tests_tui_agents.exe
target/tests_tui_agents.exe
```
