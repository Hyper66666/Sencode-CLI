# Design

Wheel deltas accumulate at line precision instead of truncating each event to a
whole notch. Scroll-only input requests a frame at most every 16 ms; typing,
cancel, resize and approvals remain immediate. Mouse movement that changes no UI
does not build a frame. Bound navigation to a full top viewport.

The renderer caches prior visible rows and only uses a VT scroll region if the
viewport dimensions and every shifted overlapping text/style/span match. Shift
the message region, repaint entering rows, then reset margins and cursor. Menu,
approval, resize, changed content and unsupported state use ordinary row diffs.
No synchronized-output mode, sleep-based animation or native application code.

Store schema-v1 `cli_target` in existing `shared_modes`, alongside the compatible
selected_connection_id/model_id session columns. It contains only connection id,
model id and effort, never credentials or policy. Save selections while idle
under the session lock; changes made during a turn are deferred until cleanup,
session switch or orderly exit. Execution metadata remains immutable while busy.
Preserve all unrelated mode fields and emit existing transactional changes.

Restore on CLI resume and in-app selection; fall back to historical session
columns for old conversations. Explicit --connection overrides the saved target;
explicit --model uses the restored connection and resets saved effort, while
explicit --effort overrides effort. New sessions inherit current/default target.
A removed saved connection remains unavailable and never silently selects another.
Branches inherit the selection; sanitized portable history retains bounded target
metadata, and root-folder rename does not change it.

Native tests verify input, cell-shift equivalence and target precedence before
qualification. Real hidden-console fixtures verify colors/layout, burst wheel
input, stream anchors, session reopen and actual loopback provider routing.

Local installation reproduced a committed update reporting failure when a live
Windows image held its renamed program backup. Defer deletion only for tracked
backup paths with access/sharing/lock errors after all publications commit.
Do not stop old sessions or swallow failed publication/rollback. The installed
payload remains checksum verified; report retained paths. An owned stdio-host
upgrade smoke verifies old-process survival, new entrypoints, normal shutdown,
and cleanup after exit. This script-only repair does not change the CLI image.
