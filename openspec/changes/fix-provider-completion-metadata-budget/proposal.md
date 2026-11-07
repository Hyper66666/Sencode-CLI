# Fix valid completion events exceeding the legacy JSON node budget

## Why
The installed CLI reproducibly rejects a valid Responses completion with 4129
nodes as parse error 10. Cumulative usage attribution crosses Sengoo's legacy
4096-node default although the answer and tool arguments are valid. Six retries
cannot repair this deterministic local parsing limit.

## Capabilities
Use existing Sengoo explicit JSON budgets at the provider event boundary, aligned
with the 1 MiB SSE event limit and a 65536-node structural limit. Distinguish
malformed JSON, resource limits and invalid event fields in safe diagnostics.
Add long-metadata continuation and standard-library cleanup regressions.

## Non-Goals
No changes to protocol selection, model defaults, permissions, tool replay,
retry count, storage schema, legacy JSON limits or native ABI. This does not
claim all failures from historical coarse logs have the same cause.

## Ownership
Integration owner: provider parser, fixtures, candidate and installation.
The adjacent Sengoo repository owns the independent JSON regression and guidance.
