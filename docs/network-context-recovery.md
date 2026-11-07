# Requests and long sessions

Native API defaults are256K context (262144 tokens),128K maximum output
(131072 tokens), and automatic compaction at80% of the local token estimate.
The estimate includes serialized history, tool schemas and per-message framing;
it is not provider-reported usage or an exact tokenizer. A655360-byte safety
trigger or850-message pressure can compact sooner. Compaction preserves the
public transcript, complete tool pairs, recent task and cumulative budgets.

`/context` shows effective limits and their source. Existing
`.sencode/context.json` schema1 settings and exact connection/model overrides
take precedence. `max_output_tokens` is an optional positive integer override.
The three protocols send max_completion_tokens, max_output_tokens and
max_tokens respectively. Actual output allowance is bounded by estimated
remaining context, including32 tokens of framing margin. The selected model
and service must support the configured limits; unsupported limits are shown
as provider failures rather than silently switching models/providers.

Rich model history now uses explicit Sengoo byte/node budgets through loading,
checkpoint restore, compaction and request encoding. The former4096-node
failure could occur with fewer than300 messages even below the context byte
ceiling. Canonical history retains1000-message/786432-byte/32768-node admission;
resource failures pause with history intact. Public/UI window limits remain.

The initial request can be followed by at most five retries for every native
model request error: HTTP 4xx/5xx, TLS/network failures, HTTP 200 truncation,
invalid SSE/JSON and provider failures reported inside a successful HTTP stream.
This applies to the main controller, child agents and consultation. TLS checks
stay enabled and provider/model snapshots stay fixed. User cancellation and
existing request/token budgets can stop the sequence sooner.

Backoff is250/500/1000/2000/4000ms; valid Retry-After may increase a wait to a
maximum of300 seconds. Invalid headers use the ordinary backoff. All waits are
cancelable and release model slots. Each attempt consumes the existing budget.
The old30-second aggregate cutoff and stream-progress exclusion were replaced
under explicit user direction on2026-11-07.

Failed attempts remain provisional: their partial response is replaced before
retry, while completed tool calls/results stay in history and are never rerun.
If all retries fail or the user cancels, the last partial response is retained.
Unknown tool outcomes, state-storage failures and lost execution authority still
pause; retrying a model request is not permission to replay a shell command.

One transient `正在重连中... N/5 · HTTP 502 Bad Gateway` row appears above
Working, then clears on successful request, cancellation or failure. It does
not add retry notices to chat history. Final diagnostics preserve the HTTP
status as secondary context for2xx, actual TLS/network/protocol phase, attempts and stop reason. A successful HTTP200 does not guarantee a complete SSE/provider response. Sanitized phase/category fields are persisted with the bounded256-attempt journal. They exclude URLs,
headers, credentials and server response bodies.

Output parameter reference: official OpenAI API documentation for
[Responses](https://developers.openai.com/api/reference/resources/responses/methods/create)
and [Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create).
Both token caps include reasoning tokens. Providers may impose lower limits.
Inline image Base64 is excluded from the text-token estimate; the adapter
reserves4096 estimated input tokens per image and retains separate wire-byte
limits. This image estimate is also local and is not a model-specific tokenizer.
Responses requests below its16-token minimum are refused locally.

Tests use disposable databases, local HTTP/TLS fixtures and synthetic histories.
Successful fixtures do not prove that a user's external API is reachable.
