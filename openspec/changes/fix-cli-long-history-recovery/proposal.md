# Preserve long CLI histories and resume compacted contexts

## Problem

The public history query returns only the first 1000 rows. Newer messages
silently disappear from callers, and a valid compaction checkpoint whose
absolute `messages_seen` exceeds 1000 fails to resume. Later compaction also
records the truncated array length as its watermark. Many tiny messages can
reach the model's structural ceiling without triggering byte-based compaction.

## Capabilities

Provide strict complete history, count, absolute range and complete tail
queries with explicit resource admission. Provide a separate bounded recent
projection with total/offset metadata for UI callers. Resume canonical model
context from a validated checkpoint plus every newer public row. Compact
automatically under message-count pressure and retain absolute watermarks and
cumulative request/token budgets.

## Non-Goals

No unbounded in-memory history, schema migration, runtime ABI change,
provider-native history substitution, silent context clipping, replay of
uncertain tools or automatic reconstruction of missing old summaries. An old
oversized session without a valid checkpoint remains readable through bounded
public ranges, but requires a new session for model execution.

## Ownership and dependencies

This change owns `state.sg`, `controller.sg`, dedicated native state/context
tests and the state/context contract below. The integration owner separately
owns wiring existing frontend/engine/command views to the recent UI API and
the final executable. This change does not duplicate TUI timeline, renderer,
pending-queue or tool-error recovery requirements. SQLite remains authoritative;
model requests remain inside the existing fenced execution owner. Existing
bounded JSON APIs and compaction schema 2 are reused without format changes.
