# Large child results and evidence references

A successful command can produce a tool result larger than 64 KiB. The evidence
view keeps the exact result in the authoritative ledger and sends a shorter
preview plus an exact-source SHA256 reference to the model. The admission for
those retained sources is 16 MiB, independent from inline model-context size.

The legacy `state_digest` uses Sengoo's original 64-KiB hashing API for small
state identities. Calling it on larger evidence was an integration defect:
the native API correctly returned invalid argument (code 2), but the controller
stopped the main request while handling the child's otherwise successful result.
Parent cleanup then cancelled the child. A successful preceding command card
therefore did not identify the failed stage.

`evidence_digest` now explicitly calls `hash_sha256_str_bounded` with the existing
16-MiB evidence admission. Both reference creation and every page verification
use it. The legacy state hash API, source ceiling, byte cursors, digest format,
session authorization, execution fencing and side-effect deduplication remain
unchanged. Completed results stay retained; no old command is rerun to recreate
evidence.

Host coordination failures now include a closed stage (`child_scheduler`,
`child_tool_projection` or `child_tool_context`) and, when known, child task and
tool identity. Those fields are also retained in failed request-attempt metadata.
They distinguish local host failures from HTTP status, shell exit and user
cancellation; cleanup still stops the parent request and waits for owned work.

The focused native regression checks exact independent SHA256 vectors from
65536 through 16777216 bytes, a one-byte-over ceiling, >64-KiB Unicode result
projection, authorized paging, unrelated-session refusal, version mismatch,
retained results and local failure attribution. The final-host fixture runs a
child command with 106138 output bytes, reads its evidence from the child and
parent, completes both tasks, and restarts the session without rerunning the
command. Synthetic provider fixtures do not establish live-service behavior.
