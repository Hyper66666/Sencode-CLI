# Native request recovery gates

- [x] Establish pure retry/HTTP-date and context/tool-unit policy fixtures.
  Evidence: `src/tests_request_retry.sg` and `src/tests_context_compaction.sg`
  compiled and ran on Windows x64 on 2026-11-04. Detailed candidate evidence is
  recorded below only after the corresponding integration run completes.
- [x] Supply verified transport-before-emission evidence from Sengoo.
  Evidence: `NetByteStream.request_started` language-owner regression and real
  closed-port `tests/request_recovery_fixture.py` on Windows x64.
- [x] Integrate bounded cancellable retry with per-attempt shared accounting in
  the coordinator request path (including summary/final consultation requests).
  Parallel child/consult sampling still stops after one failed attempt.
- [x] Verify 429/5xx/connect refusal, Retry-After, cancellation, limits and no replay after streaming.
  Evidence: complete `tests/request_recovery_fixture.py` passed 2026-11-04,
  including three actual 30-second TCP connection deadlines.
- [x] Integrate exact-model/explicit-limit automatic compaction and checkpoint restore.
  Evidence: schema 2 context checkpoint and restart fixture passed.
- [x] Verify original transcript/tool pairs, pending-tool refusal, failure pause and cumulative Goal budgets.
  Evidence: pure context tests and recovery fixture including summary HTTP400,
  unchanged prior checkpoint and Goal pause.
- [ ] Confirm public Responses continuation schema and preserve opaque output items with protocol fixtures.
- [ ] Rebuild candidate and rerun native, managed and public-runtime initialize acceptance.
  Core `engine_probe` rebuild passed native/managed suites; installed candidate
  remains root-owned and is not marked complete by probe results.

Only core-owned native behavior is implemented here. Root owns the installed
candidate and public capability matrix. A pure fixture does not close a live
service or independent installation gate.
