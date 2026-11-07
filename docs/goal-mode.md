# Goal acceptance

Start with `/goal TASK` or `sen --goal "TASK"`. You do not have to supply
`--check`: the model chooses meaningful acceptance commands and sends them in
`finish_goal.checks`. The host executes them and completes the Goal only after
all checks succeed. A claim in the model's answer does not mark it complete.

Model-proposed commands use Bash by default. The model can explicitly choose
PowerShell or cmd with `finish_goal.shell`. Existing `--check COMMAND` checks
keep their PowerShell behavior and take precedence over model proposals.
The model sees configured checks and cannot replace failed checks with weaker
ones. Accepted commands and their origin/shell are saved for `/goal resume`.

Manual and automatic-file-edit modes ask for command approval and show the
exact checks and interpreter. Full access, or explicitly authorized commands,
allows them to run. Plan still blocks acceptance command execution. Denying
approval pauses the Goal and does not run a command.

Failed checks return their output so the model can fix the project and verify
again. Two unchanged failures pause the Goal. Missing verification facilities,
timeouts and cancellation also stop it, with distinct diagnostics. `/goal resume`
explicitly continues using saved checks and cumulative request/token budgets.
Ordinary messages do not silently resume it. Uncertain tool/process outcomes
still require inspection and cannot be automatically replayed.

Model-selected acceptance is the model's chosen test coverage; the host verifies
the actual command results. Use `--check` when you need specific mandatory tests.

The input footer keeps colored permissions and focused controls. `/help` lists
commands and `/keys show` lists key bindings. Readiness labels and full shortcut
lists are hidden from the idle footer. Approval and selection controls take
priority when open.
