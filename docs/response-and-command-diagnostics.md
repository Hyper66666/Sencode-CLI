# Response and command diagnostics

HTTP200 only confirms that the server accepted the HTTP exchange. The response
body can still be truncated, contain invalid SSE/JSON, report a provider error,
hit its output limit or omit its completion event. The CLI shows the actual
failure first, for example:

`Invalid or incomplete provider response (HTTP 200 received); HTTP response body ended before completion; retries 5/5.`

Failure metadata uses closed stages and categories. Raw server error bodies,
URLs, headers and credentials never enter diagnostics. Historical code10 alone
cannot prove which of these conditions occurred before this instrumentation.

Native model requests permit five retries, including failed partial responses.
The retry event has additive `replace_partial:true`; stream-json clients should
replace only provisional text from the failed model attempt. Completed tool
results are never repeated by the retry loop. Cancellation is immediate, and
request/token budgets still apply. Managed runtimes retain their own policy.

Command exit codes remain the executable's result. `git config --get` exits1
when the setting is absent; `rg` exits1 for no matches. Neither means that the
CLI execution transport failed. Test failures retain their complete stdout and
stderr for the model to inspect; ordinary command failure returns to the model
for correction rather than aborting the agent. Commands are never automatically
rerun just because network requests retry.

An additional execution defect was reproduced independently: Windows cmd.exe
can reject a forward-slash executable path before interpreting the command.
Sengoo now normalizes only Windows program paths and preserves the explicitly
selected cmd command tail's inner quotes. Other program arguments stay exact.

On Windows, built-in writes/patches to .bat/.cmd normalize LF/mixed newlines to
CRLF and remove UTF-8 BOM. Expected-content checks still compare the original
file exactly. The edit preview reflects the normalized output. Other file types
remain unchanged. Use explicit shell=cmd for batch files and noninteractive
checks instead of launching games or pause prompts in unattended tests.

The reported screenshots were inspected against saved command results: Git
identity queries returned1 with empty output; one launcher test genuinely failed;
start.bat produced command-fragment parse errors and hit its8-second timeout.
A later model command converted the batch newlines to CRLF. No user project or
Git identity was modified by this diagnostic investigation.

The new full retry fixture also exposed a Sengoo compiler ownership defect:
unwrapping a named Result<JsonDoc, i64> with `?` left the source wrapper's Drop
active and closed a successfully returned response. The compiler now consumes
that owning operand before branching. The CLI candidate is rebuilt with this
fix; an independent native Result/Option handle-liveness regression accompanies
it in Sengoo. No retry is used to hide a state-commit or ownership failure.

Valid completion events can include thousands of cumulative usage entries.
The CLI uses Sengoo's explicit 1 MiB / 65536-node event budget instead of the
legacy 4096-node default. A 4129-node live completion reproduced the legacy
failure; removing only optional attribution let the old parser succeed. This
was a local capacity defect, not invalid tool arguments or an HTTP failure.
The historical coarse diagnostic alone cannot prove every old error had this
cause. Optional attribution is discarded after parsing and never enters model
history. Malformed event JSON, exhausted local JSON budgets and invalid event
fields have separate closed diagnostics. The byte, depth, node and aggregate
memory limits remain enforced; five retries and no tool replay remain unchanged.

In the supplied Claude Code 2.1.88 snapshot, the Anthropic SDK's
`core/streaming.mjs` parses SSE data with `JSON.parse`; no application node-count
ceiling is installed on that path. The JSON helper's 50-entry / 8 KiB thresholds
control caching, not response admission. In the supplied Grok Build snapshot
(`SOURCE_REV` 559751fdcec02d413e4c57c8832ab275e4f44980),
`xai-grok-sampler/src/client.rs` uses `serde_json::from_str` for Responses events
without a node-count ceiling. Its pinned serde_json 1.0.149 defaults to 128
levels of recursion; depth is not node count. Neither observation implies
unlimited process memory or that all other transports/storage paths are unbounded.
For shell exit status, owned-descendant timeouts, multi-line script previews and
PowerShell selection, see [command lifecycle diagnostics](command-lifecycle-diagnostics.md).

For local code-2 failures after large child output, see
[evidence digest recovery](evidence-digest-recovery.md).

Sencode's event admission is deliberately explicit and separate from Sengoo's
legacy JSON API; the current event budget is 65536 nodes / 1 MiB, depth 64.
