import { useCallback, useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { ArrowDownToLine, ArrowRight, Check, CheckCheck, ChevronDown, Ellipsis, Eye, EyeOff, FolderKey, Import, KeyRound, LoaderCircle, Plus, RefreshCw, Search, Settings2, SlidersHorizontal, Terminal, Trash2, X, Pencil, ChevronRight } from "lucide-react";
import type { Connection, ConnectionInput, Snapshot } from "./bindings";
import * as api from "./api";
import { endpointLabel, exportProfile, importProfile, newInput, protocolLabel, protocols, validateEndpoint, validateInput } from "./profile";
import ModelPicker from "./ModelPicker";

function Mark({ large = false }: { large?: boolean }) {
  return <svg className={large ? "brand-mark large" : "brand-mark"} viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" rx="12" fill="currentColor"/><path d="M28 12H16l-5 8h13l-4 8H10m2-8h16" fill="none" stroke="white" strokeWidth="2.6" strokeLinecap="square" strokeLinejoin="round"/></svg>;
}

function Modal({ children, label, onClose, drawer = false }: { children: ReactNode; label: string; onClose: () => void; drawer?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const close = useRef(onClose); close.current = onClose;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const dialog = ref.current!;
    (dialog.querySelector<HTMLInputElement>("input") ?? dialog.querySelector<HTMLButtonElement>("button") ?? dialog).focus();
    function key(event: KeyboardEvent) {
      if ([...document.querySelectorAll('[role="dialog"]')].at(-1) !== dialog) return;
      if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); close.current(); }
      if (event.key !== "Tab") return;
      const controls = [...dialog.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),[tabindex="0"]')];
      const first = controls[0], last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
    }
    document.addEventListener("keydown", key, true);
    return () => { document.removeEventListener("keydown", key, true); previous?.focus(); };
  }, []);
  return <div className={`scrim ${drawer ? "drawer-scrim" : ""}`} onMouseDown={e => { if (e.target === e.currentTarget) onClose(); }}><div ref={ref} role="dialog" aria-modal="true" aria-label={label} tabIndex={-1} className={drawer ? "drawer" : "modal"}>{children}</div></div>;
}

function ProfileBadge({ profile, size = "" }: { profile: Connection; size?: string }) {
  const host = endpointLabel(profile).toLowerCase();
  const variant = host.includes("anthropic") ? "anthropic" : host.includes("deepseek") ? "deepseek" : host.includes("openai") || profile.kind === "codex" ? "openai" : "generic";
  return <div className={`profile-badge ${variant} ${size}`} aria-hidden="true">{variant === "anthropic" ? "A" : variant === "deepseek" ? "D" : variant === "openai" ? <span>◎</span> : <Terminal size={21}/>}</div>;
}

export default function App() {
  const [data, setData] = useState<Snapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState<"connections" | "settings">("connections");
  const [form, setForm] = useState<ConnectionInput | null>(null);
  const [initialForm, setInitialForm] = useState("");
  const [formError, setFormError] = useState("");
  const [reveal, setReveal] = useState(false);
  const [probing, setProbing] = useState(false);
  const [deleting, setDeleting] = useState<Connection | null>(null);
  const [discard, setDiscard] = useState(false);
  const [menu, setMenu] = useState("");
  const search = useRef<HTMLInputElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const formElement = useRef<HTMLFormElement>(null);
  const refreshing = useRef(false);

  const refresh = useCallback(async (visible = false) => {
    if (refreshing.current) return;
    refreshing.current = true;
    if (visible) setLoading(true);
    try { setData(await api.snapshot()); setError(""); }
    catch (e) { setError(e instanceof Error ? e.message : "无法读取配置"); }
    finally { setLoading(false); refreshing.current = false; }
  }, []);
  useEffect(() => {
    void refresh();
    const focus = () => void refresh();
    window.addEventListener("focus", focus);
    const timer = setInterval(() => { if (document.visibilityState === "visible") void refresh(); }, 5000);
    return () => { window.removeEventListener("focus", focus); clearInterval(timer); };
  }, [refresh]);
  useEffect(() => { if (!notice) return; const timer = setTimeout(() => setNotice(""), 3000); return () => clearTimeout(timer); }, [notice]);

  function openEditor(input: ConnectionInput) {
    setInitialForm(JSON.stringify(input)); setForm(input); setFormError(""); setReveal(false); setMenu("");
  }
  function closeEditor() {
    if (busy || probing) return;
    if (form && JSON.stringify(form) !== initialForm) { setDiscard(true); return; }
    setForm(null);
  }
  useEffect(() => {
    function key(e: KeyboardEvent) {
      if (form && !discard && !deleting && !busy && !probing && (e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); formElement.current?.requestSubmit(); return; }
      if (e.defaultPrevented || form || deleting || discard) return;
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setPage("connections"); search.current?.focus(); }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "n") { e.preventDefault(); openEditor(newInput()); }
      if (e.key === "Escape") { if (menu) setMenu(""); else { setQuery(""); search.current?.blur(); } }
    }
    window.addEventListener("keydown", key); return () => window.removeEventListener("keydown", key);
  }, [form, deleting, discard, menu, busy, probing]);

  async function mutate(id: string, operation: () => Promise<Snapshot>, success: string) {
    if (busy) return false;
    setBusy(id); setError("");
    try { setData(await operation()); setNotice(success); return true; }
    catch (e) { setError(e instanceof Error ? e.message : "操作失败"); return false; }
    finally { setBusy(""); }
  }
  async function submit(e: FormEvent) {
    e.preventDefault(); if (!form || busy || probing) return;
    const input = { ...form, name: form.name.trim(), model: form.model.trim(), base_url: form.base_url.trim(), api_key: form.api_key.trim() };
    const invalid = validateInput(input); if (invalid) { setFormError(invalid); return; }
    setBusy(input.id); setFormError("");
    try { setData(await api.save(input)); setForm(null); setNotice("连接已保存"); }
    catch (e) { setFormError(e instanceof Error ? e.message : "保存失败"); }
    finally { setBusy(""); }
  }
  async function probeModels() {
    if (!form || busy || probing) return;
    const input = { ...form, base_url: form.base_url.trim(), api_key: form.api_key.trim() };
    const invalid = validateEndpoint(input); if (invalid) { setFormError(invalid); return; }
    setProbing(true); setFormError("");
    try {
      const result = await api.probe(input);
      setForm(current => current?.id === input.id ? { ...current, discovered_model_ids: result.model_ids } : current);
      setNotice(result.truncated ? `已读取 ${result.model_ids.length} 个模型（目录未完整）` : `已读取 ${result.model_ids.length} 个模型`);
    } catch (e) { setFormError(e instanceof Error ? e.message : "嗅探失败"); }
    finally { setProbing(false); }
  }
  function download(profile: Connection) {
    const blob = new Blob([JSON.stringify(exportProfile(profile), null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob), anchor = document.createElement("a");
    anchor.href = url; anchor.download = `${profile.name.replace(/[^\p{L}\p{N}_.-]/gu, "-")}.sencode.json`; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000); setMenu("");
  }
  const current = data?.connections.find(c => c.id === data.current);
  const profiles = data?.connections.filter(c => `${c.name} ${c.models.join(" ")} ${c.base_url} ${protocolLabel(c.protocol)}`.toLowerCase().includes(query.toLowerCase())) ?? [];
  const active = data?.connections.filter(c => c.id === data.current).length ?? 0;

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><Mark/><span>sencode<span className="brand-config">config</span></span></div>
      <nav aria-label="导航"><button className={`nav-item ${page === "connections" ? "selected" : ""}`} onClick={() => setPage("connections")}><SlidersHorizontal size={18}/>连接<span className="nav-count">{data?.connections.length ?? 0}</span></button><button className={`nav-item ${page === "settings" ? "selected" : ""}`} onClick={() => setPage("settings")}><Settings2 size={18}/>设置</button></nav>
      <div className="sidebar-bottom"><div className="sidebar-cli"><Terminal size={16}/><span>Sencode CLI</span><span className="status-dot"/></div><div className="app-version">v0.1.0{api.isPreview && <span className="preview-label">预览</span>}</div></div>
    </aside>
    <main>
      <header className="topbar"><span className="breadcrumb">Sencode<ChevronRight size={14}/><span>{page === "connections" ? "连接" : "设置"}</span></span><button className={`icon-button ${loading ? "spinning" : ""}`} aria-label="刷新配置" title="刷新配置" onClick={() => void refresh(true)} disabled={loading || !!busy}><RefreshCw size={17}/></button></header>
      <div className="workspace">
        {error && <div className="error-banner" role="alert"><span>{error}</span><button className="icon-button" aria-label="关闭错误" onClick={() => setError("")}><X size={16}/></button></div>}
        {page === "connections" ? <>
          <div className="page-heading"><h1>连接</h1><div className="heading-actions"><button className="button secondary import-button" onClick={() => fileInput.current?.click()}><Import size={16}/>导入</button><button className="button primary" onClick={() => openEditor(newInput())}><Plus size={17}/>添加连接</button></div></div>
          <section className={`current-panel ${!current ? "no-current" : ""}`} aria-label="当前连接">
            <div className="current-main">{current ? <ProfileBadge profile={current} size="big"/> : <div className="profile-badge big generic"><Terminal size={24}/></div>}<div><div className="current-label"><span className={`status-dot ${current ? "" : "muted-dot"}`}/>{current ? "当前使用" : "未选择连接"}</div><h2>{current?.name ?? "准备好下一次对话"}</h2></div></div>
            {current && <div className="current-target"><div className="current-model"><span className="model-symbol">↗</span>{current.model || "默认模型"}</div><span className="current-protocol">{current.kind === "customApi" ? protocolLabel(current.protocol) : "官方账号"}</span></div>}
          </section>
          <div className="list-toolbar"><div className="section-title">全部连接<span>{data?.connections.length ?? 0}</span></div><div className="search-field"><Search size={16}/><input ref={search} aria-label="搜索连接" placeholder="搜索连接或模型" value={query} onChange={e => setQuery(e.target.value)}/>{query ? <button className="icon-button" aria-label="清空搜索" onClick={() => setQuery("")}><X size={14}/></button> : <kbd>Ctrl K</kbd>}</div></div>
          {loading && !data ? <div className="empty-state"><LoaderCircle className="spin" size={26}/></div> : profiles.length ? <div className="connection-grid">{profiles.map(profile => {
            const selected = profile.id === data?.current, editing = profile.kind === "customApi";
            return <article key={profile.id} className={`connection-card ${selected ? "active-card" : ""}`}>
              <div className="card-top"><ProfileBadge profile={profile}/><div className="card-identity"><h3 title={profile.name}>{profile.name}</h3><div className="endpoint" title={profile.base_url}>{endpointLabel(profile)}</div></div>{selected && <span className="active-badge"><Check size={12}/>使用中</span>}{editing && <div className="menu-anchor"><button className="icon-button" aria-label={`管理 ${profile.name}`} aria-expanded={menu === profile.id} onClick={() => setMenu(menu === profile.id ? "" : profile.id)}><Ellipsis size={19}/></button>{menu === profile.id && <><button className="menu-dismiss" aria-label="关闭菜单" onClick={() => setMenu("")}/><div className="dropdown" role="menu"><button role="menuitem" onClick={() => openEditor(newInput(profile))}><Pencil size={15}/>编辑</button><button role="menuitem" onClick={() => download(profile)}><ArrowDownToLine size={15}/>导出配置</button><div className="menu-divider"/><button role="menuitem" className="danger-text" onClick={() => { setMenu(""); setDeleting(profile); }}><Trash2 size={15}/>删除</button></div></>}</div>}</div>
              <div className="protocol-tag">{editing ? protocolLabel(profile.protocol) : "官方账号"}</div>
              <div className="card-bottom"><div className="model-field" title={profile.model}>{profile.models.length > 1 && editing ? <><select aria-label={`${profile.name} 的模型`} value={profile.model} disabled={!!busy} onChange={e => { const input = { ...newInput(profile), model: e.target.value }; void mutate(profile.id, () => api.save(input), "模型已更新"); }}>{profile.models.map((model, i) => <option key={`${model}-${i}`} value={model}>{model}</option>)}</select><ChevronDown size={13}/></> : <span>{profile.model || "默认模型"}</span>}</div><button className={`switch-button ${selected ? "is-current" : ""}`} disabled={selected || !!busy} onClick={() => void mutate(profile.id, () => api.select(profile.id), `已切换至 ${profile.name}`)}>{busy === profile.id ? <LoaderCircle className="spin" size={15}/> : selected ? <CheckCheck size={15}/> : <>使用<ArrowRight size={14}/></>}</button></div>
            </article>;
          })}</div> : <div className="empty-state">{query ? <><Search size={30}/><h2>没有找到连接</h2><button className="button secondary" onClick={() => setQuery("")}>清空搜索</button></> : <><Mark large/><h2>添加第一个连接</h2><button className="button primary" onClick={() => openEditor(newInput())}><Plus size={16}/>添加连接</button></>}</div>}
          <div className="workspace-footer"><span><span className="status-dot muted-dot"/>{data ? `${data.connections.length} 个连接 · ${active ? "1 个使用中" : "未选择"}` : "未连接"}</span><span><kbd>Ctrl N</kbd>添加连接</span></div>
        </> : <>
          <div className="page-heading"><h1>设置</h1></div>
          <section className="settings-card"><h2><FolderKey size={19}/>配置</h2><div className="setting-row"><label>数据库</label><code>{data?.database ?? "未连接"}</code></div><div className="setting-row"><label>API Key</label><span><KeyRound size={15}/>Windows Credential Manager</span></div><div className="setting-row"><label>当前连接</label><span>{current?.name ?? "未选择"}</span></div></section>
          <section className="settings-card"><h2><Terminal size={19}/>快捷键</h2><div className="setting-row"><label>搜索</label><kbd>Ctrl K</kbd></div><div className="setting-row"><label>添加连接</label><kbd>Ctrl N</kbd></div><div className="setting-row"><label>保存连接</label><kbd>Ctrl Enter</kbd></div></section>
        </>}
      </div>
    </main>
    <input ref={fileInput} className="sr-only" type="file" accept=".json" aria-label="导入配置文件" onChange={async e => { const file=e.target.files?.[0]; e.target.value=""; if (!file) return; try { if (file.size>65536) throw new Error("配置文件过大"); openEditor(importProfile(await file.text())); } catch (err) { setError(err instanceof Error ? err.message : "无法导入配置"); } }}/>
    {notice && <div className="toast" role="status"><Check size={16}/>{notice}</div>}
    {form && <Modal label={form.existing ? "编辑连接" : "添加连接"} drawer onClose={closeEditor}>
      <div className="drawer-header"><h2>{form.existing ? "编辑连接" : "添加连接"}</h2><button className="icon-button" aria-label="关闭编辑" disabled={!!busy || probing} onClick={closeEditor}><X size={21}/></button></div>
      <form ref={formElement} className="profile-form" onSubmit={submit}>
        <div className="form-body">
          {!form.existing && <div className="presets">{[{ name: "OpenAI", url: "https://api.openai.com/v1", protocol: "responses" }, { name: "Anthropic", url: "https://api.anthropic.com/v1", protocol: "messages" }, { name: "DeepSeek", url: "https://api.deepseek.com", protocol: "chatCompletions" }].map(p => <button key={p.name} type="button" disabled={!!busy || probing} className={form.base_url === p.url ? "chosen" : ""} onClick={() => setForm({ ...form, name: p.name, base_url: p.url, protocol: p.protocol })}>{p.name}</button>)}</div>}
          <label className="field-label">名称<input autoFocus autoComplete="off" name="connection-name" placeholder="我的 API" value={form.name} disabled={!!busy || probing} onChange={e => setForm({ ...form, name: e.target.value })}/></label>
          <label className="field-label">API 地址<input autoComplete="off" name="base-url" placeholder="https://api.example.com/v1" value={form.base_url} disabled={!!busy || probing} onChange={e => setForm({ ...form, base_url: e.target.value })}/></label>
          <label className="field-label">协议<div className="select-wrap"><select value={form.protocol} disabled={!!busy || probing} onChange={e => setForm({ ...form, protocol: e.target.value })}>{protocols.map(p => <option value={p.value} key={p.value}>{p.label}</option>)}</select><ChevronDown size={16}/></div></label>
          <label className="field-label">API Key<div className="secret-input"><input autoComplete="new-password" name="api-key" spellCheck={false} type={reveal ? "text" : "password"} placeholder={form.existing ? "留空保留现有 Key" : "输入 API Key"} value={form.api_key} disabled={!!busy || probing} onChange={e => setForm({ ...form, api_key: e.target.value })}/><button className="icon-button" type="button" aria-label={reveal ? "隐藏 API Key" : "显示 API Key"} onClick={() => setReveal(!reveal)}>{reveal ? <EyeOff size={17}/> : <Eye size={17}/>}</button></div></label>
          <ModelPicker value={form} onChange={setForm} onProbe={() => void probeModels()} disabled={!!busy || probing} probing={probing}/>
          {formError && <div className="form-error" role="alert">{formError}</div>}
        </div>
        <div className="drawer-footer"><button type="button" className="button secondary" disabled={!!busy || probing} onClick={closeEditor}>取消</button><button type="submit" className="button primary" disabled={!!busy || probing}>{busy ? <LoaderCircle className="spin" size={16}/> : <Check size={16}/>}保存连接</button></div>
      </form>
    </Modal>}
    {deleting && <Modal label="删除连接" onClose={() => !busy && setDeleting(null)}><div className="dialog-icon"><Trash2 size={23}/></div><h2>删除 {deleting.name}？</h2><div className="dialog-actions"><button className="button secondary" disabled={!!busy} onClick={() => setDeleting(null)}>取消</button><button className="button danger" disabled={!!busy} onClick={async () => { if (await mutate(deleting.id, () => api.remove(deleting.id), "连接已删除")) setDeleting(null); }}>{busy ? <LoaderCircle className="spin" size={15}/> : null}删除</button></div></Modal>}
    {discard && <Modal label="放弃修改" onClose={() => setDiscard(false)}><div className="dialog-icon"><Pencil size={22}/></div><h2>放弃未保存的修改？</h2><div className="dialog-actions"><button className="button secondary" onClick={() => setDiscard(false)}>继续编辑</button><button className="button primary" onClick={() => { setDiscard(false); setForm(null); }}>放弃修改</button></div></Modal>}
  </div>;
}
