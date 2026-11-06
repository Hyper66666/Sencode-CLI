# Local attachment design pointer

The detailed proposal, lifecycle, ownership, privacy limits, three-adapter
representations, request-size constraint and minimal fixture matrix live in
`sencode-cli/docs/local-attachments-design.md` (relative to `windows/`).

This child owns application requirements only. The sibling Sengoo change owns
same-handle bounded files and generic format/header capability requirements.
No source, tests, scripts, installers or runtime binaries are modified by this
proposal. All implementation and acceptance tasks are intentionally unchecked.

The current 1 MiB native streaming request cap is a hard preflight input. A
later generic upload expansion must account for raw bytes, base64, serialized
request and worker copies across concurrent requests. Local asset size limits
must not imply that the captured model can accept the complete request.

Failure/recovery states are captured, inspecting, draft-ready, unsupported,
accepted, sending, retryable, committed, missing/corrupt and discarded. Only an
explicit user send enters accepted/sending. Existing execution fences protect
accepted public history; neither a restart nor an incomplete upload replays a
request. A model capability switch is resolved before outbound bytes and never
silently drops parts or changes provider.

The initial PDF engine-absent result is an honest unsupported capability, not
completion of the PDF stage. Full PDF acceptance requires a separately named
native submission, extraction or rendering path and actual offline/installed
consumer evidence.
