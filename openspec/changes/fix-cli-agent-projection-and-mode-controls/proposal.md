# Readable agents and explicit session controls

## Capabilities

Project child-agent events into stable, bounded progress cards instead of
printing internal event JSON in the conversation. Show the effective reasoning
effort next to the selected model, using medium when the model supports it.
Cycle manual approval, automatic workspace edits and full tool approval with
Shift+Tab, and keep the selected permission mode below the composer.

The user requested this implementation. All application logic remains Sengoo.
The existing generic terminal boundary already carries Shift+Tab modifiers.

## Non-Goals

No new model-based risk classifier, backend permission bypass, cloud execution,
database migration or live paid-provider test. Plan restrictions, execution
ownership and uncertain-side-effect pauses remain authoritative.

## Ownership

The agent projection owns only child-event presentation. The permission core
owns policy and host admission; the effort boundary owns capability-aware
request settings. The integration owner owns TUI keys, frontend wiring, public
console acceptance and installed candidate validation. Existing background,
shared-state and request-recovery contracts remain in force.
