# Consume the shared Sengoo Agent SDKs

Remove duplicate Provider/HTTP/SSE/transport implementations from the CLI and
consume sgllm. Adapt stdio MCP to sgmcp's polling client while retaining Sencode
permissions, control input, task state and terminal behavior. The integration
owner owns CLI adapters, dependency lock, scripts and integration evidence.

No new provider fallback, credential storage, permission grants or tool replay.
Existing module names remain compatibility imports for internal consumers.
