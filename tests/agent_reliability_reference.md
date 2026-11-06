# Tool-loop reliability reference review

Read-only review of the locally supplied Claude Code snapshot and Grok Build.
These are implementation references; the acceptance fixture calls only the
Sencode binary, an owned native Windows console and a synthetic loopback API.

## Recoverable tool failures

Claude's `restored-src/src/services/tools/toolExecution.ts` catch at line 1589
formats the failure at 1691 and returns a `tool_result` with `is_error: true`
and the original `tool_use_id` at 1714–1725. The failure is data in the
conversation, so the model can choose a corrected next tool call.

`services/tools/StreamingToolExecutor.ts` lines 347–360 distinguish a tool error
result from executor interruption. The code explicitly lets independent read
and fetch operations survive another read's failure; Bash dependency failures
have a separate sibling-cancellation rule. `utils/toolErrors.ts` retains exit
code, stderr and stdout and bounds the formatted text to 10,000 characters.

For Sencode, adopt structured recoverable results for validation and known
read-only failures. Preserve its stronger existing pause rule for cancellation,
unknown write/process effects, execution ownership loss and explicit permission
denial. A result already durably complete is reused by identity; correcting
arguments requires a new call ID. Do not retry a possibly executed operation
implicitly.

## One stable card and chronological segments

Claude's `components/messages/AssistantToolUseMessage.tsx` lines 102–120 looks
up resolution and execution state by `param.id`; progress replaces the visual
state of the same tool use. `utils/messages.ts` `buildMessageLookups` records
results in `toolResultByToolUseID` at line 1241. A running notification and its
terminal result are not independent tool messages.

Grok's `crates/codegen/xai-grok-pager/src/acp/tracker.rs`:

- `handle_tool_call`, lines 1197–1198, finishes current thinking and clears
  `current_agent_msg` before inserting a tool entry, so later text starts a new
  chronological segment.
- `pending_tools` retains call identity and its original `entry_id`; on
  completion, lines 1461–1475 merge the update and call `replace_tool_block`
  plus `finish_running` on that same entry.
- `orphan_updates` holds an update that races ahead of its initial call,
  rather than creating an unrelated duplicate card.
- Headless `reducer/messages/mod.rs` stamps invocation order and buffers results
  so out-of-order completion cannot reorder the serialized tool sequence.

For Sencode, use request ID plus call ID as the UI identity, store text and
tools in one ordered view, seal an open text segment before a new tool, and
update the original tool card in place. A completion update must not terminate
an unrelated newer text segment. Replay should reconstruct the same identity
and order from persisted messages, without executing any tool.

## Independent acceptance

`agent_reliability_fixture.py` verifies:

1. A rejected out-of-workspace read becomes an error result, the same completed
   call ID is not re-executed with changed arguments, and a fresh corrected ID
   allows the model to finish.
2. Real Windows console cells show text → one completed tool card → text.
3. Restarting that session reconstructs the same card and chronology.
4. The same native UI recovers from a read error without terminating the turn.
5. Real read → exact patch → Bash test changes only fixture-owned files, followed
   by another user turn whose provider request retains the tool history.
6. Console mode restoration and fixture credential removal complete on exit.

Run with an explicit candidate:

```text
python tests/agent_reliability_fixture.py PATH_TO_SENCODE_EXE --evidence target/agent-reliability/candidate.json
```

The v5 baseline reproduced the read-error termination, duplicated cards and
reordered opening text. Its real read/patch/Bash/continue path passed. These
results are separate from the corrected candidate's acceptance evidence.
