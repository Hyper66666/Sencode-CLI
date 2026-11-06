# Model and thinking selection

`/model` uses the saved connection catalog. Each channel keeps its own enabled
models and capabilities, so two channels may expose the same model id without
sharing a selection. Discovered models appear only after they have been enabled
in configuration. Legacy connections with an empty directory retain their saved
selected model for compatibility.

All saved suppliers are available together; choosing the default supplier does
not hide the others. The workbench shows each supplier heading followed by its
enabled models in a vertical list. Up/down crosses supplier boundaries; left/right
jumps to the adjacent supplier. Reopening `/model` refreshes saved configuration,
and `sen models` exposes the same enabled-model catalog. Select a model, then choose
its thinking level in a second list. Completing the second step captures a
connection/model/effort tuple for future requests. Running turns retain their
accepted tuple. Canceling either picker leaves the selected target unchanged.

The session remembers the complete selection, including a change made without
sending a request. `sen -c`, `sen -r`, `sen resume` and the in-app resume picker
restore it. An explicit `--connection` replaces the saved tuple; `--model` keeps
the saved supplier and resets saved effort; `--effort` overrides the level.
This preference is separate from permissions and does not grant approval.
A removed supplier remains unavailable until another target is selected.

The local levels match desktop Sencode: `low`, `medium`, `high`, `xhigh`, `max`.
Explicit model and connection capability restrictions narrow the list. Managed
account runtimes with no implemented effort control offer only **Provider
default**; the CLI does not infer capability from the account or model name.

Native API connections advertise the effort request format implemented by their
selected protocol encoder. This means the CLI can encode the parameter. A custom
endpoint or model may reject it; that error is reported, with no silent provider
or model fallback. `capabilities.reasoningEffort=false` on the connection or model
disables the control. `supportedReasoningEfforts` or `reasoningEfforts` can narrow
the levels to a configured subset.

The native wire mappings follow desktop `sencode-sampling-types`:

| Protocol | Request fields | Tier mapping |
|---|---|---|
| Chat Completions | `reasoning_effort` | `max` → `xhigh` |
| Responses | `reasoning.effort` | `max` → `xhigh` |
| Anthropic Messages | `thinking.type=adaptive`, `thinking.display=summarized`, `output_config.effort` | `xhigh` → `high`; `max` remains `max` |

The stored preference retains its original level, including the distinction
between `xhigh` and `max`. A new native selection uses `medium` when advertised;
otherwise its configured provider default remains in effect. Unsupported levels
fail before network I/O. See [session memory](scroll-session-memory.md).

Native fixtures: `src/tests_model_selection.sg` verifies catalog identity,
capability restrictions, immutable targets and all fifteen protocol/tier
combinations. `tests/model_catalog_fixture.py` verifies the actual SQLite-backed
projection in a fresh temporary profile, including 37 enabled models, Unicode
labels, complete per-model metadata and legacy compatibility. These fixtures do
not contact a provider or use user credentials.
