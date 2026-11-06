# Native CLI request recovery

The native API engine currently stops on transient provider refusal and relies
on manual context compaction. This change adds bounded evidence-based request
retries, model-scoped automatic compaction, and separately validated Responses
continuation without weakening durable submit/tool admission or managed-account
capability boundaries.

## Capabilities

- Safely retry a single native request before any provider stream is observed.
- Compact complete historical units under explicit/model-specific limits while
  retaining the original public transcript, recent tool pairs and Goal budgets.
- Preserve documented opaque Responses output items when protocol evidence and
  fixture validation support continuation.

## Non-Goals

No service fallback, automatic replay of tools, token quota estimation, account
OAuth changes, desktop compaction implementation, or managed-backend budget
claims. Desktop auto-context-compaction remains owned by its existing change.

## Ownership and dependencies

Core owns new retry/context/attempt modules, native provider framing and the
controller/scheduler integration. Root owns configuration UI, shared schema,
packaging and candidate rollout. The Sengoo owner supplies transport evidence
before connection failures may be retried. This is a child of
add-cli-fullscreen-local-parity and preserves add-sengoo-native-cli contracts.
