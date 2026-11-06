# Effective model effort

Native API turns default to `medium` when the captured connection and exact
model permit that level. This is resolved when building the owned connection
snapshot, rather than being a display-only suffix. Chat Completions sends
`reasoning_effort`, Responses sends `reasoning.effort`, and Anthropic Messages
sends adaptive thinking with `output_config.effort`.

The model picker and connection request boundary share the same capability
parser. Explicit connection or model denial wins. A declared subset without
`medium` retains the provider default, while an explicitly requested unsupported
level fails before network I/O. Normalized picker rows keep their narrowed
effort list. A manually entered model can use connection-level capability but
does not become enabled in the catalog or inherit a different model's metadata.

Native protocol support describes the implemented encoder. It does not certify
that every remote model accepts every effort field. Saved capability overrides
can narrow this contract. Managed account adapters retain their reported effort
limits; the native default does not claim new support for them.

The old low-level `provider_build_request` empty-effort entry keeps its exact
payload behavior for callers that need the provider default. Native agent
requests use the resolved `ProviderConnection.effort_id()` value. A later model,
connection or effort selection cannot mutate an in-flight connection snapshot.

Native checks are `src/tests_model_selection.sg` and
`src/tests_effort_default.sg`; the latter requires `--database` with a disposable
database. Evidence and hashes are in `target/medium-effort-evidence.json`.
The integration owner verifies the final header, picker, controller paths and
optimized executable separately.
