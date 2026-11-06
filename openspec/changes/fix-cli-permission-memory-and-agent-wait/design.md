# Design

Keep schema-v1 permission metadata in `shared_modes.cli_permissions`. Store only
the selected mode, legacy command authorization and backend policy profile.
Save under the session OS lock while idle; update only this JSON member in one
transaction. UI changes during a request are persisted after cleanup and never
change that request or an approval already shown. Public resume and in-app
switching load the destination's selection. Missing metadata defaults to manual.
Explicit permission flags override the remembered policy. Keep Plan independent.
Defer idle preference writes until the host reports ready; retain and retry a
temporarily busy save with a monotonic delay. Switching, branching and exit
stop the owned host before the final flush, so startup contention cannot drop
an unsent selection. Permanent failures remain visible with their status code.
An engine submit whose preference save cannot acquire the idle session returns
a structured admission failure. It leaves the persistent host alive, does not
accept the request ID, and may be submitted again after the owner finishes.
Local branches inherit; independent untrusted project-history import does not
grant permissions. Native engine submits still require a complete policy
snapshot and never inherit implicit full access from a previous submit.

A bounded `wait_agents` releases permits while waiting, then makes its caller
runnable when returning. A false model-acquisition result is scheduler
backpressure, not a failure or budget exhaustion. While waiting for capacity,
pump child streams/tools, cancellation and ownership checks. Reserve and charge
a request only after acquiring capacity; actual budget exhaustion still stops
execution. Cancellation and unknown tool outcomes retain the existing cleanup
and no-replay guarantees. Use a monotonic deadline for child waits.

Transcript heading visibility is a projection of user/assistant turn boundaries.
Tools, diff cards, child cards and notices do not start another assistant turn.
Host-created child/Goal continuation messages retain explicit `cli_internal`
metadata for model context and recovery and do not impersonate user turns in
the transcript. Older records without that marker are preserved as recorded.
Keep separate stable message IDs and stream segments for ordering, anchors and
updates. Reflow and history restoration compute the same heading rule. A new
user message starts a new assistant heading. Empty assistant/tool messages must
not produce several headings.

Use an isolated slow loopback provider to reproduce the screenshot path before
editing, then verify timeout, slot contention, cancellation, actual budgets,
permission resume and real Windows console rendering against one candidate.
