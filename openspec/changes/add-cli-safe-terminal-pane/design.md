# Execution and input boundaries

Only idle interactive foreground UI may request a terminal. The registry remains
disabled in generic/scrolling/headless hosts. Default approval is cancel, with
the existing fresh-input barrier. A changed launch fingerprint or Plan refuses
startup. The frontend captures literal executable/argv, no shell re-parsing.

Before launch, acquire shared session execution (preserving target), then record
a durable `user_terminal` tool claim containing the launch digest only. The PTY
owner acquires workspace exclusion. Natural exit needs a drained byte stream and
whole-tree quiescence before completing the ledger and releasing execution.
Explicit close terminates/reaps the tree. Unknown cleanup retains the running
ledger and native lock ownership; restart cannot automatically replay it.

One pane owns keyboard focus. Ctrl+Q closes/stops it, Ctrl+C goes to the shell,
and Esc returns after natural completion. No pane key reaches the composer,
menus or model. The original draft and queue remain owned by UiApp; queue dispatch
waits until the pane and launch interaction close. Plan cannot start while the
pane owns the execution. PTY environment uses the existing system allowlist.

The screen is at most 240x100 cells; reads are at most 4 KiB and input is at most
64 KiB. Partial UTF-8 and CSI/string controls are consumed incrementally. OSC
clipboard/title/link sequences and DCS/APC/PM/SOS have no effects or replies.
Only parser-produced printable cell strings enter the renderer; renderer-owned
cursor sequences are generated separately. Large CSI parameters are discarded
through their terminator. No terminal output enters model context automatically.

Monochrome cursor/erase/scroll and grapheme/wide-cell handling form the initial
VT subset. Alternate screens are cleared, without restoration of prior content.
Unsupported sequences have no host effects. Shell bracketed paste is honored;
multiline paste is refused if the shell has not enabled that mode, and paste is
bounded to 32 KiB. Resize preserves the overlapping cell grid.
