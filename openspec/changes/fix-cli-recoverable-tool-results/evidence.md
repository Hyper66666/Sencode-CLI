# Local controller recovery evidence

The source tree is a dirty Windows development candidate. Exact full Git HEADs,
compiler/binary/source hashes, host and log hashes are recorded in
`sencode-cli/target/controller-recovery-evidence.json`; no release SHA or
untested-host qualification is claimed.

- `controller-recovery-before.log`: the dedicated original controller returned
  raw status 7 and aborted on the first rejected absolute `list_directory` path.
- `controller-recovery.log`: updated native controller passes both normal PATH
  and empty PATH in separate temporary databases. Checks include a corrected
  new directory call, cached old-ID error with changed arguments, missing and
  invalid-UTF-8 reads, no-write patch preview rejection, ordered read batches,
  settled Git failure and missing-Git job admission, durable unknown-outcome
  no-replay, pending cancellation and no retained process resources.
- `controller-batch-recovery.log`: existing real-process safe-read concurrency,
  read/write/read barriers, durable replay, duplicate rejection and hook serial
  admission still pass against the updated production modules.
- `controller-recovery-openspec.log`: this change passes strict validation.
- `controller-recovery-openspec-all.log`: global validation ran and reports
  33 passing changes and three existing failures in `add-fusion-selection`,
  `add-git-workspace-management` and `add-grok-desktop-backend`. Those unrelated
  long-requirement/delta issues are not counted as successful checks.

The tests make no provider requests and access no user credentials. Temporary
files are inventoried and removed individually; directories are removed only
when empty. Controller probes are distinct from the independent final-main
provider and terminal fixture owned by integration, which must supply its own
candidate hash and execution evidence.
