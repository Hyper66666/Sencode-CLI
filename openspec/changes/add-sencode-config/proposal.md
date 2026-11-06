# sencode-config

## Capabilities

Build a small React and Tauri Windows companion for Sencode CLI: white minimal
connection cards, one-click default selection, search, add/edit/delete API
connections, model discovery, multiple enabled models per API, explicit non-secret import/export and keyboard actions. Existing
account connections may be selected but are not reauthenticated or edited here.

The Sengoo bridge reuses the CLI shared-store v1/schema29, connection locks and
Windows Credential Manager. The React projection never owns a parallel config
store. Existing turns keep their captured provider/model.

## Non-Goals

No chat UI, provider proxy, OAuth implementation, unsolicited connectivity probe,
secret export or browser localStorage copy. No changes to the desktop workbench.

## Ownership

One integration owner maintains the new application and bridge. Runtime and
credential ownership remain with existing Sengoo CLI state APIs.
