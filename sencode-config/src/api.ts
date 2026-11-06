import { commands, type ConnectionInput, type ProbeInput, type ProbeResult, type Snapshot } from "./bindings";
import { modelEntry } from "./profile";

export const isPreview = !('__TAURI_INTERNALS__' in window) && new URLSearchParams(location.search).has("preview");
const sample = (id: string, name: string, base_url: string, protocol: string, model: string, models: string[]) =>
  ({ id, name, base_url, protocol, model, models, kind: "customApi", enabled_models: models.map(modelEntry), discovered_model_ids: models });
let preview: Snapshot = {
  current: "preview-openai", database: "C:\\Users\\you\\.sencode\\local-sessions.sqlite3",
  connections: [
    sample("preview-openai", "OpenAI", "https://api.openai.com/v1", "responses", "gpt-5.2", ["gpt-5.2", "gpt-5.2-codex"]),
    sample("preview-anthropic", "Anthropic", "https://api.anthropic.com/v1", "messages", "claude-sonnet-4-6", ["claude-sonnet-4-6", "claude-opus-4-6"]),
    sample("preview-deepseek", "DeepSeek", "https://api.deepseek.com", "chatCompletions", "deepseek-chat", ["deepseek-chat", "deepseek-reasoner"]),
    sample("preview-local", "本地模型", "http://127.0.0.1:11434/v1", "chatCompletions", "qwen3.5", ["qwen3.5"]),
  ],
};
function unwrap<T>(result: { status: "ok"; data: T } | { status: "error"; error: string }): T {
  if (result.status === "error") throw new Error(result.error);
  return result.data;
}
function requireNative() {
  if (!('__TAURI_INTERNALS__' in window) && !isPreview) throw new Error("请在 sencode-config 桌面应用中打开");
}
export async function snapshot(): Promise<Snapshot> {
  requireNative();
  if (isPreview) return structuredClone(preview);
  return unwrap(await commands.getSnapshot());
}
export async function select(id: string): Promise<Snapshot> {
  requireNative();
  if (isPreview) { preview.current = id; return snapshot(); }
  return unwrap(await commands.selectConnection(id));
}
export async function save(input: ConnectionInput): Promise<Snapshot> {
  requireNative();
  if (isPreview) {
    const old = preview.connections.find(c => c.id === input.id);
    const { api_key: _, existing: __, ...metadata } = input;
    const profile = { ...metadata, kind: "customApi", models: [input.model, ...input.enabled_models.map(m => m.id).filter(id => id !== input.model)] };
    preview.connections = old ? preview.connections.map(c => c.id === input.id ? profile : c) : [...preview.connections, profile];
    return snapshot();
  }
  return unwrap(await commands.saveConnection(input));
}
export async function probe(input: ProbeInput): Promise<ProbeResult> {
  requireNative();
  if (isPreview) {
    await new Promise(resolve => setTimeout(resolve, 350));
    return { model_ids: ["fixture-model", "fixture-reasoner", "fixture-vision"], truncated: false };
  }
  return unwrap(await commands.probeModels(input));
}
export async function remove(id: string): Promise<Snapshot> {
  requireNative();
  if (isPreview) { preview.connections = preview.connections.filter(c => c.id !== id); if (preview.current === id) preview.current = ""; return snapshot(); }
  return unwrap(await commands.removeConnection(id));
}
