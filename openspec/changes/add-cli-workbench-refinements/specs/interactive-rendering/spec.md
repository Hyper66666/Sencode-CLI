## ADDED Requirements

### Requirement: Unicode-safe workbench and recoverable requests
The workbench SHALL render Chinese and emoji model output without splitting a
UTF-8 scalar and SHALL display recoverable request failures without exiting.

#### Scenario: Greeting and later retry
- WHEN a user sends a Chinese greeting and the response begins with Chinese text
- THEN the response appears and the workbench remains ready for the next message.
- WHEN a request or instruction-file decoding fails
- THEN a contextual diagnostic is shown, the history and draft are retained and no side-effecting tool is replayed automatically.

### Requirement: Monochrome identity and phase animation
The centered home SHALL use a black-and-white dimensional SENCODE wordmark.
Thinking and context compression SHALL have distinct animated states, replacing
the static streaming label while retaining responsiveness and scroll position.

#### Scenario: Idle, thinking, compression and cancel
- WHEN the viewport changes between narrow and wide sizes
- THEN the wordmark fits without clipping the input controls.
- WHEN generation or compression is active
- THEN only changed animation rows refresh and cancellation remains available.
- WHEN the operation completes or is cancelled
- THEN no stale active animation remains.

### Requirement: Code change previews
Native file modifications SHALL display contextual source snippets with actual
line numbers, red removed lines and green added lines, before approval and after
successful application. Plain and NO_COLOR modes SHALL retain +/- markers.

#### Scenario: Safe edit and denial
- WHEN a validated edit requires approval
- THEN the preview shows its target, unchanged context and changed lines before execution.
- WHEN approval is denied or the expected content is stale
- THEN the file is not changed and no successful-applied card is emitted.
