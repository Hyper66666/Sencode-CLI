# Tasks

- [x] Implement independently owned launch snapshot/approval and workspace cwd guard (`sgc check src/pty_session.sg`, matching development toolchain).
- [x] Implement cleared/allowlisted environment, shared write lock, bounded 256KiB VT bytes and explicit user I/O.
- [x] Verify natural exit, surviving descendants, cancel and Drop lock lifetime, plus cross-process retained lock on unknown cleanup (`tests/pty_session_fixture.py` against standalone Sengoo test, Windows x64, passed 1.84s).
- [x] Verify Plan/unapproved/stale requests, real junction/escape paths, >500KB bounded display and fake provider-secret noninheritance in the same isolated fixture.
- [x] Document public module integration and Windows-only evidence; this change strict passes. Full Windows validation was run: 22/25 pass; existing add-fusion-selection, add-git-workspace-management and add-grok-desktop-backend fail unrelated long-requirement/target-spec checks and remain unchanged.
- [ ] Integrate the module into the TUI with explicit approval (owner: root; separate application gate).
