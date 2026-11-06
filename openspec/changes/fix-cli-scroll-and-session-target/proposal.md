# Smooth transcript scrolling and session target memory

## Capabilities
Reduce scrolling work with bounded repaint cadence and validated viewport cell
shifts, preserve high resolution wheel input, and restore the last selected
supplier/model/thinking effort with the conversation. Implement this in Sengoo.
Leave the empty composer free of placeholder text in idle and running states.

## Non-Goals
No provider fallback, execution-policy persistence, shell changes, learned agent
memory, global model preference replacement or new database schema.

## Boundaries
The CLI owns UI input and presentation. SQLite remains authoritative; shared
session locks and cleanup checks guard target preference writes. Active requests
retain their accepted target. Project-local history carries additive metadata.
