- [x] Establish stable identity and scoped attached-SQLite capture.
- [x] Verify legacy adoption, live writes, rollback and exclusion of other projects.
- [x] Verify Unicode directory rename and missing-catalog recovery.
- [x] Verify existing-original, existing-catalog, active-owner and schema conflicts.
- [x] Verify stale-row preservation, scoped session moves/deletes, exact schema
  and both JSON parsers' role interpretation (60 native regression checks).
- [x] Verify public CLI startup/resume and streaming against one frozen candidate.
- [x] Package and verify installed bare commands from a renamed external project.
- [ ] Qualify coordinated desktop portable-write integration and power-loss recovery.

Frozen native evidence: `sencode-cli/target/acceptance-project-history-native-frozen2.json`
and `sencode-cli/target/worktree-tui/project-history-evidence.json` (60 checks).
The initial `target/project-history/native4.log` is historical, not the hardened
candidate's acceptance. Public, installation and desktop evidence are distinct
gates.
