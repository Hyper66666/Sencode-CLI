# Local verification — 2026-11-05

Sencode base SHA: `a468086401a0d19077b5cf0b6aea3ecff0f04c9a`.
Sengoo base SHA: `d46b3f6cd8d6e770734f98edc57aa67cb931e26a`.
Both working trees already contained changes and were preserved. This application
and its two bridge source files are uncommitted. Full source hashes, host identity,
compiler identity and final artifact hashes are in `target/build-evidence.json`.
All `target/` evidence paths refer to build outputs in the source project.

Validated locally on Windows x64:

- `npm test`: 4 tests. Metadata-only import/export, legacy imports, invalid inputs,
  model bounds, duplicates, Unicode whitespace and default membership.
- `node tests/ui.mjs`: 12 browser-fixture checks with system Edge. Connection and
  model selection, discovery retaining enablement/default/vision, keyboard save,
  password masking, nested Escape, import/export, deletion confirmation and
  760/520 px layouts without horizontal overflow. No browser runtime exceptions.
- `tests/bridge_fixture.py`: 14 isolated checks against the real Sengoo executable,
  temporary schema29 SQLite, randomly named disposable Windows credentials and
  loopback HTTP. All three auth protocols, chunked Unicode models, bound/pagination,
  HTTP errors, redirects, malformed/empty/oversized bodies, idle timeout,
  invalid model catalog, unknown-field preservation and credential rollback passed.
  Default connection was confirmed by the installed CLI against that temporary DB.
- Rust debug/release builds and frontend production build passed. Regenerating
  tauri-specta bindings produced an identical SHA256.
- `openspec validate add-sencode-config --strict`: passed.
- The initial portable Windows app completed native UI selection, stored-key
  model discovery, enabling three models, default/vision changes and committed
  SQLite verification. No chat history was created. This used a system-only PATH
  and a temporary working directory outside the source tree. Exact initial hashes
  and six assertions are in `target/native-evidence-initial.json`.
- The final portable build was launched under the same isolated conditions;
  discovery reached the real loopback HTTP fixture. Manual user interaction
  changed the test connection/draft before the remaining scripted assertions.
  `target/native-evidence.json` records this rerun as **interrupted**, not passed.
  The final bridge passed the complete 14-check isolated suite separately.

Evidence scopes are distinct. Browser fixtures are not native persistence tests.
Loopback discovery is not a real provider call. The system-only PATH check is not
a fresh Windows VM. No live provider credentials, real API requests, production
configuration edits or fresh-VM installation tests were used.

The app includes its compiled Sengoo bridge and Visual C++ runtime DLL; WebView2
remains a Windows prerequisite. The bridge uses the private source-development
Sengoo candidate; this is not evidence for a public Sengoo toolchain release.
The installed CLI is unchanged (`5d0cbfca542738bb1b68a4f24c247b63b5a589190fcd53b95758c309ed31260c`).

Delivered: `D:/SencodeConfig/sencode-config.exe`, adjacent `resources/`, metadata
checksums, license notices, and `D:/sencode-config-0.1.0-windows-x64.zip`.
Desktop shortcut: `%USERPROFILE%/Desktop/sencode-config.lnk`.
No Git commit, push, public publishing or existing credential modification was performed.
