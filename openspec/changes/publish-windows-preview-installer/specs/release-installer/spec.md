## ADDED Requirements

### Requirement: Fixed archive verification before installation
The release bootstrap SHALL download the explicitly pinned Windows x64 archive
over HTTPS and verify its embedded SHA-256 before extracting or installing it.

#### Scenario: Install a published release
- **WHEN** the user runs the bootstrap with a matching downloaded or offline archive
- **THEN** it delegates to the existing payload-verifying installer and honors the supplied prefix and PATH options.

#### Scenario: Reject changed archive bytes
- **WHEN** the archive hash differs from the embedded release hash
- **THEN** the command fails before creating the installation and preserves the offline input.

### Requirement: Preserve installation and release provenance
The release SHALL retain payload notices and original build identities, and SHALL
describe this candidate as a Windows development preview.

#### Scenario: Clean up a completed or failed download
- **WHEN** the bootstrap finishes or fails
- **THEN** it removes only its owned temporary files and empty directories and preserves application state and offline inputs.

#### Scenario: Publish the verified candidate
- **WHEN** the release is published
- **THEN** its ZIP and bootstrap have published checksums and its evidence distinguishes the original source-dirty build from the release source checkpoint.
