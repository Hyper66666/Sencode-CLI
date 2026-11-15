# Verification

- [x] Reproduce the strict idle code-7 failure on an abandoned no-tool native record (`target/selection-save-20261116/recovery-run.log`).
- [x] Verify both preference writers persist while releasing only stale activity and retaining the old execution/fence; failed preference writes roll activity and preferences back.
- [x] Verify live owner, cleanup-required, foreign-engine, running-tool, missing and archived cases reject (the same native recovery gate).
- [x] Verify the original target/permission persistence tests and frontend regression scenarios (qualified product SHA `a794de2c...12be3`: model/scroll console 33 checks, permission console 28 checks).
- [x] Validate the child and all OpenSpec changes strictly (41/41 at registration checkpoint); record exact local evidence.
