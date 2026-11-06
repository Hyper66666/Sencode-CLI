# sencode-config

Sencode CLI 的 Windows 配置切换工具。React + Tauri，白色简约界面。

## 使用

运行 `sencode-config.exe`。便携版中的 `resources` 目录需和 exe 保持相邻。

- 添加 API 地址、协议和 Key，点击 **嗅探模型**。
- 勾选多个模型，点击星标选择默认模型；图片按钮对应桌面的图片能力设置。
- 接口没有模型目录时，输入模型 ID，点击加号或 Enter 手动添加。
- 点击连接卡片上的 **使用** 切换默认 API，在卡片下拉框切换该 API 的默认模型。
- 支持 Chat Completions、Responses、Anthropic Messages。
- 嗅探只更新候选目录；不会自动启用模型、改默认模型或保存草稿。
- `Ctrl K` 搜索，`Ctrl N` 添加，`Ctrl Enter` 保存，`Esc` 关闭。

直接使用 CLI 的共享配置库和 Windows Credential Manager，没有独立的配置副本。
默认库为 `%USERPROFILE%\.sencode\local-sessions.sqlite3`，要求 shared contract v1 / schema 29。
旧版本数据库会被拒绝写入，需先由匹配的桌面版本协调升级。
已有官方账号可被选择；此工具不提供登录、账号编辑和删除，账号能否执行由 CLI 自身决定。
切换只影响未来请求。配置工具不会修改项目 `.sencode` 中的聊天记录。

API Key 不进入数据库、导出文件和命令行参数。编辑时留空保留原 Key。
导出含模型元数据，不含 Key；导入后需要重新输入 Key 并明确保存。
嗅探 GET `<API 地址>/models`，不跟随重定向，响应上限 1 MiB，最多读取 256 个模型。
远程地址要求 HTTPS；HTTP 仅允许 loopback。图片能力是用户配置，不会通过探测推断。

## 开发

需要 Node 24、Rust/MSVC、Sengoo 和 clang。运行成品仅需 Windows x64 和 WebView2。

```powershell
npm ci
# 使用匹配的 Sengoo 候选工具链；不会覆盖安装版 sen。
./scripts/build.ps1 -Compiler D:/Sengoo/target/bounded-request-build/debug/sgc.exe -SengooRoot D:/Sengoo -Clang C:/path/to/clang.exe
npm run desktop
```

`build.ps1` 编译 Sengoo bridge、构建前端和 Tauri，再生成独立便携目录及 zip。
`scripts/package.ps1 -Destination D:/SencodeConfig` 可将已构建的产物复制到指定目录；只覆盖带有自身标记的目录。
原生资源均随包携带，不依赖源码路径或开发工具。

React 通过生成的 tauri-specta bindings 调用 Tauri。Tauri 只启动包内的 Sengoo
bridge，使用有界 JSON stdin/stdout，Key 不放 argv；bridge 复用 CLI 状态、锁和凭据 API。
桌面 `enabledModels` / `discoveredModelIds` / `selectedModelId` 及模型能力保持兼容，
编辑时保留现有配置中的未知字段。

```powershell
npm test
node tests/ui.mjs  # 先 npm run dev；使用系统 Edge、明确标记的预览夹具
python tests/bridge_fixture.py src-tauri/resources/sencode-config-bridge.exe target/bridge-evidence.json
```

浏览器 `http://127.0.0.1:1432/?preview` 仅为内存视觉预览，标有“预览”，嗅探返回夹具。
普通浏览器不会假装已保存真实配置。原生隔离测试可设置 `SENCODE_CONFIG_DATABASE`
指向自己创建的临时库；不要在验证中使用用户真实连接或 Key。
验证范围及产物哈希见 `verification.md`。
