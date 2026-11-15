# Selection persistence recovery

Windows x64 development verification, 2026-11-16. Base revision:
`dc3a3c60c481ab520ab6f4f48e32bd17ccd84ee3` plus the integrated working tree;
this is not a released-build claim.

## Reproduction and native gate

`src/tests_session_preference_recovery.sg` starts a real native execution, verifies
that both its own and another client cannot change preferences while its lock is
held, and then releases that lease without finalizing the execution. The old
`session_idle` predicate still rejects the resulting no-tool SG record with code
7. The new preference admission allows both saves after the released lock.

The same test confirms execution/fence identity preservation, stale activity
release and transactional rollback through a temporary SQLite failure trigger.
Cleanup-required, active foreign engine, running tool (including inactive parent),
current-instance activity, archived and missing session cases remain blocked.

Targeted build/run logs and binaries live in
`target/selection-save-20261116/`. The recovery native gate and both original
`session_target` and `session_permissions` regressions passed all assertions.
`evidence.json` records the source, tool, binary and terminal-log hashes. The
combined frontend gates passed against qualified product SHA-256
`a794de2c7bbe5c38262153ea14377124f4becb62c2d5c3aef966190789412be3`.

The compiler is the pinned
`D:/Sengoo/target/agent-conditional-compiler/bin/sgc.exe`, source-development mode,
`-O 0 --force-rebuild`. The clang binary at its moved Codex-local toolchain path
has the original verified SHA-256 `56ef1abd0df11a3b1b77822193e927c6345078c24511567ae10b3afd803d03a3`.

## Frontend regression coverage

`tests/scroll_target_fixture.py` and `tests/session_policy_wait_fixture.py` now
inject the same abandoned native state into their isolated fixture databases.
They exercise actual model/permission selection, pending persistence and the
absence of the screenshot's save-failure notices. Both were executed serially
against the source-frozen qualified product in hidden Windows consoles:

- `target/media-selection-20261116/scroll-target-qualified.json`: 33 checks passed,
  including abandoned-native-model-selection-has-no-save-notice.
- `target/media-selection-20261116/session-policy-wait-qualified.json`: 28 checks
  passed, including abandoned-native-permission-choices-persist-without-save-notices.

The first integrated candidate's scroll gate failed when the independent media
preflight incorrectly rejected extensionless plain prompts. Its 23 passing checks
and terminal failure remain in `scroll-target.json`; that candidate is not a pass.
The media issue was repaired before the qualified product above was rebuilt.

The child validates strictly. All OpenSpec changes validated strictly at the
41-item checkpoint while the independent media-path fix was also registered.
