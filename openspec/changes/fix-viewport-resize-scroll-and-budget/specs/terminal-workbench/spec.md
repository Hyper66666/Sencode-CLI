## ADDED Requirements

### Requirement: Geometry-safe fullscreen recovery
The workbench SHALL redraw all rows after invalidation and recover from rapid
resize/fullscreen/minimize transitions without retaining a stale frame cache.

#### Scenario: Repeated or same-size viewport invalidation
- **WHEN** a viewport is invalidated or geometry changes during a frame
- **THEN** the next settled frame reconstructs header, transcript and composer completely
- **AND** reading anchor and draft survive and unchanged settled frames produce no writes

### Requirement: Long-history scroll and jump to latest
Wheel processing SHALL remain responsive with retained long histories and show
a centered muted downward triangle in the composer gap while scrolled up.

#### Scenario: Jump while streaming or idle
- **WHEN** the user clicks the visible triangle while reading older messages
- **THEN** the workbench immediately follows the current bottom and hides the triangle
- **AND** the click neither submits, approves, expands a tool nor modifies the draft

#### Scenario: Long-history viewport performance
- **WHEN** a long transcript is scrolled at 80, 120 or 160 columns
- **THEN** only overlapping/exposed viewport rows require terminal updates
- **AND** measured wheel-to-visible-update p95 is below 50 ms on the recorded Windows host

### Requirement: Workspace header
The left header SHALL display the current workspace path beside SENCODE in
place of BUILD, fitting independently from the current model and effort.

#### Scenario: Narrow viewport and long Unicode workspace
- **WHEN** the workspace path cannot fit beside the model
- **THEN** the path is safely clipped while the selected model and effort stay visible
- **AND** Plan/read/Vim state remains accessible without rendering BUILD
