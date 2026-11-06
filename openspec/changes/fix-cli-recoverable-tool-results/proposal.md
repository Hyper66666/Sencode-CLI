# Recover ordinary tool errors without stopping the agent

## Problem

A `list_directory` call with a rejected absolute path produces status 7.
The controller durably writes an error result, then returns a host error anyway.
The tool batch stops and the UI pauses its queue before the model can correct
the path. Missing files and process-backed read failures share that behavior.

## Capabilities

Distinguish recoverable tool results from host interruption and unknown
side-effect outcomes. Preserve source-order results and durable call-ID
deduplication in serial execution and parallel safe-read batches. Give the
model an exact error code and correction hint while keeping the permission
boundary intact. Normalize editor preflight errors only before writes begin.

## Non-Goals

No automatic retry of a tool, permission widening, model/provider failover,
schema migration, process sandbox, suppression of cancellation, or automatic
recovery of unknown writes, commands, MCP or hook side effects.

## Ownership

The controller/executor owner modifies `controller.sg`,
`controller_tool_batch.sg`, `executor.sg` and dedicated native regressions.
SQLite remains authoritative. UI projections and provider requests consume the
existing completed tool event and history result; no second state owner is added.
