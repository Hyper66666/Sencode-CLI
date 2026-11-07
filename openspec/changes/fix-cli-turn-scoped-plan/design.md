## Scope and lifecycle

`/plan TASK` or `--plan` constrains the submitted turn. Bare `/plan` arms the
next turn in the current window. Tool continuations and children in that turn
retain the captured Plan policy until they settle. Completing or cancelling the
turn, a provider/budget/preflight failure, or a broken host clears the foreground
Plan overlay before any next queued task or user input executes. Cleanup remains
mandatory before executing follow-up work; clearing a flag does not release
leases or certify unknown outcomes.

The engine resets Plan after dispatch even on early Result errors. The persistent
stdio host takes Plan from each submit and clears it on terminal paths. The
frontend clears its overlay after result/EOF/failure and before the next input or
queue dispatch. Idle cancellation clears an armed selection. Existing /plan
approve remains a compatibility way to clear an armed selection.

## Persistence and recovery

New plan artifact metadata keeps `active=false`, adds `scope=turn` and records
historical `read_only` and path. The running immutable policy is authoritative.
Neither startup nor session switching restores historical `active=true`, including
legacy records. A crash cannot latch the next process in Plan. The artifact stays
available. Remembered manual/auto/full and command permissions are unchanged;
exiting Plan never runs a plan or grants an approval by itself.

## Verification

Native policy checks plus real execution-host and hidden-console loopback checks
cover normal completion, cancellation, provider/budget/preflight failure, queued
follow-ups, worker crash/reconnect, legacy records and explicit re-entry. Mock
provider evidence is separate from live-service or fresh-VM qualification.
