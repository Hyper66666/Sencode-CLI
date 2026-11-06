# Responses task continuation

The Sengoo provider follows Sencode's existing Responses turn contract from
`sencode-sampling-types/src/responses_turn.rs` and
`conversation.rs::requires_continuation`.

Only a validated `response.completed` with an explicit boolean
`response.end_turn: false` asks the controller for another request on the same
task. Missing and true end the turn normally. Message phases such as
`partial_answer`, `commentary`, `final_answer`, and unknown future phases are
preserved without guessing task completion. Non-boolean signals, incomplete
responses, refusal, malformed events and missing provider terminal events cannot
authorize continuation or tools.

Canonical assistant records retain optional `responses_end_turn` and boolean
`requires_continuation` beside ordered `responses_output`. These control fields
are local metadata; the wire history replays only validated protocol items. Opaque
items and phases remain scoped to the producing endpoint, connection and model;
switching targets rebuilds public history. The controller continues without
fabricating a user message, retaining cancellation and the shared request/token
budget, including child requests.

A complete HTTP Content-Length body or chunk terminator plus a complete SSE
stream and provider terminal can settle the request without waiting for a
keep-alive socket to close. Truncated HTTP or SSE remains an error.

Run `tests/responses_end_turn_fixture.py CANDIDATE --evidence REPORT.json` for
the isolated real-host/loopback scenarios and `src/tests_protocol.sg` for native
parser regressions. Synthetic local service checks and real API checks are
separate evidence; this fixture does not use an external provider.
