# Asynchronous child and consultation evidence

Owner: scheduler/network agent. Host: Windows x64, 2026-11-04, clang 19.1.7.
Sencode baseline `a468086401a0d19077b5cf0b6aea3ecff0f04c9a` and Sengoo baseline
`d46b3f6cd8d6e770734f98edc57aa67cb931e26a`; evidence uses the working-tree
candidate above these baselines, not an immutable release SHA.

- [x] Implement pure Sengoo scheduler with defaults 4 global/2 per connection,
  canonical cwd writer FIFO, one-level authority, stable ids, parent wait,
  cancellation and once-only root request/usage accounting.
- [x] Run `sgc --runtime-mode source-development run src/tests_scheduler.sg
  --force-rebuild -O 0`: all assertions passed after compiler short-circuit fix.
- [x] Implement actual parallel three-protocol consultation, independent reports,
  shared Goal accounting, read-only tool rejection and explicit cancellation.
- [x] Build `src/tests_consult.sg --force-rebuild -O 0` and run
  `python tests/consult_fixture.py target/tests_consult.exe`: passed, including
  real 4/2 concurrency, five requests/125 tokens, raw Unicode fragmented every
  three bytes, HTTP 500 isolation, denial, cancel, budgets and zero resources.
- [x] Implement `children.sg` start/list/poll/wait/cancel plus host tool claims,
  independent contexts, filtered authority, events and canonical cwd permits.
- [x] Build `src/tests_children.sg --force-rebuild -O 0` and run
  `python tests/children_fixture.py target/tests_children.exe`: passed with real
  4/2 network concurrency, five independent Unicode reports, shared budgets,
  real read_file continuation, denied write/spawn/plan, approved file writes,
  writer queue, call-id checks, cancellation and zero handles/workers.
- [ ] Root integrator verifies controller entry points, shared-store persistence,
  final packaged executable and release compatibility. Module fixture results
  are not evidence of these separate integration gates.

Child management is bounded to 32 captured tasks and 256 pending host events;
hosts must drain events after polling. Wait accepts at most 1000 ms per call and
never bypasses host permission or executes pending tools itself. The fixture
uses synthetic credentials and an isolated temporary workspace outside both
source repositories. No external provider credentials or release publication
were used. Linux/macOS or installed-package success is not claimed.
