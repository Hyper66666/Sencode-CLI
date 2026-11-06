# Scrolling terminal interface and command discovery

Owners: renderer agent owns `terminal.sg` and terminal regression tests; installer
agent owns installation/command discovery and its smoke checks; I/O agent owns
consultation/MCP queued input. Root owns application integration and acceptance.

- [x] Render a compact branded welcome, workspace, selected model and session.
- [x] Render a Unicode-aware, wrapping multiline composer with resize, draft
  history, paste, cancellation and visible keyboard hints.
- [x] Show readable command results, provider/tool activity, modes and approval
  prompts without exposing terminal controls from untrusted content.
- [x] Retain bounded input during provider, command, consultation and MCP waits;
  queued text must never authorize an operation.
- [x] Keep redirected text/JSON/stream-JSON and dumb/no-color terminals usable.
- [x] Install collision-checked, owned `sen`/`sencode` command forwarders in an
  existing per-user command directory, preserving cwd and resume arguments.
- [x] Verify layout and real hidden Windows-console interactions, isolated
  external-project behavior, and installation in PowerShell 7 and 5.1 against
  the new executable. Record fresh hashes; old candidate evidence is historical.

No proprietary recovered source is used. Existing terminal behavior is the
reference; the interface remains a native Sengoo application.

2026-11-04 Windows x64 evidence: `target/acceptance/tui-final-evidence.json`
passes 14 cases / 26 steps and rechecks CLI/compiler/foundation hashes;
`target/tui-console-evidence.json` and `target/tui-installed-console-evidence.json`
pass 12 actual-console scenarios, including tall composer reflow. New package
smoke checks pass on PowerShell 7 and 5.1 (`target/install-tui-evidence*.json`).
Installed command discovery is independently verified from two external folders
with only System32 and WindowsApps in PATH; see
`target/installed-global-command-evidence.json`. These checks do not observe an
already-open user terminal's private environment or qualify a fresh Windows VM.
