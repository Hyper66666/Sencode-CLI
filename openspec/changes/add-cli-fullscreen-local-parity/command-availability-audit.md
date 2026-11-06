# Command availability and remaining umbrella gates

Audit owner: UI child, with implementation ownership retained by the existing
umbrella owners. Recorded 2026-11-04 against working-tree source based on Sencode
`a468086401a0d19077b5cf0b6aea3ecff0f04c9a`. This is a dependency/evidence note;
it does not introduce a second implementation owner or mark tasks complete.

Detailed design: `sencode-cli/docs/command-availability-next.md`.

## Keep these requirements open until their named scope is verified

| Existing task / requirement | Verified subset | Unfinished scope or final evidence |
| --- | --- | --- |
| P1 shared registry / Registry-driven completion | Fullscreen `/` and `/help`, aliases, two-step Enter, fixed arguments, references and disabled-menu dispatch have tests | Scrolling help remains hardcoded; host-specific reasons and runtime capability availability need one projection. `/model` label overstates exposed reasoning controls |
| P1 fullscreen / restore | Centered monochrome view, streaming composer, Markdown subset, keys/read/queue and real-console fixtures pass independently | Final combined source/compiler/application gate and installation must use one candidate; do not substitute earlier `9e3d...` or `0c9087...` evidence |
| P2 negotiated runtime policy | Native enforcement and managed capability limitations are explicit | Strict managed Plan, controlled children and exact request/token budget support cannot be inferred from chat/streaming success |
| P3 PTY/media/IDE | ConPTY owner and new safe pane have targeted tests; main fixture reproduced then verified the canonical CMD-path fix | Pane claim/cleanup/exit-code audit changes require final rerun. Images/PDF input, clipboard media, LSP/IDE and full terminal emulation remain separate scope |
| P4 MCP / extensions / memory | Native stdio tool subset and top-level management; read-only config/doctor/instructions exist | Fullscreen `/mcp` and `/diff` are disabled. Hooks/plugins, remote MCP/OAuth/resources/prompts/elicitation, learned memory and search integration remain unavailable |
| P5 workflows / background attach | Refer to the background/job child's explicit public-command evidence for its actual subset | Do not close teams, task dependencies, monitors, loops or durable interactive attach from basic job primitives or one foreground child test |
| P6 delivery / matrix reconciliation | Earlier local installations and alias startup have evidence | New combined package, clean Windows VM, desktop installer/handoff, required other-platform/toolchain checks and rollback are separate gates. Human trials remain deferred by the user |

## Documentation reconciliation after the candidate passes

- `README.md` currently omits `/keys`, `/read` and `/terminal`, and still excludes
  interactive console applications. Replace this with the exact bounded Windows
  user-terminal behavior and tested VT subset, without promising arbitrary TUI
  application compatibility.
- `docs/local-parity.md` still says the TUI terminal pane is pending. Update only
  after the final combined candidate passes; keep media and IDE work pending.
- `docs/user-terminal-jobs.md` describes the independent owner and correctly
  separates frontend evidence. Add the safe-pane child and final evidence rather
  than treating its older owner fixture as a complete product qualification.
- User keymap/Vim/read instructions need a public entry point. Explain default
  editing, INSERT/NORMAL, Ctrl+C versus Escape, safe reserved bindings and
  read-only configuration. The implementation is a Vim subset.
- Keep exact protocol/runtime/Goal limits and unavailable commands visible.
  `/memory` reads applicable instructions; learned persistent memory is pending.

No umbrella checkbox was changed by this audit. A child completing its bounded
implementation does not complete a mixed phase containing other capabilities.
