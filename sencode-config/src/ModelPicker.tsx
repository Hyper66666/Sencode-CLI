import { useState } from "react";
import { Check, Image, LoaderCircle, Plus, Radar, Search, Star } from "lucide-react";
import type { ConnectionInput } from "./bindings";
import { modelEntry, validModelId } from "./profile";

export default function ModelPicker({ value, onChange, onProbe, disabled, probing }: {
  value: ConnectionInput; onChange: (input: ConnectionInput) => void;
  onProbe: () => void; disabled: boolean; probing: boolean;
}) {
  const [query, setQuery] = useState("");
  const catalog = [...new Set([...value.enabled_models.map(m => m.id), ...value.discovered_model_ids])];
  const visible = catalog.filter(id => id.toLowerCase().includes(query.toLowerCase()));
  function toggle(id: string) {
    const exists = value.enabled_models.some(m => m.id === id);
    const enabled_models = exists ? value.enabled_models.filter(m => m.id !== id) : [...value.enabled_models, modelEntry(id)];
    onChange({ ...value, enabled_models, model: enabled_models.some(m => m.id === value.model) ? value.model : enabled_models[0]?.id ?? "" });
  }
  function add() {
    const id = query.trim();
    if (!validModelId(id) || catalog.includes(id) || value.discovered_model_ids.length >= 256 || value.enabled_models.length >= 256) return;
    onChange({ ...value, discovered_model_ids: [...value.discovered_model_ids, id], enabled_models: [...value.enabled_models, modelEntry(id)], model: value.model || id });
    setQuery("");
  }
  return <section className="models-section" aria-label="模型配置">
    <div className="models-heading"><h3>模型 <span>{value.enabled_models.length} 已启用</span></h3><button className="button secondary" type="button" onClick={onProbe} disabled={disabled}>{probing ? <LoaderCircle size={15} className="spin"/> : <Radar size={15}/>}嗅探模型</button></div>
    <div className="model-search"><Search size={16}/><input aria-label="搜索或添加模型" placeholder="搜索或输入模型 ID" value={query} disabled={disabled} onChange={e => setQuery(e.target.value)} onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); add(); } }}/>{query.trim() && !catalog.includes(query.trim()) && <button type="button" className="icon-button" aria-label="添加模型" title="添加模型" disabled={disabled || !validModelId(query.trim()) || value.enabled_models.length >= 256 || value.discovered_model_ids.length >= 256} onClick={add}><Plus size={18}/></button>}</div>
    {catalog.length > 0 && <div className="model-list-toolbar"><span>{visible.length} 个模型</span><button type="button" disabled={disabled || value.enabled_models.length >= 256 || visible.every(id => value.enabled_models.some(m => m.id === id))} onClick={() => {
      const extra = visible.filter(id => !value.enabled_models.some(m => m.id === id)).slice(0, 256 - value.enabled_models.length).map(modelEntry);
      const enabled_models = [...value.enabled_models, ...extra];
      onChange({ ...value, enabled_models, model: value.model || enabled_models[0]?.id || "" });
    }}>启用全部</button></div>}
    <div className="model-list">
      {visible.length ? visible.map(id => {
        const model = value.enabled_models.find(m => m.id === id), selected = value.model === id;
        return <div className={`model-row ${model ? "enabled-model" : ""}`} key={id}>
          <label className="model-check"><input type="checkbox" aria-label={`启用 ${id}`} checked={!!model} disabled={disabled || (!model && value.enabled_models.length >= 256)} onChange={() => toggle(id)}/><span className="check-box"><Check size={12}/></span><span title={id}>{model?.label || id}</span></label>
          <button type="button" className={`model-capability ${model?.capabilities.visionSupported ? "on" : ""}`} aria-label={`${id} 图片能力`} title="图片能力" aria-pressed={!!model?.capabilities.visionSupported} disabled={disabled || !model} onClick={() => onChange({ ...value, enabled_models: value.enabled_models.map(m => m.id === id ? { ...m, capabilities: { ...m.capabilities, visionSupported: !m.capabilities.visionSupported } } : m) })}><Image size={15}/></button>
          <button type="button" className={`model-default ${selected ? "on" : ""}`} aria-label={`${id} 设为默认`} title={selected ? "默认模型" : "设为默认"} aria-pressed={selected} disabled={disabled || !model} onClick={() => onChange({ ...value, model: id })}><Star size={14} fill={selected ? "currentColor" : "none"}/>{selected && <span>默认</span>}</button>
        </div>;
      }) : <div className="model-empty">{query ? "没有匹配的模型" : "嗅探或添加模型"}</div>}
    </div>
  </section>;
}
