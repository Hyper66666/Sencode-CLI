## ADDED Requirements

### Requirement: Explicit terminal sessions retain execution ownership
The fullscreen host MUST require fresh explicit launch approval outside Plan,
own the shared session and workspace, and release execution only after cleanup.

#### Scenario: Default cancel
- WHEN the launch interaction is dismissed or submitted without selecting approval
- THEN no child process starts and the original composer remains available.

#### Scenario: Terminal completion
- WHEN an approved terminal's output drains and its entire process tree exits
- THEN the host completes its durable ledger and releases the execution lease.

#### Scenario: Unknown cleanup
- WHEN process cleanup cannot be certified
- THEN the running ledger remains unresolved and restart cannot replay the shell.

### Requirement: Child terminal bytes cannot control the host terminal
The pane MUST incrementally parse bounded VT and UTF-8 into printable cells,
and MUST NOT forward child escape sequences or terminal side effects.

#### Scenario: Malicious control strings
- WHEN a child writes split OSC clipboard/title or DCS sequences
- THEN their payloads have no effect on the outer terminal or clipboard.

#### Scenario: Unicode and focus
- WHEN the user edits or cancels inside a live terminal pane
- THEN its UTF-8 input reaches only that terminal and the chat draft is retained.
