## Why

Children inherit a provider but fall back to its saved default model. The model
cannot see the host's actual configured request target or discover another
provider's enabled models, so user-selected model names fail to route.

## Capabilities

- Inherit the immutable current provider/model/effort snapshot for subagents.
- Resolve configured enabled model IDs, labels and case-insensitive fragments
  across providers, with deterministic precedence and explicit ambiguity.
- Expose a bounded read-only public model directory and current request identity.

## Non-Goals

No upstream model probing, new credentials, automatic failover, changes to
provider defaults, nested agents or native execution of managed account models.

## Ownership

Controller owns admission and snapshots; model_routing owns public directory
and target resolution; request_identity owns ephemeral host metadata. Sengoo
remains the implementation language. Existing native boundaries are sufficient.
