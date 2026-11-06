# Long history and model-context recovery

The SQLite transcript is the public source of truth. It is not limited to the
first 1000 messages. Complete history either returns every row or fails with an
explicit resource status; callers can read exact absolute ranges when a single
document cannot hold the whole transcript.

History documents contain `messages`, `total_messages` and `offset`. The UI
uses a separate newest-window query. If rich rows exceed its document budget,
that query reduces the newest window and reports its actual offset. It never
switches back to an old prefix. Invalid JSON is not treated as a resource
limit. A single oversized newest message remains an explicit error.

Public query admission is 16 MiB encoded output and the runtime's 4096-node/link
bound. SQL lengths are checked before allocating oversized row text; small
windows reserve only their bounded size. There is no silent successful prefix.
Raw legacy JSON node exhaustion is normalized to resource status 13 only for
the exact `json node limit exceeded` diagnostic. Other parse errors retain 10.

The model uses a different path: current system instructions, the existing
compaction checkpoint, then every public message after its absolute
`messages_seen` count. Assistant tool calls and their outputs must remain
paired. A UI recent window cannot substitute for that complete canonical tail.

Model context is bounded to 1000 messages and 786432 encoded bytes, including
system instructions and retained checkpoint messages. At 850 messages,
automatic compaction runs even when tiny messages have not reached the usual
byte/token thresholds. Its summary request spends the existing shared budget;
compaction and restart never reset accumulated requests or tokens. Checkpoints
record the SQL public count, even when the full transcript cannot fit a single
JSON document.

A valid checkpoint beyond message 1000 can resume normally. An older session
without a checkpoint whose canonical context already exceeds admission fails
with status 13 and a diagnostic. Its newest messages and transcript remain
intact. Start a new session to continue model execution; `/compact` cannot
invent an incomplete context for that oversized old session.

Native verification:

```text
tests_long_history_state.sg
tests_long_history_context.sg
python tests/long_history_fixture.py target/test-long-history-state.exe target/test-long-history-context.exe
```

The first regression covers 1105 complete rows, absolute ranges/tails, adaptive
newest windows and byte/node rejection. The second covers canonical checkpoint
restore and reopening, orphan/future checkpoint rejection, a 1900-row session
with 900 newer small messages, real loopback summary compaction and exact
request/token accounting. No real provider, user configuration or user key is
used. The generated loopback-only Credential Manager entry is removed after
the native context test.

The standard `scripts/test.ps1` runner includes `long_history_state`,
`long_history_context` and `long_history_public`. It builds the native probes
and drives the context probe with the loopback summary fixture. The public
probe takes an explicit final CLI candidate and verifies the total, newest
window, project-root rename, archive identity and terminal restoration.
Candidate `5b34aaf31a90a964b2b4bc3334f61277d4bd40deed92a711fe28a37d6c52d973`
passes all three runner cases in
`target/tool-reliability-r2-20261105-opt/long-history-runner.json`.
