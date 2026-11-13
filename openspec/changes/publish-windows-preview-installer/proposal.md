# Publish the verified Windows preview

## Why

The verified Windows candidate is only available locally. Users need a GitHub
Release with its archive, checksums and an installer that downloads fixed bytes.

## Capabilities

- Add the release-specific PowerShell bootstrap under `scripts/install-release.ps1`.
- Publish the existing verified archive unchanged as a Windows x64 prerelease.
- Record the original build identity and the release source checkpoint separately.

## Non-Goals

No application behavior, state schema, runtime pin or stable-platform claim changes.
The React/Tauri configuration companion is outside this CLI archive.

## Ownership

This child owns download verification and release publication. The existing
package installer continues to own payload verification, updates, PATH and shims.
