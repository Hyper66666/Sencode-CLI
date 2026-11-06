# Sengoo-native Sencode CLI

## Why
Provide a standalone Windows coding CLI and use the real application to improve
Sengoo. The user approved the native-core plan on 2026-11-04.

## Capabilities
Streaming Chat Completions/Responses/Anthropic, programming tools, sessions,
shared desktop API configuration/history, subagents and readonly consultation,
Plan, bounded foreground Goal, local stdio MCP and a scrollback terminal UI.

## Non-Goals
No OAuth/account runtimes, remote MCP, browser, plugin marketplace, hooks, PTY
applications, background Goal or parallel competing code implementations.

## Baselines and dependencies
Sencode a468086401a0d19077b5cf0b6aea3ecff0f04c9a.
Sengoo d46b3f6cd8d6e770734f98edc57aa67cb931e26a; depends on its
add-sencode-cli-foundations. Existing Rust/desktop runtimes keep their behavior.
CLI application logic is Sengoo, OS/TLS/SQLite dependencies remain native.
