# Interrupted-turn continuation verification

## Baseline and reproduction

- Host: Windows x64, `DESKTOP-FUAQMFB`, 2026-11-07.
- CLI revision: `b2b85ef2c8f369f2fd69ef8729ab420cc420959a`, with preserved local changes.
- Sengoo revision: `86c6f87975646b91c9cf2d7d069ac06ee4243b9b`, with preserved local changes.
- Compiler SHA256: `cc280b3bf0ec0bf17650b0745500c72e205ee2d2073af8ea7ed552045570f1b0`.
- Synthetic reproduction: 134 request-attempt entries and unrelated state
  reproduce request completion failure 10 with the original replacement code.
  The old JSON arena retained the replaced branch while copying its replacement.
  A response could already be persisted, leaving calls without public results;
  the following strict context check then failed with 12.
- Original reproduction: `target/cancel-resume-20261107/repro-before.json`.
  Reproduction binary SHA256:
  `db9483c2031dee33c24ada34e45929a95b6db12c65bc77f1fc26917ed6c4e606`.
  Original state-source SHA256:
  `5ccb6b49955115e5e552fd5b890ceb898186f389f19b19c7c526911208ae91c2`.

## Changes verified

State members are projected and transactionally patched in SQLite. Request
updates no longer copy either the old branch or all unrelated mode fields into
one Sengoo JSON arena. Tests include independent 2200-element fields, remembered
models/permissions, branches, a full 256-entry journal and stale fences. Import
projects the existing allowed metadata and retains its permission restrictions.

At failed-turn cleanup and before a new ordinary turn, the execution owner
validates all trailing unresolved calls before writing repair records. Exact
completed ledger results are restored. Never-admitted calls receive truthful
not-executed results and reserved IDs. Running, mismatched or uncertain results
block recovery. History queries remain strict read-only operations. Request
evidence persistence failures retain their own diagnostic category.

## Reference review

The local reference trees are excluded from the product repository. The relevant
implementation is rewritten in Sengoo; no native agent logic was added.

- Claude Code snapshot: `restored-src/src/query.ts`, lines 1011 onward, drains
  remaining tool results after abort; `services/tools/StreamingToolExecutor.ts`
  generates interruption errors for queued tools; `utils/messages.ts`,
  `ensureToolResultPairing`, validates pairs before subsequent API requests.
- Grok Build: `crates/codegen/xai-grok-sampling-types/src/conversation.rs`,
  `repair_dangling_tool_calls_with`, restores only unanswered calls;
  `crates/codegen/xai-chat-state/src/actor/mod.rs`, lines 323 onward, keeps
  queries pure and repairs at write boundaries before building requests.
- Grok Build's `live_cancel_after_partial_tool_results_repairs_remaining` and
  chat-history integrity tests cover partial completion and the duplicate-result
  hazard of repairing still-live tools. Sencode additionally requires fenced
  ownership and exact durable completion evidence before restoring a result.

## Candidate

The final internal O2 candidate uses `source-development` runtime mode and is
not a release-qualified public build. Build input hashes cover 538 CLI, compiler,
runtime, standard-library and SQLite source/configuration files. Compilation
confirmed all recorded inputs and the compiler remained unchanged.

Candidate SHA256:
`a97bc2551b25aedeca64d7d2e5b50a43125e38e0aff4b57b469b1b5942d33242`.
Build evidence: `target/cancel-resume-20261107/candidate-2/build-inputs.json`
and `build-result.json`.

## Final execution and installation

- `native-v2-evidence.json`: all 9 suites / 18 compile-and-run steps passed:
  `request_state`, `controller_recovery`, `execution_diagnostics`,
  `controller_tool_batch`, `state`, `long_history_context`, `session_target`,
  `session_permissions`, `project_history`. Portable-history checks include
  importing allowed metadata above the aggregate node limit and retaining
  duplicate-origin rejection.
- `production-v2-evidence.json`: all 8 suites passed against the candidate hash:
  `cancel_resume_host`, `engine_host`, `responses_tools`, `plan_turn_host`,
  `goal_acceptance_host`, `request_recovery_host`, `session_policy_wait`,
  `project_history_public`. The dedicated cancellation fixture passed 24 checks
  across Chat Completions, Responses and Anthropic Messages, with 21 loopback
  requests, no provider-validation errors and all 3 synthetic credentials removed.
- Final evidence is under `target/cancel-resume-20261107/`; the detailed
  production fixtures are in `target/acceptance/20261107-202414-445-30dbad6b/`.
- `candidate-2/final-gates.json`: candidate, compiler, build/acceptance source
  hashes and the installation-smoke checks agree; no recorded inputs changed.
- Package:
  `target/packages-cancel-resume-20261107-v2/sencode-cli-0.1.0-dev.0-windows-x64.zip`.
  Archive SHA256:
  `82e8a492b4063579b77c718e220edeebf7dfcacde44a27b40e36c26020dc7c8e`.
  It includes the existing pinned runtimes, ripgrep and redistributable DLL.
- `candidate-2/install-smoke.json`: both aliases passed in an isolated Unicode
  project with a restricted PATH; covers bare startup, resume, running-image
  upgrade, locked-alias rollback and modified-payload rejection.
- `candidate-2/local-install-evidence.json`: installed to `D:/SencodeCLI`;
  15 payload hashes and all 6 direct/bare/forwarder entrypoints passed. User and
  process PATH stayed unchanged; no pre-existing user process was stopped.
- The previous goal/footer package is retained and every rollback payload was
  checksum-verified. Previous executable SHA256:
  `834c2719dcfd9014beab9840dbf3f6ed39b3ee975dbe31cf9bc5c0091b66e844`.
- OpenSpec strict validation: this change passed; all 29 current changes passed.
  `git diff --check` passed. No Git commit, push or public release was performed.

Existing running CLI processes retain their old image. Exit and restart in the
project with `sen -c` to use this candidate and let its fenced next-turn recovery
reconcile an affected trailing batch. Recovery never runs an old unclaimed call.

## Scope

Fixtures use isolated projects, databases, real CLI host processes, Bash
side-effect sentinels and loopback providers. Synthetic credential entries are
deleted after testing. No live paid-provider call, user-database mutation or
fresh-Windows-VM qualification is claimed. User-history contents and credentials
are not included in checked-in evidence.
