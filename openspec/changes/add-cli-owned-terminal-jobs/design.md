# Design

An explicit request contains executable, literal args, workspace/cwd, dimensions
and user environment overrides. A preview/fingerprint identifies the complete
launch snapshot. Start requires fresh host approval of that snapshot, refuses
Plan/child-policy starts, resolves a cwd inside the workspace without reparse
components, and acquires cli_state_workspace_lock before starting the process.
The child gets a cleared environment plus a fixed OS discovery allowlist and
explicit user edits. Provider keys and arbitrary parent env are not inherited.

Lifecycle is created/running, direct-exited-with-descendants, tree-quiescent,
closed or cleanup-unknown. Output bytes are bounded in a 256KiB ring with an
absolute offset and dropped-byte count; raw VT never reaches the user console
from this module. The frontend owns terminal emulation and escape policy.
All input remains explicit user terminal input and is absent from model tools.

Natural completion releases the workspace lock only after tree_quiescent and
direct-child reap. Cancel/close terminates the job and verifies the same
condition before release. Drop best-effort kills/reaps; an unknown cleanup
result detaches the native lock owner intentionally so Windows retains the
lock until the owning CLI process exits. No heartbeats grant early takeover.
No subprocess is replayed or resumed automatically after a crash.

Frontend integration must close live terminal jobs or refuse Plan activation;
new writes independently reject a current Plan policy. The module is not a
system sandbox: an explicitly approved shell retains the user's OS rights.
Launch snapshots/environment values and raw terminal output stay in memory;
they are not written to shared history or normal logs by this module.
