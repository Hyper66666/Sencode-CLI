# Ownership and failure boundaries

The integration owner changes evidence.sg and the relevant controller/diagnostic
paths and fixtures. Read user state only through SQLite mode=ro; reproduce with
synthetic data. Preserve adjacent ongoing work and do not commit/push.

Use an evidence-local digest helper whose admission matches the existing source
maximum (16 MiB), with the explicitly bounded std::hash API. Both creating a
reference and verifying every page use the same helper. state_digest remains a
legacy small-identity helper. SHA256 remains over the exact UTF-8 representation
already stored by the authoritative tool ledger or assistant message.

Projection remains a model-only preview, preserving host control flags and a
reference to full data. A returned page must match the source digest, session
authorization, byte offset and Unicode boundary. Missing, modified, unowned or
oversized evidence never causes an old command to run.

The child-result projection and context insertion boundaries record a distinct
child-coordination failure with child/task and tool identity. The parent cancels
its in-flight request conservatively, retains completed results and drains owned
resources. No provider retry is used to disguise a local context/state failure.
Closed host-stage metadata is retained with request attempts for later diagnosis.

Validation: independent <=64-KiB and 106138-byte comparison; native exact digests
through 16 MiB; large-result projection and authorized multi-page Unicode reads;
synthetic final host with a child command producing >64 KiB, parent continuation,
restart restoration, no side-effect replay, and injected host-stage attribution.
