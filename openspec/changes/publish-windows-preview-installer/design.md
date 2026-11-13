# Fixed release download

The bootstrap embeds the GitHub repository, preview tag, archive name and SHA-256.
It downloads over HTTPS into a unique temporary directory, checks the full hash
before extraction and delegates to the existing payload installer. `-ArchivePath`
supports an offline copy with exactly the same required hash. `-Prefix`, `-NoPath`
and `-CommandDirectory` retain the underlying installer's behavior.

A bad hash must fail before installation. Download or installation failure remains
an error; cleanup cannot turn it into success. Cleanup inventories the owned
temporary directory, rejects links, deletes individual files and then empty
directories. It never deletes an offline input archive or application state.

No credentials or histories enter the assets. Publish as a prerelease with the
original source-dirty build provenance, exact executable/archive identities and
separate historical fixture, current install and remote-download verification.
Do not label the candidate as a fresh-VM, live-provider or non-Windows result.
