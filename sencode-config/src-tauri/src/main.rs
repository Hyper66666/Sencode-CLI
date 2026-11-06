#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use specta::Type;
use std::{path::PathBuf, process::Stdio, time::Duration};
use tauri::{path::BaseDirectory, Manager};
use tokio::{io::{AsyncReadExt, AsyncWriteExt}, process::Command, sync::Mutex};

#[derive(Debug, Clone, Serialize, Deserialize, Type)]
pub struct Connection {
    pub id: String, pub name: String, pub kind: String, pub model: String,
    pub base_url: String, pub protocol: String, pub models: Vec<String>,
    pub enabled_models: Vec<ConfiguredModel>, pub discovered_model_ids: Vec<String>,
}
#[derive(Debug, Clone, Serialize, Deserialize, Type)]
#[serde(rename_all = "camelCase")]
pub struct ModelCapabilities { pub vision_supported: bool }
#[derive(Debug, Clone, Serialize, Deserialize, Type)]
pub struct ConfiguredModel { pub id: String, pub label: Option<String>, pub capabilities: ModelCapabilities }
#[derive(Debug, Clone, Serialize, Deserialize, Type)]
pub struct Snapshot {
    pub connections: Vec<Connection>, pub current: String, pub database: String,
}
// Deliberately no Debug implementation: the password must never enter a log.
#[derive(Serialize, Deserialize, Type)]
pub struct ConnectionInput {
    pub id: String, pub name: String, pub base_url: String, pub protocol: String,
    pub model: String, pub api_key: String, pub existing: bool,
    pub enabled_models: Vec<ConfiguredModel>, pub discovered_model_ids: Vec<String>,
}
#[derive(Serialize, Deserialize, Type)]
pub struct ProbeInput { pub id: String, pub base_url: String, pub protocol: String, pub api_key: String, pub existing: bool }
#[derive(Debug, Serialize, Deserialize, Type)]
pub struct ProbeResult { pub model_ids: Vec<String>, pub truncated: bool }
#[derive(Deserialize)]
struct Response { ok: bool, data: Option<serde_json::Value>, code: Option<i64> }
struct Host { bridge: PathBuf, database: Option<String>, lock: Mutex<()> }

impl Host {
    async fn call<T: serde::de::DeserializeOwned>(&self, mut request: serde_json::Value) -> Result<T, String> {
        let _lock = self.lock.lock().await;
        if let Some(path) = &self.database { request["database"] = path.clone().into(); }
        let mut payload = serde_json::to_vec(&request).map_err(|_| "配置无效")?;
        if payload.len() > 65500 { return Err("配置内容过长".into()); }
        payload.push(b'\n');
        let mut cmd = Command::new(&self.bridge);
        cmd.stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::null()).kill_on_drop(true);
        #[cfg(windows)] cmd.creation_flags(0x08000000);
        let mut child = cmd.spawn().map_err(|_| "无法启动配置服务，请重新安装 sencode-config")?;
        let mut stdin = child.stdin.take().ok_or("配置服务不可用")?;
        let stdout = child.stdout.take().ok_or("配置服务不可用")?;
        let task = async {
            stdin.write_all(&payload).await.map_err(|_| "无法提交配置")?;
            stdin.shutdown().await.map_err(|_| "无法提交配置")?;
            drop(stdin);
            let mut output = Vec::new();
            stdout.take(2 * 1024 * 1024 + 1).read_to_end(&mut output).await.map_err(|_| "无法读取配置")?;
            if output.len() > 2 * 1024 * 1024 { return Err("配置列表过长".to_string()); }
            let _status = child.wait().await.map_err(|_| "配置服务异常退出")?;
            let response: Response = serde_json::from_slice(&output).map_err(|_| "配置服务响应无效")?;
            if !response.ok {
                return Err(match response.code.unwrap_or(0) {
                    2 => "请检查名称、地址、协议和模型",
                    5 => "连接或 API Key 不存在",
                    7 => "无法访问配置，或地址必须使用 HTTPS",
                    8 => "配置版本或连接类型不兼容",
                    12 => "配置正在使用，请稍后重试",
                    13 => "配置内容过长",
                    11 => "模型嗅探超时",
                    301 | 302 | 303 | 307 | 308 => "模型接口不允许重定向",
                    401 | 403 => "API Key 无效或没有模型目录权限",
                    404 => "没有找到模型目录，可手动添加模型",
                    429 => "请求过于频繁，请稍后重试",
                    10 => "模型目录格式无效",
                    _ => "保存失败，请检查配置是否被其他程序占用",
                }.into());
            }
            serde_json::from_value(response.data.ok_or("配置服务没有返回数据")?).map_err(|_| "配置服务响应字段无效".into())
        };
        let outcome = tokio::time::timeout(Duration::from_secs(25), task).await;
        payload.fill(0);
        outcome.map_err(|_| "配置服务超时，请重试".to_string())?
    }
}

#[tauri::command]
#[specta::specta]
async fn get_snapshot(host: tauri::State<'_, Host>) -> Result<Snapshot, String> {
    host.call(serde_json::json!({"action":"snapshot"})).await
}
#[tauri::command]
#[specta::specta]
async fn save_connection(host: tauri::State<'_, Host>, input: ConnectionInput) -> Result<Snapshot, String> {
    for (value, limit) in [(&input.id, 128), (&input.name, 128), (&input.base_url, 2048), (&input.model, 256), (&input.api_key, 8192)] {
        if value.len() > limit || value.contains(['\0', '\r', '\n']) { return Err("配置字段无效或过长".into()); }
    }
    if input.id.is_empty() || !input.id.bytes().all(|b| b.is_ascii_alphanumeric() || b"-_.".contains(&b)) || input.name.trim().is_empty() || input.model.trim().is_empty() {
        return Err("请填写名称和模型".into());
    }
    host.call(serde_json::json!({"action":"save", "input": input})).await
}
#[tauri::command]
#[specta::specta]
async fn select_connection(host: tauri::State<'_, Host>, id: String) -> Result<Snapshot, String> {
    host.call(serde_json::json!({"action":"select", "id":id})).await
}
#[tauri::command]
#[specta::specta]
async fn remove_connection(host: tauri::State<'_, Host>, id: String) -> Result<Snapshot, String> {
    host.call(serde_json::json!({"action":"remove", "id":id})).await
}
#[tauri::command]
#[specta::specta]
async fn probe_models(host: tauri::State<'_, Host>, input: ProbeInput) -> Result<ProbeResult, String> {
    host.call(serde_json::json!({"action":"probe", "input":input})).await
}

fn main() {
    let bindings = tauri_specta::Builder::<tauri::Wry>::new().commands(tauri_specta::collect_commands![get_snapshot, save_connection, select_connection, remove_connection, probe_models]);
    if std::env::args().any(|arg| arg == "--export-bindings") {
        bindings.export(specta_typescript::Typescript::default(), "../src/bindings.ts").expect("export command contract");
        return;
    }
    tauri::Builder::default()
        .invoke_handler(bindings.invoke_handler())
        .setup(|app| {
            let bridge = app.path().resolve("resources/sencode-config-bridge.exe", BaseDirectory::Resource)?;
            app.manage(Host { bridge, database: std::env::var("SENCODE_CONFIG_DATABASE").ok(), lock: Mutex::new(()) });
            Ok(())
        })
        .run(tauri::generate_context!()).expect("start sencode-config");
}
