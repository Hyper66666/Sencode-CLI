# User terminal pane

In the fullscreen workbench, use `/terminal` or `/terminal powershell` to open
Windows PowerShell, or `/terminal cmd` for Command Prompt. `/term` is an alias.
The first Enter completes a menu choice; submit the completed command separately.
An exact launch preview then defaults to Cancel and requires fresh approval.

The pane is an explicit user action. It is unavailable in Plan, during a model
turn, in child agents, in redirected output, or without ConPTY. It does not grant
model tools permission to launch interactive shells. Shell commands use the
current Windows account and can modify the workspace; they have no OS sandbox.

Ctrl+C is sent to the shell. Ctrl+Q closes the pane and terminates its owned
process tree. After a natural shell exit, Esc returns to the original draft.
The session and workspace remain held until the tree is quiescent and cleanup
is recorded. Failed cleanup remains unresolved and prevents normal handoff.
The model queue stays paused while the pane or launch confirmation is open.

Output is decoded and rendered by a bounded Sengoo cell screen, never forwarded
as raw terminal escape sequences. Clipboard/title/link OSC and DCS/APC/PM/SOS
strings are consumed. The initial monochrome VT subset supports cursor movement,
erase, wrapping, scrolling, Unicode clusters and resize; it is not a full xterm.
Switching an alternate screen clears it without restoring prior screen contents.
Programs that require unsupported terminal responses may not work correctly.

Input queues are bounded to 64 KiB. A paste is limited to 32 KiB; multiline paste
requires bracketed-paste support from the shell. The pane never adds its terminal
contents to model context or conversation history automatically. The durable
tool ledger stores a launch fingerprint and cleanup status, not typed commands.

Native ownership tests and the actual-main hidden Windows console fixture are
separate gates. The latter covers approval barriers, Chinese output, real resize,
control-string isolation, Ctrl+C, child/grandchild termination, CMD natural exit
and console restoration. See the matching candidate verification for hashes.
