# Restore session permissions and keep child waits resumable

## Problem
Session re-entry resets the user's permission selection. A bounded child wait or
temporarily full model pool can become code 12, cancel healthy children, and be
mislabelled as an exhausted budget. Each assistant/tool segment repeats its
speaker heading within a single user turn.

## Capabilities
Persist local session permission selections, preserve immutable running policy,
make scheduler backpressure resumable and cancellable, and show one assistant
heading per user turn in both live and restored transcripts.

## Non-Goals
No new backend, data schema, background execution, global permission default,
untrusted-history authorization, automatic tool replay or budget increase.

The Sengoo CLI owns the fixes. Existing SQLite session locks, mode transactions,
engine submit snapshots and terminal events remain the ownership boundaries.
This extends `fix-cli-scroll-and-session-target` and existing scheduler contracts.
