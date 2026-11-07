# Design

Each model turn admits no tools until the entire response validates and is
committed. Thus a failed model attempt can be retried from the same accepted
history without replaying completed local tools. Each attempt uses a fresh ID,
is charged to the existing budget, and retains the same provider/model snapshot.
An incomplete streaming message is removed only under the execution fence and
only while it has no canonical shared_history record. Final failure and user
cancellation retain the last partial response. The retry event instructs the
TUI to replace provisional text, while completed transcript/tool entries remain.
Children retain accepted history and reset only the failed request preview.
Consultation releases model slots before requeueing an attributed attempt.

Backoff defaults to 250/500/1000/2000/4000 ms. Valid Retry-After may increase a
wait up to 300 seconds. Invalid headers use backoff. There is no old 30-second
aggregate wait cutoff. Every wait pumps input/children or is queued by monotonic
deadline. Explicit cancellation, exhausted budgets, lost execution authority,
unknown tool outcomes and failed state commits pause normally.

Transport phases distinguish network read, HTTP framing/finish, SSE decode/
finish, provider event/terminal/validation. Provider error content maps to a
closed category, never arbitrary text, URLs, headers or credentials. HTTP 2xx
is secondary context. At most 256 request records use explicit 8192-node JSON
budgets for their richer fields; unrelated mode state remains independent.

The built-in write_file/apply_patch paths normalize only .bat/.cmd outputs.
They preserve exact stale-write matching against original bytes, normalize
existing CRLF before emitting CRLF and show normalized content in edit preview.
The command runner retains real exit codes/stdout/stderr and does not treat a
normal nonzero exit as infrastructure failure or automatically rerun it.
