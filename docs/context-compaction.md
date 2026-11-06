# Native context compaction

The native Sengoo implementation follows the existing Sencode runtime's
continuation policy: trigger at 85% estimated occupancy, select a partial tail
against a 50% target, preserve complete assistant/tool runs, carry forward prior
summary facts, and reject inadequate summaries. Its prompt and implementation
were written in Sengoo for this CLI. No recovered Claude implementation was
copied.

The inspected Sencode modules are `sencode-compaction/src/select.rs`,
`code_compaction/{config,assemble,summary,sample,compact}.rs`,
`intra_compaction/{config,trigger}.rs`, and the shell's full-replace context
helpers. The borrowed design ideas are byte/token-budget selection, original
system-instruction retention, a true-user-query anchor, a healthy cleaned
summary minimum and explicit accounting for summary requests. This is a native
CLI implementation of those mechanisms; it does not import the Rust runtime's
memory engine or pretend local byte estimates are model token counts.

## Lifecycle

1. Validate roles, tool identities and complete call/result groups.
2. Estimate occupancy from serialized history plus tool declarations.
3. Select a whole-unit tail by budget and fingerprint the complete source.
4. Send an internal, tool-free summary request through the existing scheduler
   and shared Goal request budget.
5. Clean leading scratchpad and wrapper tags. Require a substantive summary,
   its planned byte cap, and at least 20% reduction.
6. Check the source fingerprint and boundaries again. Refuse a result still
   above the active trigger.
7. Persist the fenced checkpoint. Only then install the new owning `JsonDoc`.

Summary requests emit lifecycle and phase events but no public answer deltas or
assistant transcript rows. The public transcript is append-only with respect to
compaction. Failure leaves its source and last successful checkpoint intact.
There is no silent quality retry; any explicit retry takes another shared
budget reservation. Ordinary requests and summaries retain cumulative
accounting across restart.

The source hash protects same-count modifications, not just appended turns.
It uses Sengoo's explicit bounded in-memory SHA256 interface with a 786432-byte
maximum; the legacy 64-KiB hash entry point remains unchanged. A valid
90684-byte context exposed that language-library boundary during this work.
The generated carrier's `context_summary` marker prevents it from becoming the
newest actual user task on the next cycle. The latest complete tool group is
always retained, even if it exceeds the target; post-validation rejects a
context that still exceeds the trigger.

## Compatibility and limits

Configuration remains schema 1. Existing explicit values are retained, while
new optional fields default to trigger 85, target 50, summary minimum 500 Unicode
scalars and reduction minimum 20 percent. `context_window_tokens` is a declared
user limit. An omitted target adapts to half of an older trigger of 50% or
lower, with a minimum of 1%. Only the legacy 1% trigger permits an implicit equal
1% target; explicit targets must remain below their trigger. The occupancy
estimate is `(serialized input bytes + 2) / 3` plus
16 per message, not a provider tokenizer or quota calculation.

The summary byte cap is the smallest of 65536, one quarter of the input ceiling,
and one quarter of the original history size. Too-small histories and histories
without a reducible old prefix are refused. Target occupancy is best effort;
the preservation rules and final trigger check take precedence. The text prompt
is capped at 786432 bytes. Strict token-budget mode remains unsupported until
all request paths provide the necessary accounting. Managed engines retain
their own advertised context behavior.

## Executable checks

`src/tests_context_compaction.sg` covers model limits, complete groups and the
preserved latest task. `src/tests_context_compaction_refinement.sg` adds default
and old-schema compatibility, byte-budget tail sizing, snapshot fencing,
out-of-order tool results, malformed identifiers, summary cleaning, quality and
reduction refusal, and 32 repeated fresh-document compaction cycles.

`tests/request_recovery_fixture.py` uses a synthetic loopback provider, temporary
SQLite database and a unique synthetic credential reference. It checks repeated
automatic compaction, exact cumulative request accounting, clean private
summaries, preserved public history, checkpoint restore and summary-failure
handling. It never uses an existing user's connection or database. This fixture
is separate from real provider and installation verification.

Current run evidence and source hashes are recorded in
`target/context-refinement/evidence.json`. A passing module test does not by
itself establish controller, managed-engine, desktop or installation behavior.
