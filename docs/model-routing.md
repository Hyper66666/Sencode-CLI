# Agent model selection

Subagents inherit the **current request's** provider, model and reasoning effort.
The provider's saved default does not override a selection made with `/model`.

When a user asks for another configured model, `spawn_agent.model` accepts its
enabled ID, display label or a case-insensitive name fragment. For example,
`terra` resolves `gpt-6.1-terra` even on another configured provider. The read-only
`list_models` tool searches that same directory; no configuration-file lookup or
API key is needed from the user.

Exact IDs take precedence over labels and partial matches. Multiple distinct
matches return candidates for clarification. If the same ID exists on the
current provider, that provider wins; other provider ties need a choice. Pass
`connection_id` to constrain a selection. Selecting a different provider alone
uses its configured default; selecting the current provider alone preserves the
current model. Discovered-only models are not enabled targets. Account models
that require a managed runtime report that native subagents cannot invoke them.

The host supplies each request's configured model, provider and effort in its
system context. This describes the selected API alias, not an independently
verified identity of the upstream model. It is regenerated for each request and
is not saved as a user message or carried across model switches.
