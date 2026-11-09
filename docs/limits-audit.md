# Sencode CLI 限制审计

已对照两个本地源码快照的请求循环、子代理、压缩、解析、工具输出和滚动实现。
建议优先消除“累计次数或历史数量一到就停”的限制，把资源控制放在活动并发、
驻留内存、输出日志及恢复分页上。下表明确区分本轮实现和后续建议。

| 优先级 | 当前限制 | 处理结论 |
| --- | --- | --- |
| 已实施 | 默认 50 次模型请求，旧 Goal 恢复也保留默认上限 | 前台、Goal、子代理、会诊和后台默认不限请求次数；保留累计用量和用户可选的显式预算。旧记录没有来源标记时，无法区分主动设置的 50 与旧默认 50，按旧默认迁移。 |
| 高 | 界面只缓存 512 条 / 4 MiB | 反向分页读取项目历史，缓存上限不再限制能浏览的历史；尚未实现。 |
| 高 | stdout/stderr 各捕获 1 MiB，整文件读取 1 MiB | 完整输出落盘，配合日志范围读取、文件分段读取和搜索分页；尚未实现。 |
| 高 | 默认上下文 256 Ki Token / 80% 压缩，另有 640 KiB 字节触发；恢复最多 1000 条 / 768 KiB | 拆分模型容量、传输内存和恢复分页，校准 Token 估算，为没有 checkpoint 的超大旧会话分段建立摘要；尚未实现。 |
| 中高 | 一轮保留 32 个子任务，回答 64 KiB，子代理历史 768 KiB | 归档已结束任务、报告分页、子代理复用压缩；尚未实现。嵌套委派需先补取消、权限和写许可组合验证。 |
| 中高 | 命令默认 120 秒、最多 600 秒，网络空闲 90 秒，后台默认 1 小时 | 区分空闲与总时限，增加长命令转后台及日志跟踪；尚未实现。 |
| 中 | 并行默认 4 路 / 每连接 2 路，底层配置最多 8 路 | 开放配置并保留背压和 FIFO 写入；尚未开放公共配置。 |
| 中高 | SSE 1 MiB / JSON 65,536 节点 / 深度 64 | 投影必要字段，跳过无关元数据，再按峰值内存评估可配置预算；不能把总节点数、递归深度和缓存条目混为一谈。 |
| 低 | 用户主动指定的请求预算最多 10,000 | 可以取消这个额外数值上界，保留整数和溢出校验。默认 0 已不限制请求总数。 |
| 中 | TUI 布局尺寸最多 500 列 / 300 行，草稿 64 KiB | 超大终端应把实际几何与布局预算分开，避免尺寸裁剪与帧校验冲突；大段粘贴可转成可查看的附件，而不是无限扩张编辑缓冲。未在本轮取消这两项上限。 |

应保留执行权与 fencing、工具去重、未知副作用不重放、Plan 和审批、进程树回收、
有界 I/O 与磁盘配额，以及用户要求的失败重试最多五次。

请求次数与参考实现的 turn 不是完全相同的计量单位。参考实现也有局部限制：
例如 CC 的实验性 fork 子代理定义 `maxTurns: 200`，自动压缩连续失败三次后熔断。
不能据此声称参考工具完全没有上限。

以下为源码依据与细项；所有“Next / Consider / Still”均为待实施项。

Scope: Claude Code 2.1.88 and Grok Build `SOURCE_REV`
559751fdcec02d413e4c57c8832ab275e4f44980. This reviews the related request,
subagent, compaction, JSON/SSE, tool and viewport paths, not every line or every
remote account runtime. Implementation/testing status is in the candidate
verification; this table distinguishes actual changes from follow-up work.

| Area | Reference finding | Sencode decision |
| --- | --- | --- |
| Request count | CC `query.ts` checks optional `maxTurns`; Grok `session/acp_session_impl/turn.rs` checks optional `max_turns`. A reference turn is not necessarily identical to Sencode's shared request unit. | Remove the implicit 50 cap from foreground, Goal, children, consultation and background launch. Omission/zero means unlimited; explicit limits remain optional. |
| Old Goal checkpoint | Defaults should not become new user instructions on recovery. | Remove old unmarked default 50 without resetting usage/checks. New explicit limits carry provenance through archive import. |
| Compaction | Continuation state and execution budget are separate. | Successful compression continues without a default call cap; an explicit budget pause shows counts and retains context. Context failure has a separate stage. |
| JSON/SSE | CC uses `JSON.parse`; Grok uses `serde_json::from_str` without fixed total-node caps on those paths. serde_json's default recursion guard is 128 levels. | The earlier fix replaced legacy 4096-node response parsing. Keep current explicit 65536-node / 1 MiB / depth-64 event admission. Consider projecting/skipping optional metadata before raising memory admission. |
| Responses retention | Output index, parsed JSON nodes and actual retained output are different quantities. | Still index <=4096, 64 retained items/tool calls, 256 KiB per retained item / 768 KiB aggregate. Next separate sparse identity validation from retained size, project optional metadata and extend supported legal event shapes. Preserve call-ID conflict detection and validated tool execution. |
| Context capacity | CC `autoCompact.ts` uses model capacity, summary output reservation (up to 20000 tokens) and buffers. | Sencode's local byte/3 estimate, 640 KiB trigger and 1000-message / 768 KiB recovery admission are separate from the 256 Ki-token model setting. Next calibrate estimates and page recovery, preserving complete tool pairs. Provider capacity cannot be removed by the client. |
| Scroll/render | CC `useVirtualScroll.ts` caps mounted items at 300, with overscan/quantization. `ScrollBox.tsx` tracks sticky-bottom separately. Grok has wheel-burst/resize/anchor tests and cached viewport rendering. | Keep bounded visible-row work and overlap shifts; fix invalidation, height-only reflow and temporary handle allocation. Memory caps must not be confused with durable history limits. |
| Resize | Cached cells are invalid after geometry transitions even if their logical text is unchanged. | Geometry-check delivery, redraw every row on invalidation and schedule one settled recovery paint. Resume zero-write idle. |
| Jump to latest | CC provides `scrollToBottom()` and sticky state; Grok distinguishes following from reading history. | Centered muted triangle in the composer gap; click follows current tail without submitting or changing a draft. |
| Transcript cache | Virtualization limits mounted work separately from durable storage. | Still 512 messages / 4 MiB cached in Sencode. Next priority: backward pagination from project history. Removing the cache bound alone would increase memory/reflow costs. UI eviction does not delete durable history. |
| Tool output | CC Bash inline length defaults to 30000, configurable up to 150000 (`utils/shell/outputLimits.ts`), separate from persisted output. Grok inline defaults are 40000 bytes / 20000 chars, MCP 20000 bytes, with separate file retention and a disk-growth cap. | Keep bounded inline captures; Sencode already captures 1 MiB per stdout/stderr. Next add file-backed full output and explicit retrieval instead of unbounded inline data. |
| File reads/search | Reference tools provide bounded/ranged reads and search. | Keep 1 MiB whole-file and bounded-search admission; next add line/byte ranges and result pagination. Large-file access should not require a whole-file copy. |
| Child lifetime/size | References distinguish live slots, retained results and optional turn limits. | Still one-level delegation, 32 controller task records, 64 KiB child answers. Optimize through archived terminal tasks, paged reports and nested ownership tests before relaxing these limits. |
| Parallelism | Capacity is backpressure, distinct from total successful requests. | Keep default global 4 / per-provider 2 and FIFO workspace writes. Next expose existing scheduler configuration. |
| Timeouts | Grok backgrounds long foreground commands and separately bounds background lifetime, drain/reap and output-file growth. | Current commands default 120 s (explicit up to 600 s), network idle 90 s, background jobs 1 h. Next distinguish idle/total lifetime and support explicit background handoff; preserve bounded cancellation and reaping. |
| Retry | Failed-attempt retry and successful-task length are separate. | Keep the user's five retries per failed model request; remove default total-request cap. Never replay a completed/unknown side effect automatically. |
| Permissions/recovery | Execution, interaction and task lifecycle remain distinct in both references. | Keep fencing/single executor, tool deduplication, Plan constraints, approval focus barrier and process-tree quiescence. These protect execution correctness. |

Reference paths reviewed:

- CC: `src/query.ts`, `main.tsx`, `tools/AgentTool/runAgent.ts`,
  `loadAgentsDir.ts`, `forkSubagent.ts`; SDK `core/streaming.mjs`;
  `utils/json.ts`; `services/compact/autoCompact.ts`, `compact.ts`;
  `hooks/useVirtualScroll.ts`; `ink/components/ScrollBox.tsx`;
  `components/ScrollKeybindingHandler.tsx`; `tools/BashTool/utils.ts`.
  Bash length configuration: `utils/shell/outputLimits.ts`.
- Grok: `crates/codegen/xai-grok-sampler/src/client.rs`,
  `stream/responses.rs`; shell `session/acp_session_impl/turn.rs`,
  `agent/config.rs`, `agent/subagent/mod.rs`, `mvp_agent/subagent_spawn.rs`;
  tools `src/lib.rs`, `computer/local/terminal.rs`, `util/mcp_truncate.rs`;
  pager `scrollback/state/mod.rs`, `scrollback/scrollback_pane.rs`,
  `app/app_view.rs` (off-screen render cache eviction), plus scroll, resize,
  follow-mode and selection tests.

All numbers refer to these paths/snapshots. CC's 8 KiB/50-entry JSON helper
thresholds control caching; Grok's 128-level JSON guard is depth. Neither is
a 4096-node response ceiling. The references also have real resource limits.
