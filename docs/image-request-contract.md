# Original-image requests

Only explicit user-submitted absolute paths in `submit.images` grant image
read authority. The TUI keeps `[image1]` chips mapped to original paths; bitmap
clipboard fallback uses a bounded system-TEMP PNG. The backend canonicalizes
and snapshots each original, inspects PNG/JPEG headers and records path, MIME,
byte length and SHA256. It does not create a project image copy or store Base64
in messages. The image file must remain available with its original bytes.

The exact selected enabled model must declare `capabilities.visionSupported`
true. An explicit connection-level false narrows that capability. A model name
or protocol never enables it. Managed-account adapters have no verified image
contract in this increment and reject image input. The submit list admits at
most eight paths and 8 MiB of original binary data per turn. The complete active
image history also has an 8-MiB binary ceiling and a 16-MiB converted JSON bound.

Session catalog grants identify exact path, size and digest. Request conversion
checks capability and grants before opening history paths, then checks the same
immutable snapshot's size/hash before Base64 conversion. Branches and portable
imports do not inherit read authority. Reattaching unchanged original images
can grant them again. Changed or missing originals require restoring the exact
bytes or starting a new session; no current file substitutes for old content.

Text and image parts are converted into actual Chat Completions, Responses or
Anthropic Messages wire content, not paths pretending to be image input. The
conversion is ephemeral and completes before a network job starts. No external
provider or user credential is used by the loopback acceptance fixture.

The large-image regression exposed a caller ownership mistake on rejected
conversions: Sengoo `Result<T,E>` drops only the active branch. Putting a live
`JsonDoc` into the inactive `value` of `is_ok:false` transfers it without Drop.
Image helpers now return a zero-handle inactive placeholder and keep the local
document owned for cleanup. Repeated capability, missing-grant and hash-mismatch
rejections check that bounded JSON document count and reserved bytes return to
zero before transport starts. This fixes the call site without changing Result
representation or compiler Drop semantics.

Run `tests/image_request_fixture.py target/test-image-request.exe` against the
compiled `src/tests_image_request.sg`. It verifies an original >1-MiB PNG in
three real pollable EngineRequests against Python's independent Base64 result,
7-byte response fragments, exact text/MIME ordering, no internal reference
fields on the wire, no original mutation or image-copy files, and zero retained
FileSnapshot handles. This is Windows local fixture evidence; final CLI/TUI and
real-provider checks are recorded separately by integration.
