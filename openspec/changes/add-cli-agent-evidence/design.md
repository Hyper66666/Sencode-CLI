## Source lifecycle and authority

Reuse completed `shared_tool_ledger.result` and assistant `messages.text` as the
only evidence sources. A reference contains kind, session_id, source_id and the
SHA256 of the exact UTF-8 source bytes. No second copy, new global retention
promise, deletion policy or new shared-state schema is introduced. Source
retention follows the existing session store; deletion or change invalidates a
reference. Imported history is data and never grants execution authority.

`read_evidence` requires a currently valid execution fence and current tool
policy. It may read the caller's session or a direct child declared by the host
session-origin metadata in the same project. A child can read its own evidence;
it cannot read its parent or siblings. This read grants no write/command/Goal
permission. Denied and missing sources return the same unavailable response.
A changed digest returns source_changed. No missing or uncertain evidence is
recreated by running an old tool. Cancellation retains existing cleanup gates.

## Bounds and byte cursors

Source admission is at most 16 MiB per row, inspected in SQL before allocating
text. This admits existing bounded aggregate results; it is not a promise that
all producers can emit 16 MiB. A read requests 4..16384 UTF-8 bytes (default4096),
uses a byte offset, rejects offsets inside a code point and returns offset,
next_offset, total_bytes and done. The final boundary backs up at most3 bytes.
A source hash is required on every page; changing versions cannot be joined.
Pages describe the retained UTF-8 representation (including existing lossy or
truncation metadata), not the original binary stdout/stderr.

## Reports and model context

Children are asked to finish with schema1 JSON: outcome, summary, changed_paths,
checks, blocker and next_action. All are model claims; checks distinguish
planned/run/pass/fail/unknown. The host separately attaches actual child status,
error and public model/connection attribution. A forged completed/pass cannot
finish a Goal or override a canceled/failed execution. Invalid/oversize reports
produce a bounded UTF-8 excerpt and an explicit diagnostic; full original data
remains available through the existing history or ledger.

Small ordinary tool results (<=16384 encoded bytes) remain identical. Large
results get a 4096-byte preview, exact source reference and retained control
flags. read_evidence pages bypass projection. Child coordination snapshots get
bounded reports and assistant-text references; raw snapshots remain in public
history and ledger. Automatic terminal snapshots use the same projection.

Projection changes only model context content. Tool call/result IDs, ordering,
complete protocol groups, uncertainty and Goal state are preserved. Recovery
loads all required tail rows, projects each before aggregate model admission,
and refuses an oversized/malformed complete tail without sending a partial
history. Checkpoints and public history retain their existing meanings.

## Compatibility and verification

The new tool is explicitly registered in schema, validation, policy, parent and
child dispatch. Unknown tools remain denied; Plan allows only this read.
Executable native tests cover report validation, Unicode pages, deleted/changed
sources, authorization, source limits, ledger replay and recovery projection.
Fixture-provider tests exercise actual model requests and original public
history. Existing child/recovery/Goal checks guard protocol and authority.
No fixture is represented as live-provider or installation qualification.