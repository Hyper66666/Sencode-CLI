# Event parsing boundary

Parse each provider event with `json_parse_limits(data, 1048576, 65536)`.
The existing runtime retains byte, node, depth, document-count and aggregate
reservation admission controls; parsing remains on the single state owner.
Each parsed event is dropped after projection. Optional usage attribution is
never copied into history; only reported totals and bounded ordered output
items survive. No native implementation is needed.

Malformed event JSON remains error 10; explicit resource exhaustion returns 13.
Diagnostics contain closed categories, never raw events, credentials, URLs,
provider error messages or hidden reasoning. Validated terminal events remain
mandatory before local tools can execute. All existing five-retry, cancel,
permission and no-side-effect-replay rules remain in force.

Evidence separates synthetic protocol/continuation fixtures, a minimal live
probe, a history-shaped live reproduction and installation. Live probes use
an isolated project and DB, a read-only view of the source session and the
existing OS credential. They never execute returned tools or change source
history. Response text is inspected in memory and only structural evidence is
saved. The first live response can be replayed locally for deterministic retry
checks without repeated upstream calls.
