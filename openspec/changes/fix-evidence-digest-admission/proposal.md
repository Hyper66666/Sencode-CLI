# Fix evidence digest admission and child failure attribution

The reported successful child command retained a 106138-byte result. Model-context
projection then calls the legacy 64-KiB digest through state_digest even though
evidence sources admit 16 MiB. The resulting local error 2 cancels the parent
request and the child; it is not a shell or HTTP failure.

Use Sengoo's existing explicitly bounded hashing interface at both reference
creation and evidence read. Keep the legacy API and state-identity digests
unchanged. Preserve source/permission checks, exact bytes, tool deduplication
and process cleanup. Attribute child context/projection failures explicitly.

Non-goals: new native ABI, higher source retention limits, replaying completed
tools, making child claims trusted, or completing the larger agent-evidence plan.
