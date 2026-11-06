# Native hook workers (implementation candidate)

This P4 slice is being implemented behind host capability gates. Installed
availability is not implied by this document. The native worker contract and
acceptance matrix live in `../openspec/changes/add-cli-native-hook-workers/`.

A local manifest describes one precompiled Sengoo executable. Registration is
disabled by default; enabling records reviewed hashes. Every actual invocation
still needs a fresh approval. Plan, read-only children and unattended calls do
not start workers. The worker has the user's OS access; this is not an OS
sandbox. No automatic shell, script execution or package download occurs.

```json
{
  "schema": 1,
  "id": "review-guard",
  "version": "0.1.0",
  "language": "sengoo",
  "protocol": "sencode.native-worker/1",
  "executable": "review-guard.exe",
  "sha256": "REPLACE_WITH_64_LOWERCASE_HEX_DIGITS",
  "timeout_ms": 5000,
  "before_tool": ["write_file", "apply_patch"],
  "after_tool": ["read_file"]
}
```

`continue` is neutral: the parent operation still follows ordinary permission
rules. `block` prevents only a before-tool operation. After hooks cannot undo
or relabel the parent result. Unknown tool outcomes never launch an after hook.
Worker output is untrusted data; it cannot change permissions or instructions.
Host tool/model calls are unsupported in this first slice. A minimal protocol
helper/example is not a complete extension SDK.

Candidate management commands use the same native registry:

```text
sen extensions list
sen extensions inspect WORKER_ID
sen extensions add C:\absolute\path\sencode-worker.json
sen extensions enable WORKER_ID
sen extensions disable WORKER_ID
sen extensions remove WORKER_ID
```

`add` records a disabled entry. `enable` presents the manifest and executable
hashes for trust review; the explicit management-only `--yes` can record that
review in automation. It never supplies a later launch approval. Listing and
inspection do not create a missing worker registry, spawn processes or discover
repository executables. Re-register changed bytes and review their new hashes.
Plan rejects management mutations.

Only `read_file`, `list_directory`, `search`, `find_files`, `write_file` and
`apply_patch` subscriptions exist in schema 1. Executables, manifest files and
their ancestors are pinned during approval and process lifetime on supported
Windows local fixed disks. Other filesystem types remain unavailable. The
original tool obtains its own permission and write permit after before hooks
complete; a worker cannot grant either. After-hook failure preserves the saved
parent result and pauses continuation. Cleanup uncertainty retains process,
image and workspace guards and marks session recovery as requiring cleanup.
