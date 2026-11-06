## ADDED Requirements

### Requirement: Installed commands can use the pinned search tool
The Windows package SHALL include the checked official ripgrep binary and licenses and SHALL make it available to command subprocesses without requiring a developer installation or modifying the user's global PATH.

#### Scenario: Command environment omits development tools
- **WHEN** installed CLI runs an approved rg command through Bash or PowerShell with a System32-only inherited PATH
- **THEN** rg executes from the installed tool directory, preserves Unicode results and normal match/no-match exit codes, and the parent environment remains unchanged

#### Scenario: Damaged package tool
- **WHEN** the packaged ripgrep differs from its manifest checksum
- **THEN** installation rejects the package before publishing any changed executable
