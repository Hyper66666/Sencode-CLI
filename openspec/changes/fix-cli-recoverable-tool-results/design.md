# Error and replay boundary

`Result` failure from a tool implementation is not automatically failure of the
agent host. Built-in filesystem and hardened Git reads have no mutation
capability. Ordinary invalid input, missing path, permission, unsupported, I/O,
parse, timeout, bound and UTF-8 failures from those reads become an `is_error`
tool result, persisted and appended under the original call ID. The model may
choose a corrected new call. The host never retries the call automatically.

Invalid handles, resource exhaustion, execution interruption and cancellation
continue to abort the host. Before checkpoint admission, editor preview/path
validation is known not to have written; ordinary errors there can be returned
as explicit no-operation results. Errors after entering the checkpoint or a
general subprocess/MCP/coordinator path have no such proof and pause.

Unknown outcomes carry a durable `outcome_unknown` marker. Reusing that call ID
returns the same recorded outcome and pauses again; it cannot execute again or
silently treat a recorded unknown outcome as a normal successful completion.
Persistence, lease validation, hook rejection, approval denial and event sink
failures remain host boundaries. Permissions and Plan are not weakened.

Parallel Git reads keep their leases until process-tree quiescence. A settled
read failure is a result and does not cancel unrelated reads. Results are
published once in declaration order. Cancellation still drains live work and
stops the batch. Filesystem reads reuse the same serial controller behavior
inside safe-read schedules rather than inventing a second error policy.

Behavior was compared read-only with the supplied Claude tool executor's
exception-to-error-result path and GrokBuild's tool-result/error continuation.
No source implementation from either project is copied. The added outcome
proof is specific to Sencode's durable no-replay and permission contract.

Native tests precede final-main integration: reproduce `list_directory`
status 7; correct it with a new ID; check cached errors; missing/invalid UTF-8
reads; deterministic editor preflight rejection; settled Git failures;
unknown-side-effect and cancellation preservation; resource cleanup.
