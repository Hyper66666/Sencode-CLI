# Evidence scope

Measured on `DESKTOP-FUAQMFB`, Windows x64, 2026-11-04. Repository baseline HEAD
is `a468086401a0d19077b5cf0b6aea3ecff0f04c9a`, with existing uncommitted work.
The files and binaries below identify the tested snapshot, independently of
that baseline. Development used explicit `source-development` runtime mode;
these are local verification artifacts, not a public release or cold install.

The previously installed `9e3d4980aefd5e221663d764e583d42983cd3b32668517e7e7e66cfc100b154a`
candidate was preserved. New binaries were written only to
`sencode-cli/target/ui-editor/`.

## Native checks

The latest schema/Vim test and UiApp integration test built and ran successfully
with the rebuilt compiler identified below. They cover reserved inputs, atomic
keymap rejection, duplicate/escaped JSON members, Unicode graphemes, incomplete
operators, literal paste, bounded undo, deletion-first INSERT sessions, two-step
Enter, fullscreen capability gates, approval and picker priority, queue focus,
reading anchors including stream completion, draft/cursor preservation and
unchanged default-mode Escape cancellation.

The independent reading module also built and ran successfully. Earlier in this
verification pass, the existing commands, terminal, fullscreen UI, reference /
queue input and Markdown native suites passed. Subsequent editor-specific audit
fixes were rerun through the focused keys/UiApp/file/console gates; the final
integration owner retains the combined PTY candidate regression gate.

Example commands, from `D:/sencode/windows/sencode-cli`, after configuring the
existing standard library, runtime, module map and pinned clang toolchain:

```powershell
D:/Sengoo/target/debug/sgc.exe --runtime-mode source-development build src/tests_tui_keys.sg --force-rebuild -O 0 -o target/ui-editor/tests_tui_keys.exe
./target/ui-editor/tests_tui_keys.exe
D:/Sengoo/target/debug/sgc.exe --runtime-mode source-development build src/tests_tui_editor.sg --force-rebuild -O 0 -o target/ui-editor/tests_tui_editor.exe
./target/ui-editor/tests_tui_editor.exe
python tests/keymap_fixture.py target/ui-editor/tests_tui_keymap_file.exe --evidence target/ui-editor/keymap-file-evidence.json
```

The isolated read-only loader passed **16 file checks**. It used an isolated
APPDATA and synthetic explicit paths, confirmed that map bytes were unchanged,
and removed only owned files and empty temporary directories. It did not open
Sencode storage, user credentials or a provider.

## Actual Windows console checks

`tests/tui_editor_console_fixture.py` drove the Sengoo synthetic UI driver in an
owned hidden Win32 console under a kill-on-close Job. It passed **11 checks**:
safe Alt mapping, `/keys` argument discovery and two-step Enter, visible Vim
state, Chinese delete/undo, literal bracketed paste, approval default-deny,
independent picker focus, streaming Escape versus Ctrl+C, reading focus with
unchanged draft/cursor, session-only reset, default Escape compatibility and
terminal mode restoration. Assertions read actual console cells.

```powershell
python tests/tui_editor_console_fixture.py target/ui-editor/tests_tui_editor_console.exe --evidence target/ui-editor/editor-console-evidence.json
```

The existing synthetic fullscreen console gate passed **9 checks**. The real
private main executable then passed the unchanged **14-check production
fixture**, using an isolated database, synthetic credentials and a local HTTP
SSE provider. Credentials were deleted and the owned temporary tree removed.

```powershell
D:/Sengoo/target/debug/sgc.exe --runtime-mode source-development build src/main.sg --force-rebuild -O 2 -o target/ui-editor/sencode-sg.exe
python tests/fullscreen_console_fixture.py target/ui-editor/sencode-sg.exe --production --evidence target/ui-editor/fullscreen-production.json
```

Under **four simultaneously active loopback SSE requests**, 40 input-to-visible
samples measured p50 **14.8489 ms**, p95 **23.2116 ms**, maximum **26.316 ms**.
The measurement runs from `WriteConsoleInputW` injection to the first
`ReadConsoleOutputW` viewport containing the appended draft, with 1 ms polling.
This is local Windows console evidence; it does not claim remote-provider or
other-terminal latency. Pure render benchmarks are a separate measurement.

After this main-candidate run, the integration owner requested a generic,
default-disabled `/terminal [powershell|cmd]` registry entry and `/term` alias.
That registry-only addition passed `tests_commands` (alias, disabled dispatch,
fixed arguments). It belongs to the sibling PTY work and is not claimed inside
the main binary hash below. The final PTY candidate must rerun its own combined
production gate.

## Tested identities

| Artifact | SHA-256 |
| --- | --- |
| `src/tui_keys.sg` | `bf11c3fc672b1a1aca2b1a6445f1a8338c9aab9e1b3d8753aba556359f1691c6` |
| `src/tui_reading.sg` | `9f981f5075e59550f8f34d2871aa234dd76534f21147d29b5ebb03c9b8657b88` |
| `src/tui.sg` | `8f7bf9cb27c873b6d5492fc5fe19cb86772d69f5f1ba3505eb7506d543a96ea2` |
| `src/tests_tui_keys.sg` | `bdb2fa9ee1afc212d7654801a074fa8a05008fe77a390194cd40960ddde10b4e` |
| `src/tests_tui_editor.sg` | `b143f85d7c3a9568dbf36cb61010a5751b10b07b030dc4aab876f501df889774` |
| `src/tests_tui_editor_console.sg` | `74e63596acef2c5a390b44b88fb9e8eb9f83eb521b27e64976a3d81e0d595ee3` |
| `tests/keymap_fixture.py` | `25a8e79335a661a98793f7fb45c8cfd8f8cd7f6556fdf3a5ca0f29490185fbb5` |
| `tests/tui_editor_console_fixture.py` | `eb847f7bb4cf63770ac7d7255bfa0f894909f8bcb9d4a81b2c7f22c1cecad131` |
| `target/ui-editor/tests_tui_keys.exe` | `fc887c2c8d995af5fbd36e8f4fc14d8ad41792eb984db4cbfc6b4342942e0752` |
| `target/ui-editor/tests_tui_editor.exe` | `9ced97914081fecf2c48cbbfd908b6cd0ce0aba1ce4f7b5809eb798876b5ab5f` |
| `target/ui-editor/tests_tui_keymap_file.exe` | `cc2945a39be0507827b5ddf5eff536a0a6546c79bf7f879e0a483adb4ad5c44c` |
| `target/ui-editor/tests_tui_editor_console.exe` | `2ecc277ab2581259965788712b716c5cd6cd5b54ad41a598ff23ee4f90ed23df` |
| `target/ui-editor/sencode-sg.exe` | `0c90877ec4dd09af3f44aef0b337d6fd1d4e9bebede5c390260d1969c287f31c` |
| `D:/Sengoo/target/debug/sgc.exe` | `b79895635aabd0acfef17a81f9f7f0060fcc473bc56b41da47ebb7ff6912169c` |

`openspec validate add-cli-editor-keybindings --strict` passed. This child
implements only a documented Vim composer subset; it does not claim full Vim,
arbitrary key actions, project keymaps, changed permissions or tested platforms
beyond this Windows host.
