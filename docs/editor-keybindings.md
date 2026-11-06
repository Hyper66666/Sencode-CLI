# Composer keys and reading focus

`/keys` opens the editor picker; `/keys default`, `/keys vim`, `/keys show` and
`/keys reset` are explicit shortcuts. Reset affects the current process and does
not edit a configuration file. Enter in a command menu completes the command;
a separate Enter submits it. Configuration applies only to the composer, after
approval and overlay focus handlers have had priority.

The optional user file is `%APPDATA%/Sencode/cli-keybindings.json`. Set
`SENCODE_KEYMAP` to explicitly select another file. The application reads this
file without creating it. It accepts at most 64 KiB and 64 bindings. Invalid or
ambiguous configuration displays a warning and retains safe built-in defaults.
Unknown fields, duplicate fields including escaped equivalents, duplicate keys
and reserved keys are rejected.

```json
{
  "version": 1,
  "mode": "vim",
  "bindings": [
    {"key": "alt+b", "action": "word_left"},
    {"key": "alt+f", "action": "word_right"}
  ]
}
```

Allowed actions are `left`, `right`, `word_left`, `word_right`, `line_start`,
`line_end`, `delete_backward`, `delete_forward`, `delete_word_backward`,
`delete_word_forward`, `delete_to_line_start` and `delete_to_line_end`. Chords
are Left/Right/Home/End, Ctrl+Left/Right and permitted Ctrl/Alt letter chords.
Submission, approval, cancellation, exit, paste and queue-control keys cannot
be reassigned. A keymap cannot synthesize a command or authorize an operation.

The Vim subset starts in INSERT. Esc enters NORMAL; `i`, `a`, `I`, `A` return
to insertion. NORMAL supports `h/j/k/l`, `w/b`, `0/$`, `gg/G`, `x`, `D`, `dd`,
`dw`, `cw` and `u`. Undo is bounded to 32 snapshots / 1 MiB. Editing respects
Unicode grapheme boundaries. This is a composer subset, without Vim command
line, macros, registers or a full modal editor. Ctrl+C remains cancellation;
Enter remains explicit send/save. Return to INSERT before composing `/` commands.

`/read` transfers focus to transcript browsing while retaining the composer
draft and cursor. New streamed output keeps the reading anchor. Enter does not
submit, and automatic queued-message dispatch waits until reading focus closes.
Esc or `q` returns to the composer; an incoming approval still takes precedence.
