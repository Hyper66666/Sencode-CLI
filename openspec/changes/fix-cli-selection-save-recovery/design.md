# Preference save without claiming execution

The two preference writers retain the session OS lock and use one helper to
check an existing nonarchived session. The helper blocks pending cleanup, running
tool records, live meeting/fusion work, active non-SG execution and an active
record owned by this same instance. An abandoned SG execution owned by an earlier
instance is admitted only after acquiring its released OS lock and confirming no
pending work. This matches the existing native turn admission domain.

Within the same preference transaction, the safe abandoned native record is
marked inactive so shared-state ownership triggers admit the write. Ownership,
fence, execution ID, messages and tool records stay untouched. The later actual
turn claim still owns transcript recovery and advances the fence. Any write
failure rolls back both activity release and preferences. A busy preference write
returns retryable code 11; missing/archived data remains terminal. Live, unknown
tool or uncertified cleanup records cannot be released by a preference save.

Both fullscreen preference saves retain their dirty state on code 11, retry at
100 ms while continuing to service input, and wait for worker readiness. The final
save after stopping/reaping the owned worker reports a terminal failure instead
of discarding it silently. Request snapshots remain unchanged during an active
turn; the future frontend selection is saved after release.
