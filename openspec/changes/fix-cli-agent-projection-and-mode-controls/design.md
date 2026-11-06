# Design

Child events are scoped by child session/agent identity and update one summary
card. Child deltas never become parent answer deltas or literal tool JSON.
Malformed events and terminal control characters cannot break the host or
appear as raw protocol data. The transcript remains the canonical stored data;
rendering does not execute tools. Existing request IDs gate all live events.

The selected target has an effective effort resolved from the same capability
metadata used by request admission. An implicit default selects medium only
when supported; explicit unsupported settings fail rather than pretending to
apply. Running requests keep their captured target and permission settings.

Shift+Tab is a reserved composer action after modal focus handling. It never
submits a draft, answers an approval, escapes a selector or changes a running
request. Manual is the default. Auto authorizes workspace file edits and still
asks for commands/MCP; full authorizes those tool categories too. Full is an
explicit policy field, not inferred from unrelated legacy flags. Plan, child
role, path validation, resource bounds and fencing are checked first. Managed
engines expose their actual backend policy and cannot claim unsupported modes.
The composer footer shows the current mode continuously, including streaming.

OS clipboard, credentials and user sessions are not used by fixtures. Public
acceptance uses disposable projects, an owned hidden Windows console and a
loopback provider. No additional runtime language is introduced.
