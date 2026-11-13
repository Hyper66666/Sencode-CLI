# Design

The six protocol modules become imports of sgllm; CLI connection/image grants,
engine_request and state stay application-owned. Six pure policy modules
(policy, scheduler, tool_schedule, tool_spec, request_retry and question) import
sgagent. Its helpers are host-independent; this does not replace the CLI's
durable execution loop with the example kernel. MCP wrappers
call begin/poll/result and pump the existing engine controls without reading
user input in the SDK. Cleanup must reach process-tree quiescence before writer
release. Public SDK errors retain numeric compatibility; owning inactive Err
payloads are avoided and error details use explicit successful accessors.

Dependency manifests and lockfiles include the SDKs and transitive schema
package. Direct-compiler test maps must reflect the same graph. Acceptance
records the shared package sources as well as CLI/stdlib inputs. A previous
candidate built while adapters were changing is preflight only and cannot
support final hash/freeze claims.

The schema/SDK boundaries remain experimental until actual package and CLI
consumers pass. Keep original installed CLI as the working version until final
candidate integration, packaging and rollback checks succeed.
