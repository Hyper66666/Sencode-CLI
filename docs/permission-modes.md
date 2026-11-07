# Native CLI permission modes

The native API engine has three request policies. Shift+Tab selects the next
policy; the composer footer names it. Each accepted request keeps its captured
policy, so switching while work is running affects later requests. An approval
already being displayed still needs its own response.

The public CLI remembers each local session's selected mode, explicit command
authorization and managed-backend policy profile. `sen -c`, `sen -r`,
`sen resume` and `/resume` restore that selection, including changes made
without sending another message. Changes during execution are saved after
cleanup; startup lock contention retains the pending selection for retry.
`--permissions manual|auto|full` explicitly overrides it. New sessions and old
sessions without permission metadata use manual approval. Local branches and
directory renames preserve preferences; independently imported history cannot
grant execution permissions. See [session memory](scroll-session-memory.md)
and the [verification record](permission-session-verification.md).

| Mode | Workspace edits | Commands | MCP |
| --- | --- | --- | --- |
| 手动审批 (`manual`) | Ask | Ask | Ask |
| 自动审批 · 文件编辑 (`auto`) | Automatic | Ask | Ask |
| 完全权限 (`full`) | Automatic | Automatic | Automatic |

Reads remain automatic in every mode. Automatic approval is the edit-approval
mode; it does not run a model-based risk classifier. Full access authorizes
arbitrary noninteractive commands and approved configured MCP execution. The
command process has the current user's operating-system access.

Plan applies to one selected turn and exits after its reply completes, is
cancelled or fails. Resuming a session does not restore Plan. The selected
manual/auto/full mode continues to apply after Plan ends, without automatically
executing the saved plan or approving tools.

Plan remains read-only in every mode, with the designated plan file as its
existing exception. Explore and plan children receive a read-only policy;
general children inherit only their parent's permissions and existing one-level
limit. Full access does not change workspace path checks, tool schema checks,
write scheduling, process-tree cleanup, execution fencing or the no-replay rule
for uncertain side effects. Unknown tools are still rejected.

The host submit contract adds a boolean `full_access`. It defaults to false on
every submit. A submit following full access clears implicit automatic edit and
command flags unless the new submit explicitly grants them. The legacy
`auto_edit` and `allow_commands` fields and command-line flags keep their
existing meanings.

Managed account backends retain their explicitly selected backend policy. They
reject native full access because this adapter cannot enforce it. They must not
be displayed as enforcing a native permission mode.

Native verification is implemented in `src/tests_permissions.sg`, driven by
`tests/permissions_fixture.py`. It executes owned file edits, a shell command,
MCP discovery and a call; it also checks Plan, child, managed-backend and legacy
submit restrictions. It uses no provider, user state, clipboard or credentials.
