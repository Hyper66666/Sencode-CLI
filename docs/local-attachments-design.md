# Local attachment design (not implemented)

This draft records the next media boundary. It does not close the fullscreen
media phase, provide an `/attach` command or claim a working image/PDF request.
The candidate being tested during this draft remains unchanged.

## Existing behavior and reuse

`src/provider.sg` currently reads each history entry's `content` as text and
emits text in Chat Completions, Responses and Messages. The stream parser can
continue handling returned text/tool deltas after a future multimodal request;
it does not establish multimodal request support by itself.

The desktop already has `AttachmentRef`, `ToolImageRef`, ordered
`ContentBlock::Image`, durable image assets, retryable attachment commit handles
and an 8 MiB non-image registry limit. These are concrete compatibility inputs,
not permission to write new attachment JSON into arbitrary existing fields.
Its PDF.js WebView preview is not a native CLI PDF engine. Shared queued prompts
have `attachments_json`, but the CLI currently needs explicit validated asset
loading and public-history projection to consume it.

## Ownership split

| Owner | Responsibility | First bounded result |
| --- | --- | --- |
| Sengoo foundation | Same-handle local binary read, owned bytes/digest, bounded magic/header metadata | PNG/JPEG dimensions and PDF version/header facts |
| Sencode assets/state | User selection, session-scoped durable asset, restart and desktop compatibility | Stable references; explicit missing/unsupported state |
| Sencode Provider | Typed ordered content, captured target capability, three protocol encoders | Exact complete-request preflight and golden fixtures |
| Sencode TUI | Explicit attach/remove affordance, escaped name/MIME/size/status, fresh send | Responsive list/cards; no inline image renderer required |
| Future PDF engine owner | Page count, encryption, extraction/rendering and offline packaging | Separate versioned capability and executable evidence |

Only the first column's foundation functions belong in native/stdlib work.
Provider names, model selection, API keys, JSON, SQLite and agent state remain
in Sengoo application code and do not cross file-I/O worker threads.

## Proposed capture and send lifecycle

1. An explicit user action selects a literal local path. Merely pasting a path
   into prose does not read a file or upload it. Clipboard media and remote URL
   fetch remain separate capabilities.
2. Validate local path permissions and acquire a bounded file snapshot. Inspect
   the copied bytes, not the filename extension. Escape display strings. Show
   bytes, detected MIME, header dimensions/version and unsupported reasons.
3. Keep a session-bound draft asset with an ID, digest, exact byte count and
   owned byte source. Partial capture is not a sendable asset. Removing a draft
   releases only assets this CLI owns; never delete the selected source.
4. At turn acceptance, freeze text, ordered asset IDs/digests, connection, model
   and capability revision under the normal execution fence. Later edits or
   default-model switches affect only future turns. Do not automatically retry
   an interrupted send or reuse a previous upload/approval against changed data.
5. Check target support and exact serialized request size before any outbound
   request. Unknown/unsupported target capability requires an explicit choice
   (different target, text-only send with user consent, or cancel). Never silently
   remove an image, turn it into a filename-only success, or switch provider.
6. Persist the accepted public message and attachment references with the
   existing fenced/changelog transaction. Reuse the desktop image contract where
   its loader can actually consume the asset. A necessary shared asset/schema
   change needs a version gate and desktop adapter; opaque CLI-only references
   cannot be advertised as desktop handoff support.
7. On restart, verify the retained asset's byte count/digest. Missing/corrupt
   assets are visible and block a multimodal resend until the user resolves
   them; do not silently reread an unrelated file now at the old path. Failed or
   cancelled turns retain a retryable draft/reference until explicit discard or
   well-defined owned-asset retention. No success is inferred from upload alone.

Source copies are immutable after capture. This guarantees the bytes selected
for the request, not an atomic transaction over a concurrently rewritten source
file. Subagents receive only explicitly scoped references and cannot use an
attachment path to widen their inherited read permissions. Plan can inspect
already-authorized attachments; it gains no shell, MCP or arbitrary write route.

## Provider request boundary

Add an application content representation separate from the legacy flat text:
ordered `text` and `image(asset_ref)` parts, and later `document(asset_ref)` only
when an adapter explicitly supports it. Legacy text-only history still produces
the current request shape. Assistant tool calls/results retain their existing
IDs, order and protocol continuation behavior.

The initial image encoder fixtures should verify these distinct representations:

| Adapter | User content representation to qualify |
| --- | --- |
| Chat Completions | Array of text and `image_url` data-URL parts |
| Responses | Array of `input_text` and `input_image` data-URL parts |
| Messages | Text and image parts with a base64 source and detected MIME |

Field shapes must be pinned by golden fixtures and a separately authorized live
compatibility check for the configured endpoint/model. A protocol name or a
model-name substring does not establish vision/PDF support. Managed-account
adapters require their own negotiated media capability and tests; success for
one API-native encoder does not qualify them all. No remote image URL fetch or
provider Files API/upload lifecycle is implied by local data URLs.

Legacy `std::net` requests retain their 1MiB cap. The new explicit bounded
request/document interfaces accept at most16MiB with aggregate native admission;
they do not automatically enable larger requests for legacy callers.
Compute base64 length as
`4 * ceil(raw_bytes / 3)` with checked arithmetic, then include MIME/data-URL
framing, escaped JSON, all retained history, instructions and tools. Check the
actual final request length against both adapter and transport caps. An 8 MiB
local asset is not automatically sendable. Do not raise the native cap without
bounded upload/copy admission and concurrency evidence. UI errors must name this
local limit rather than attribute it to the provider.

## PDF boundary

The baseline generic inspector reports a PDF candidate's header/version and
truthful capabilities. Page count, encryption and full validity remain unknown
without a real parser; no substring page counter is acceptable. Native PDF
document submission, text extraction/OCR and page rendering into image parts
are three different future paths. Each needs explicit adapter/engine support,
size/page/time limits, cancellation and restart semantics. Header-only probing
or rejecting unsupported PDFs does not complete the PDF or multimodal phase.

## Minimum fixtures before UI integration

- Foundation: temporary Unicode/space files at byte-cap edges, same-handle path
  replacement, binary NULs, reparse/device refusal, malformed/huge image headers
  and PDF header-only capability. See the Sengoo child proposal.
- Three adapter goldens: same ordered text + one tiny locally generated image,
  followed by a tool turn and second user turn; verify MIME, exact base64 bytes,
  text-only compatibility, tool IDs and no accidental path disclosure.
- Preflight refusal: forged extension, missing/corrupt asset, unknown vision
  model, PDF engine absence, NUL/invalid input and complete request one byte over
  the native cap. A loopback capture server asserts zero requests on refusal.
- Frozen send/restart: switch default model while a request is queued, modify
  the source path, restart after capture and verify the same digest/reference;
  cancellation leaves a visible retryable draft and does not resend itself.
- Shared-state handoff: isolated desktop-compatible DB/asset store, idle handoff
  and fenced stale owner; both clients show the same image or an explicit
  unsupported/missing state, with no silent text-only continuation.
- Resource/responsiveness: repeated attach/remove/failure, multiple concurrent
  model requests with aggregate copy budgets, slow local read cancellation and
  read/encode early returns. Track native owners and use ASan where supported.

No fixture reads the real clipboard or credentials, contacts a live provider,
opens user documents, downloads dependencies or alters the real session DB.
All temporary input and asset cleanup follows the repository's per-file rule.

Implemented evidence now covers the generic file/media foundation, ordered
three-protocol image goldens and an actual loopback PNG capture over1MiB with
9 zero-outbound preflight refusals. See `target/provider-media` and the sibling
Sengoo `target/file-media/evidence.json`. Shared capture/restart/desktop/visible
attachment controls and a real PDF engine remain unimplemented gates.
