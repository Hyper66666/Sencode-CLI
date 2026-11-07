- [x] Storage owner: reproduce and repair request-evidence replacement; isolate mode reads/writes and preserve model/permission/branch/import compatibility (`request_state`, `session_target`, `session_permissions`, `project_history`).
- [x] Controller owner: fenced recovery of trailing calls using exact ledger evidence without execution (`controller_recovery`, `cancel_resume_host`).
- [x] Diagnostics owner: preserve request-state failure attribution (`execution_diagnostics`, `cancel_resume_host`).
- [x] Integration owner: final candidate regressions, package, local installation and rollback verification.

Evidence and remaining qualification boundaries: [verification.md](verification.md).
