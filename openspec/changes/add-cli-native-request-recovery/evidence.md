# Evidence ledger

Host: Windows x64, 2026-11-04. Sencode repository base:
`a468086401a0d19077b5cf0b6aea3ecff0f04c9a` with preserved local work.
Source-development compiler/runtime builds are development artifacts and do not
qualify independent installed release or live service checks.

## Pure/native fixtures

- `src/tests_request_retry.sg`: compiled and ran; retry evidence, attempt and
  delay bounds, delta/date Retry-After, pre-send I/O/timeout, unsupported TLS,
  cancellation, stream and side-effect refusal.
- `src/tests_context_compaction.sg`: compiled and ran; exact model limits,
  duplicate/invalid settings, pending and orphan tool rejection, complete
  units and verbatim retained tail, unchanged original history.
- `src/tests_http.sg`: compiled and ran; byte framing, mixed-case Retry-After,
  duplicate headers, original HTTP bounds and URL policy.
- `src/tests_protocol.sg`: compiled and ran; existing three-protocol/SSE tests
  remain green, including explicit refusal of unsupported reasoning+tools.
- `tests/engine_fixture.py target/engine_probe.exe`: passed after retry/context
  integration and the interrupted-tool/public-history repair.
- `tests/managed_fixture.py target/engine_probe.exe target/managed_fixture.exe`:
  passed after native changes; managed capability gates were not relaxed.

`tests/request_recovery_fixture.py target/engine_probe.exe` fully passed on
2026-11-04 at 19:52 Asia/Shanghai after the terminal-only observation fix. It
exercised three actual 30-second closed TCP connection deadlines, HTTP-date and
delta-seconds Retry-After, 429/5xx and nonretryable errors, bounded attempts,
backoff cancellation, no replay after send/stream, per-attempt identities and
usage provenance, Goal limits, exact-model automatic compaction, recent tool
pairs, original public transcript, restart accounting, and failed-summary
pause with the previous context checkpoint unchanged. The same rebuilt probe
passed the complete engine and managed-process fixtures.

Scope: coordinator requests and its summary/final consultation calls retry.
Parallel child and individual consultation sampling still report the first
failure; this change does not claim they retry. Their existing shared request
accounting and cancellation behavior remains validated by the original suite.

## Actual public runtime readiness

- Official pinned Codex app-server `0.144.4`: production helper passed only
  public initialize/initialized in an initially empty CODEX_HOME, verified
  version/platform/profile, then terminated and reaped the owned process tree.
  Binary SHA256:
  `a8807a3727efabbd1cc46293d5705775328533c7a9eeb6112caf5b50a644e926`.
- Repository-built Sencode ACP `0.2.102` / ACP1: production helper passed only
  public initialize in an initially empty GROK_HOME with disconnected proxy
  settings, then terminated/reaped. Binary SHA256:
  `2fe261df9bfb278d9097e4939a720757f9b9a3546fa945d5f71f17a3a56aca62`.

Neither probe logged in, created a provider session/thread, requested a model,
or read an existing user's credentials. Readiness is not a live paid-call result.

## Responses continuation gate

Attempts to fetch both official reasoning documentation endpoints failed TLS in
this environment. No current official document was retrieved. The implementation
therefore keeps reasoning+tool continuation explicitly unsupported; local Rust
examples do not substitute for public contract verification. This task remains
open and must not be reported as a completed capability.

## Defect found during long-wait integration

Repeated pending polls replaced seven fields in one JsonDoc arena and exhausted
its node bound before the network deadline. Independent ProviderJob and
EngineRequest probes isolated this to observation writes, not TLS/network error
classification. The controller now saves one terminal/error/cancel snapshot.
The unrelated `println(bool)` ABI defect was isolated and fixed in Sengoo by the
language owner with independent O0/O2 regression evidence.
