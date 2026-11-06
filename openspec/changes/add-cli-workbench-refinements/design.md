# Runtime and UI boundaries

Sengoo owns all UI frames, menus, animation clocks, agent context and scheduling.
The generic runtime remains the OS I/O boundary. The local engine emits typed
phase and diff events; the frontend never executes model parameters speculatively.
Tool parameters are validated and permission checked before scheduling.

Connection, model and effort are captured together for each request. The model
catalog reads enabledModels, never the discovered-but-disabled catalog. Enter on
a model opens an effort picker; a separate selection commits the future target.
Unsupported managed-backend controls remain disabled with a reason.

Thinking and compaction use separate bounded animation frames driven by monotonic
elapsed time, with renderer-owned styling and no model ANSI. Diff cards retain
actual source line numbers, context, delete/add markers and red/green semantic
styles. NO_COLOR retains markers and plain output has no cursor control.

Recoverable request failures remain within the workbench with context-preserving
diagnostics. Invalid protocol data is rejected, never guessed or replayed. A
stopped host can restart only after its process tree is reaped; unknown tool
outcomes still pause for explicit reconciliation.

Compaction preserves public history, tool-call/result pairs, current task,
project instructions and cumulative budgets; only committed model context changes.
Cancellation retains in-use write permits until actual tools are quiescent.

Validation uses owned temporary workspaces/credentials, loopback providers and
hidden console cell/attribute captures. User project inspection is read-only.
