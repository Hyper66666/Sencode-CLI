# Native CLI implementation and verification

Owner: CLI agent. The root implementation gates retain shared-state, desktop,
delivery and human trial acceptance; the module tasks below do not duplicate
those requirements.

- [x] Implement typed provider adapters and raw-byte HTTP/SSE framing in Sengoo.
  Evidence: `src/tests_protocol.sg`, `tests_http.sg`, and real four-stream
  `tests/provider_fixture.py`; each UTF-8 boundary and tool-argument fragments.
- [x] Compile the real main executable and complete an external read, exact
  patch, command, explicit/recent resume loop. Evidence: `tests/cli_fixture.py`.
- [x] Preserve Plan restrictions and exact plan-file writes, including hostile
  patch, shell and MCP attempts. Evidence: the external CLI fixture.
- [x] Preserve Goal request/token budgets, saturate counts, pause on identical
  failed verification or missing approval, and retain counts after compaction.
  Evidence: `tests_core.sg` and external CLI fixture.
- [x] Integrate asynchronous child start/list/wait/cancel with shared budgets,
  tool ledger and per-session execution state. Evidence: external CLI fixture
  plus the sibling-owned children fixture/task list.
- [x] Retain typed input while provider work runs, keep it separate from approval,
  and preserve Unicode cursor/paste boundaries. Evidence: `tests_terminal.sg`.
- [x] Implement stdio MCP initialization, pagination, bounded stderr and timeout.
  Evidence: native `tests_mcp.sg` against the Python stdio fixture.
- [ ] Complete the consolidated final run including MCP abnormal exit, oversized
  stdout, cancellation and zero native process resources.
- [ ] Complete one locked package build and all twelve CLI acceptance cases on
  one compiler identity; store source/compiler/application hashes and logs.

Reasoning-item continuation in Responses is explicitly outside the validated
text/tool subset. A reasoning turn containing tools is rejected before any tool
executes; the protocol regression verifies this boundary.
