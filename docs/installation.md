# Install the native Sencode CLI on Windows

The Windows x64 package provides `sen.exe` and `sencode.exe`. They are identical
copies of the Sengoo-native application. Either name starts the application
directly and preserves the caller's working directory and arguments.

Download a Windows x64 ZIP and its `.sha256` file from the same published release.
Compare the ZIP with the checksum before extracting:

```powershell
Get-FileHash ./sencode-cli-VERSION-windows-x64.zip -Algorithm SHA256
Expand-Archive ./sencode-cli-VERSION-windows-x64.zip ./sencode-cli
./sencode-cli/install.ps1
```

The installer checks every payload file against `package-manifest.json` before
copying it. Checksums detect corruption; obtain the archive and checksum from a
trusted release source. Current locally built packages are unsigned development
candidates until a release is explicitly published.

The default destination is `%LOCALAPPDATA%\SencodeCLI`, with the application in
its `bin` directory. Installation needs no administrator access. The installer
adds `bin` to the user PATH for future processes and places native `sen.exe` and
`sencode.exe` forwarders in `%LOCALAPPDATA%\Microsoft\WindowsApps`, which Windows
normally already includes in PATH. This also lets an existing terminal find the
commands without inheriting a new PATH. Type `sen` from a project directory to
start there; no path argument is required.

Both forwarders use an owned `.sencode-cli-bin` junction to the same installation.
They preserve Unicode arguments, the current directory, standard streams and the
application exit code. They do not invoke a command shell. Existing commands are
never overwritten: a collision, changed forwarder or foreign ownership marker
stops installation. If WindowsApps is unavailable or absent from the shell's
existing PATH, the installer reports that limitation; a new terminal uses the
registered `bin` entry. A terminal's inherited environment cannot be changed by
an unrelated process.

For a portable installation without any PATH changes:

```powershell
./sencode-cli/install.ps1 -Prefix 'C:/tools/SencodeCLI' -NoPath
& 'C:/tools/SencodeCLI/bin/sen.exe' --version
```

`-NoPath` also omits the global forwarders. For managed environments with an
existing user command directory, `-CommandDirectory PATH` explicitly selects
where to install them; the directory must already exist and be separate from
the installation prefix. This option can be combined with `-NoPath` to keep all
PATH settings untouched. Do not select a system directory or another product's
private directory. Existing desktop and Rust runtime installations remain
separate from this CLI installation.

Use an empty directory for the first installation. Subsequent installations may
update a directory bearing this installer's ownership marker. Stop running CLI
processes before upgrading. A checksum failure or foreign nonempty destination
stops installation with an error. The installer never downloads native tools.

Ripgrep 14.1.1 is included as `bin/rg.exe`, with its upstream MIT/Unlicense
notices and pinned checksums in `package-manifest.json`. Model command jobs
prepend the installed tool directory to their own PATH, including when the
terminal has an older PATH. `sen doctor` reports the resolved search executable.
This does not register ripgrep globally or modify a workspace's environment.

The installed program requires Windows and the native components shipped in the
package. Running it does not invoke Sengoo, Rust, Python, Node.js, clang or a shell
wrapper. The small Windows command forwarder imports only Kernel32. A model
request additionally requires a configured connection, its OS
credential and network access. Ordinary shell tools are needed only for tasks
that choose to use those tools.

```powershell
sen --help
sencode --version
sen --cwd 'C:/projects/example'
sen resume
sen resume SESSION_ID
sen -c
sen -r
sen -r "unique title"
```

No arguments starts the fullscreen workbench in the current directory.
`resume` without an ID selects that project's latest session. Use `--cwd` to
select another project. `--help` and `--version` do not open state or credentials.
`-c` continues immediately; `-r` opens the project session picker in fullscreen.
`-r SEARCH` matches an exact ID or a unique title substring. Ambiguous searches
require an explicit selection. Use `--tui scrolling` for the earlier interface.

Conversation data is saved to `.sencode/history.sqlite3` inside the selected
project. Open an existing project once to capture its catalog history before
moving it. After closing the CLI and stopping that project's background jobs,
rename the folder and run `sen -c` there to continue the same conversation.
Keep `.sencode` with the project; the CLI adds private history ignore rules
without replacing existing rules. API credentials stay in Windows Credential
Manager. If the shared catalog is lost, `sen --import-history -c` explicitly
imports a reviewed idle archive; saved Goals remain paused.

This candidate requires shared-state schema 29. An existing desktop database
may still use schema 28; the CLI refuses to upgrade that database and leaves its
data unchanged. Close older desktop clients and use the matching desktop build
to back up and perform the coordinated upgrade before sharing the database.

To try the candidate independently first, select a new database path explicitly:

```powershell
sen --database "$env:LOCALAPPDATA/SencodeCLI/candidate-state.db"
```

Choose a path that does not already contain a database. This creates separate
candidate sessions and connection configuration; it does not import existing
desktop sessions or credentials. Keep using the same `--database` path when
resuming or configuring this isolated candidate.

To remove a portable installation, stop the CLI, inventory the files under the
chosen prefix, remove those files individually and remove directories once
empty. For a global installation, also remove only the two forwarders whose
hashes match `.sencode-cli-command-shims.json`, unlink its verified
`.sencode-cli-bin` junction without traversing its target, and remove that marker.
Keep other WindowsApps files. Remove the exact `bin` entry from the user PATH
through Windows Environment Variables. Application state and stored
credentials have their own lifecycle; replacing executable files is not a reset.

## Build and verify a local package

From the CLI source directory, build first, then package the final executable:

```powershell
./scripts/build.ps1 -SengooRoot D:/Sengoo -Configuration Release
$package = ./scripts/package.ps1
./scripts/smoke-install.ps1 -PackageDirectory $package.package_directory `
    -EvidencePath ./target/install-evidence.json
```

`package.ps1` audits PE imports, including delay imports. Every dependency must
be a Windows system DLL or an explicitly supplied redistributable:

```powershell
./scripts/package.ps1 -RuntimeDll @('C:/redistributables/example.dll') `
    -OutputDirectory ./target/packages-candidate-2
```

The script rejects a missing non-system dependency or an unused supplied DLL.
Managed official runtimes are optional packaging inputs. Pass
`-ManagedRuntimeManifest PATH` containing schema 1 and a `managedRuntimes` array;
each entry includes `engine`, pinned `runtime_version`, `protocol_version`,
fixed `executable`, lowercase `sha256`, an absolute `source` file and a `license`
file. Supported pairs are Codex app-server 0.144.4 / protocol 0.144.4 /
`codex-app-server.exe` and Sencode ACP 0.2.102 / protocol 1 / `sencode-agent.exe`.
Packaging audits their PE dependencies, verifies hashes and includes notices.
The installer places the trusted manifest beside the installed executables.
No runtime is downloaded during installation. A package without those inputs
continues to support API connections and reports account runtimes unavailable.

The ZIP contains both aliases, the installer, this guide, the repository license,
a schema-v1 manifest and `SHA256SUMS`. The manifest records source revision,
working-tree status, payload hashes and native imports. Existing output paths
are refused; use a new output directory for another candidate.

The smoke check installs under a fresh Unicode/metacharacter prefix with
`-NoPath -CommandDirectory` pointing to an isolated existing command directory,
runs both
aliases from a Unicode path, and verifies help, version, argument errors, exact
Unicode/empty/quoted arguments and the caller's directory through the diagnostic
`probe` command. It reruns the native files from a directory containing only the
executables and their explicitly bundled DLLs. Child processes get a new empty
profile and a PATH containing only Windows System32; no compiler paths or
Sengoo environment variables are inherited. Read-only probes must leave profile
and workspace directories empty. A final `doctor` run initializes only an
explicit disposable database, using no saved user connections or credentials.
Both aliases then start with no arguments using the empty synthetic profile,
list their new session through `/agents`, resume the latest session, and resume
the exact ID. This checks startup and recovery without a model request. The
separate provider fixture covers read/edit/command execution with real streams.
The Sengoo synchronous filesystem regression separately verifies Chinese/emoji
file names, managed reads, atomic replacement, copy, listing/search and removal.
Asynchronous file operations require their own qualification.
User/process PATH remains unchanged. Temporary files are removed individually
unless `-Keep` is supplied.

The same check invokes bare `sen` and `sencode` through CMD with a stale PATH
containing only System32 and the existing command directory; the new install
`bin` is deliberately absent. It verifies startup lookup, Unicode and shell
metacharacter arguments, native literal-quote forwarding, nonzero exit status
and `resume SESSION_ID`. Owned updates pass; foreign-command collisions and
modified forwarders must stop before publishing payload changes. This proves
the forwarding mechanism without assuming that an existing user console has
refreshed its environment.

This is a local tools-absent-environment check. It does not replace a fresh
Windows VM installation: the development host still contains its source trees
and tools. Record that cold-install qualification separately before claiming
clean-machine release acceptance. Other operating systems need their own
packaging and execution evidence.
