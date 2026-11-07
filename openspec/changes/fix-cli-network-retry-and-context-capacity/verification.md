# Local candidate verification —2026-11-07

Host DESKTOP-FUAQMFB, Windows x64. CLI baseline
`b2b85ef2c8f369f2fd69ef8729ab420cc420959a`; Sengoo baseline
`86c6f87975646b91c9cf2d7d069ac06ee4243b9b`. Both trees contain preserved
uncommitted work. Compiler SHA256
`cc280b3bf0ec0bf17650b0745500c72e205ee2d2073af8ea7ed552045570f1b0`.

Candidate/evidence root: `target/network-context-20261107/`.
`candidate-final/build-inputs.json` captures539 source/compiler/runtime inputs.
Use its build result and final gate/installation manifests for exact executable
and package hashes; prior candidate evidence is retained separately.

Final executable SHA256:
`cbeae71c85c98d0bf0eef26c6d56b386e5c4d483cc352ec9daea00d4b9d5bfb0`.
Archive SHA256:
`9aab85df6b7c95e422202c78a023399e4e06a3ba507f034820608e8efed90164`.
Native evidence passes8 suites/16 build-run steps; final production evidence
passes7 real-host suites on that executable. Final console input-visible
p95=37.3166ms across40 samples with four active SSE streams.

`candidate-final/final-gates.json` confirms all source/test/compiler hashes
and the final executable match. `candidate-final/local-install-evidence.json`
records15 installed payloads,6 checked entrypoints, unchanged PATH, preserved
pre-existing user processes and verified rollback. Both `sen` and `sencode`
now resolve to the candidate. Existing processes continue their old image
until exit. Rollback is the cancel-resume-v2 package with executable SHA256
`a97bc2551b25aedeca64d7d2e5b50a43125e38e0aff4b57b469b1b5942d33242`.
No user database, credential, proxy or certificate setting was modified.

Verification scope:

- Native suites: context_compaction, request_retry, execution_diagnostics,
  tui_timeline, provider_media, long_history_context, media_transport,
  image_request. Rich history exceeds4096 nodes with282 messages; all three
  encoders retain the newest tool unit and131072-token output cap. Rich and
  1900-row checkpoint scenarios execute two real loopback summaries, restore
  exact canonical context and preserve public rows/cumulative budgets.
- Output cap/override and80% crossing checks, failed-reduction resource cleanup,
  default legacy constructors, complete tool-unit and byte-bound refusal.
- Actual engine fixtures: request_recovery_host, cancel_resume_host,
  responses_tools, engine_host, plan_turn_host, goal_acceptance_host, fullscreen.
  HTTP502 exhaustion makes six attempts/five retry events; TLS-abort fixture
  captures six ClientHellos without application HTTP emission. Certificate,
  partial-stream and ambiguous-send paths do not gain unsafe replay.
- Three protocols pass24 interruption/state-recovery checks. Plan and Goal
  regression fixtures retain permissions, acceptance and cumulative budgets.
- Real hidden Windows-console readback covers25 fullscreen checks, including
  80/120/160 columns, continuous input and four active SSE streams. The first
  candidate run measured input-visible p95=40.9411ms (40 samples, max48.4375ms).
  Final measurements are retained in the production evidence's fullscreen.json.
- Three-protocol large-image captures exceed1.57MB, retain exact original hash,
  preserve system identity and neither mutate nor copy the original image.

The evidence is from synthetic isolated projects, disposable databases, local
HTTP/TLS fixtures and actual Windows console APIs. It does not prove external
provider availability or fresh-VM installation. Managed official runtime
capacity/recovery is controlled by that backend and is not redefined here.
OpenSpec strict validation passes30 CLI items and71 Sengoo items.

Sengoo's independent JSON evidence is
`D:/Sengoo/target/network-context-20261107/json-evidence.json`. Its normal native
and public-wrapper tests pass. The ASan run exits0 with the pre-existing LLVM19
Windows interception warning; clean sanitizer qualification is not claimed.

The image fixture previously omitted the engine's required system entry;
its corrected fixture now validates identity plus the user image for all three
protocols. No production engine validation was relaxed to accommodate it.
