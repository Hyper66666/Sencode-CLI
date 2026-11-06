import type { ConfiguredModel, Connection, ConnectionInput } from "./bindings";

export const protocols = [
  { value: "chatCompletions", label: "Chat Completions" },
  { value: "responses", label: "Responses" },
  { value: "messages", label: "Anthropic Messages" },
];
export const protocolLabel = (value: string) => protocols.find(p => p.value === value)?.label ?? value;
export const modelEntry = (id: string): ConfiguredModel => ({ id, label: null, capabilities: { visionSupported: false } });
export const validModelId = (id: string) => !!id && new TextEncoder().encode(id).length <= 200 && !/[\p{White_Space}\p{Cc}]/u.test(id);
export function newInput(connection?: Connection): ConnectionInput {
  return { id: connection?.id ?? `custom-${crypto.randomUUID()}`, name: connection?.name ?? "",
    base_url: connection?.base_url ?? "", protocol: connection?.protocol ?? "chatCompletions",
    model: connection?.model ?? "", api_key: "", existing: !!connection,
    enabled_models: structuredClone(connection?.enabled_models ?? []), discovered_model_ids: [...(connection?.discovered_model_ids ?? [])] };
}
export function validateEndpoint(input: Pick<ConnectionInput, "base_url" | "protocol" | "api_key" | "existing">): string | null {
  if (!protocols.some(p => p.value === input.protocol)) return "请选择协议";
  if (!input.existing && !input.api_key.trim()) return "请输入 API Key";
  if (/[\0\r\n]/.test(input.api_key) || new TextEncoder().encode(input.api_key).length > 8192) return "API Key 无效";
  try {
    const url = new URL(input.base_url);
    if (url.username || url.password || url.hash || url.search) return "API 地址不能包含凭据或参数";
    if (new TextEncoder().encode(input.base_url).length > 2048 || /[\0\r\n]/.test(input.base_url)) return "API 地址无效";
    if (url.protocol !== "https:" && !(url.protocol === "http:" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname))) return "API 地址需要使用 HTTPS";
  } catch { return "请输入完整的 API 地址"; }
  return null;
}
export function validateInput(input: ConnectionInput): string | null {
  for (const [key, limit] of [["name", 128], ["base_url", 2048], ["model", 256], ["api_key", 8192]] as const) {
    if (new TextEncoder().encode(input[key]).length > limit || /[\0\r\n]/.test(input[key])) return "内容无效或过长";
  }
  if (!input.name.trim()) return "请输入连接名称";
  if (!input.enabled_models.length) return "请至少启用一个模型";
  if (input.enabled_models.length > 256 || input.discovered_model_ids.length > 256) return "最多支持 256 个模型";
  const ids = input.enabled_models.map(m => m.id);
  if (ids.some(id => !validModelId(id)) || input.discovered_model_ids.some(id => !validModelId(id))) return "模型 ID 无效";
  if (new Set(ids).size !== ids.length) return "模型 ID 不能重复";
  if (input.enabled_models.some(m => (m.label !== null && (typeof m.label !== "string" || /[\0\r\n]/.test(m.label) || new TextEncoder().encode(m.label).length > 256)) || typeof m.capabilities?.visionSupported !== "boolean")) return "模型配置无效";
  if (!ids.includes(input.model)) return "请选择已启用的默认模型";
  return validateEndpoint(input);
}
export function exportProfile(profile: Connection) {
  return { schema: 1, name: profile.name, base_url: profile.base_url, protocol: profile.protocol, model: profile.model,
    enabled_models: profile.enabled_models.map(m => ({ id: m.id, label: m.label, capabilities: { visionSupported: m.capabilities.visionSupported } })),
    discovered_model_ids: [...profile.discovered_model_ids] };
}
export function importProfile(text: string): ConnectionInput {
  if (text.length > 65536) throw new Error("配置文件过大");
  const raw: unknown = JSON.parse(text);
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) throw new Error("配置文件无效");
  const value = raw as Record<string, unknown>;
  if (value.schema !== 1) throw new Error("不支持的配置版本");
  for (const key of ["name", "base_url", "protocol", "model"]) if (typeof value[key] !== "string") throw new Error("配置文件缺少必要字段");
  const input = { ...newInput(), name: value.name as string, base_url: value.base_url as string,
    protocol: value.protocol as string, model: value.model as string,
    enabled_models: [modelEntry(value.model as string)] };
  if (value.enabled_models !== undefined) {
    if (!Array.isArray(value.enabled_models) || value.enabled_models.length > 256) throw new Error("模型配置无效");
    input.enabled_models = value.enabled_models.map((m: unknown) => {
      if (!m || typeof m !== "object" || !("id" in m) || typeof m.id !== "string") throw new Error("模型配置无效");
      const v = m as Record<string, unknown>;
      if (v.label !== null && v.label !== undefined && typeof v.label !== "string") throw new Error("模型配置无效");
      const caps = v.capabilities as Record<string, unknown> | undefined;
      if (!caps || typeof caps.visionSupported !== "boolean") throw new Error("模型配置无效");
      return { id: m.id, label: (v.label as string | null) ?? null, capabilities: { visionSupported: caps.visionSupported } };
    });
  }
  if (value.discovered_model_ids !== undefined) {
    if (!Array.isArray(value.discovered_model_ids) || !value.discovered_model_ids.every(v => typeof v === "string")) throw new Error("模型目录无效");
    input.discovered_model_ids = [...new Set(value.discovered_model_ids as string[])];
  }
  const error = validateInput({ ...input, api_key: "validation-only" });
  if (error) throw new Error(error);
  return input;
}
export function endpointLabel(profile: Connection): string {
  if (profile.kind !== "customApi") return profile.kind === "codex" ? "ChatGPT" : "官方账号";
  try { return new URL(profile.base_url).host; } catch { return profile.base_url; }
}
