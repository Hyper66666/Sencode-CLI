# Grok Build design review

Reviewed the user's local Apache2.0 reference at `D:/sencode/grok-build`, revision
`2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8`, origin
<https://github.com/xai-org/grok-build>. This is a source review, not a measured
performance comparison or a claim about community rankings. No private service
endpoint, telemetry or authentication behavior was reproduced.

| Source | Useful design | Application in Sencode |
| --- | --- | --- |
| `crates/codegen/xai-grok-pager/src/app/event_loop.rs` | Bounded ACP drain stops as soon as input arrives; cancel remains high priority | Keep each job poll bounded and preserve streaming/input latency fixtures; do not drain a token flood before handling keys |
| Same file, `Presenter` | Coalesce redraws; wait for writer acknowledgements; record progress rather than treating a slow terminal as a new frame sink | Cell differences already reduce output; an acknowledged bounded writer remains a separate gap for frozen/slow terminals |
| Same file, startup typeahead | Preserve genuine typed drafts, filter terminal noise, keep startup keys out of trust dialogs | Preserve drafts and the fresh-input approval barrier; never replay startup input into an approval |
| `crates/codegen/xai-grok-pager/src/scrollback/render.rs` | Cached entry heights/wrapped rows and viewport-only rendering | Preserve stable message identity when width changes; regress at80/120/160columns |
| `crates/codegen/xai-grok-pager/src/app/agent_view/input.rs` | One focus-ownership predicate controls external editing and close-key routing | Keep modal/menu/pane/input precedence; one event has one consumer |
| `crates/codegen/xai-prompt-queue/src/types.rs` | Stable queue IDs, optimistic edit versions, immutable origin and most-recent editor | Existing editable pending queue keeps IDs; cross-client queue editing needs an explicit versioned contract before sharing |
| `crates/common/xai-tool-runtime/src/render.rs` | Structured outcomes and model-facing content are distinct | Tool cards show bounded summaries while the Agent receives its contracted tool result |
| `crates/codegen/xai-grok-hooks` | Decision, process health, identity and cleanup are distinct | Native worker results distinguish blocked, failed and cleanup-unknown; uncertain cleanup pauses recovery |

The immediate implemented borrowing of an idea is the scrollback resize anchor:
reflow follows the previously visible message instead of reusing a row number
whose meaning changed at another width. Black/white styling, centered composition
and explicit two-Enter completion remain Sencode product choices.

The reference's Rust/Tokio/ratatui implementation is not a dependency of the
Sengoo UI. API and scheduler logic remain Sengoo; any future queued terminal
writer belongs to a generic bounded runtime I/O boundary. Do not adopt the
reference hook error policy blindly: native worker failures pause rather than
silently permitting a parent operation, and hooks cannot rewrite persisted tool
outcomes. Live interoperability and cold-install evidence remain separate.
