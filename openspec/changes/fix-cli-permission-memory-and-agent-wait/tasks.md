# Tasks

- [x] Add isolated reproduction and regression contracts for pending children, permission memory and speaker grouping.
- [x] Implement locked per-session permission persistence and all resume paths; verify unsent changes, busy policy isolation, overrides, Plan and import boundaries.
- [x] Fix bounded child wait resumption and model-slot backpressure; verify healthy children finish, cancellation and real budget exhaustion remain correct.
- [x] Render one assistant heading per user turn; verify streaming, tools, notices, history, resizing and scrolling.
- [x] Build and qualify one Windows candidate; update documentation, validate OpenSpec, package, verify upgrade/rollback and update local sen/sencode without stopping existing sessions.

Evidence: `sencode-cli/docs/permission-session-verification.md`; final candidate
`sencode-cli/target/policy-wait-20261106/candidate-6/`, application SHA-256
`23e8635ba2b25b9f16f63db723c51056b09f178b4ba274d50c33b4c631c98d4c`.
