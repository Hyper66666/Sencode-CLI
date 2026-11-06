# Next command and availability work

This is a design and source audit, dated 2026-11-04. It does not enable commands
or close an umbrella phase. Current-source observations are separate from the
installed `9e3d4980...` candidate and the combined candidate undergoing final
acceptance. Implementation follows that candidate freeze.

## Current surfaces

| Surface | Current source behavior | Remaining work |
| --- | --- | --- |
| Fullscreen `/` and `/help` | Registry supplies names, aliases, labels and enabled-command help; Enter only completes | Keep this behavior for every new command and argument picker |
| Scrolling `/help` | `view_help()` and the plain fallback remain separate text lists in `views.sg` / `main.sg` | Render the actual scrolling host's supported registry instead of maintaining another list |
| `/model`, `/connections` | Choose a saved target or next-request model; current requests retain their accepted target | `/model` description mentions reasoning levels although no reasoning selector is exposed; correct the description before claiming that selector |
| `/keys`, `/read`, `/queue` | Fullscreen-owned and enabled only by `tui_new`; generic registry disables them | Add user documentation for safe keymap paths/schema, Vim subset, focus and explicit cancellation |
| `/terminal`, `/term` | Windows capability gate, explicit user approval and independent pane; no model tool | Complete final-candidate acceptance and installation evidence; retain separate focus and explicit process-tree cleanup |
| `/config`, `/doctor`, `/memory` | Fullscreen frontend enables real read-only handlers | Learned memory and settings mutation remain unavailable; keep those limits visible |
| `/mcp` | Fullscreen registry disabled; top-level `sen mcp list/add/remove/doctor` and native stdio tools exist | Add a typed fullscreen projection and appropriate process approval; listing configuration is different from launching a server |
| `/diff` | Fullscreen registry disabled; native `git_diff` tool uses bounded protected Git argv | Reuse that executor through a host operation and add a read-only diff view |
| `/hooks`, `/plugin` | Named but disabled; no fullscreen implementation | Keep disabled until an extension child has its own contract, tests and capability evidence |
| Plan / Goal / controlled children | API-native enforcement exists; managed strict policy and exact token accounting are limited | Derive visible availability from negotiated guarantees and current policy, while retaining the execution host's final checks |

`src/runtime_adapter.sg` distinguishes native and managed guarantees. A saved
connection, successful model response or native permission setting must not
enable an unsupported managed mode. Missing model/account credentials do not
prevent local help, settings inspection, session metadata or the explicit user
terminal from working.

## One host-specific availability projection

Retain stable canonical command ids and aliases in the existing registry.
Descriptions, argument syntax, categories and fixed argument candidates remain
registry-owned. A host projection adds a small state per canonical command:

| State | Meaning | Menu / dispatch behavior |
| --- | --- | --- |
| `ready` | Handler and required host guarantees exist now | Discoverable and completable; later explicit Enter may dispatch |
| `blocked` | Handler exists, but current mode, focus, connection or platform prevents it | Show the concrete reason and an applicable remedy; no provider/tool request |
| `planned` | No qualified handler | Dimmed advanced discovery with an explicit unimplemented reason; never executable |

This projection is proposed, not a change to the existing diagnostic or
headless-output schema. The frontend owns display state; the execution host
owns provider guarantees, permissions, budgets and effects. Availability is
recomputed after target changes, policy changes and negotiated host updates.
Queued work revalidates at dispatch. A stale picker selection cannot reuse an
earlier connection's capabilities or an earlier confirmation's approval.

Canonical-name resolution does not grant availability. Unknown or disabled
slash input stays local and cannot become an ordinary provider prompt. The
host still validates the actual operation, even if the UI previously showed
`ready`. A backend rejection updates the displayed reason without silently
switching service, weakening Plan or changing the request's captured target.

Help is a view over this same projection for fullscreen and scrolling hosts.
Full-screen-only commands are disabled for scrolling; headless mode never
pretends it can answer a picker or approval. Busy-state metadata belongs to the
operation, not merely its top-level name: `/mcp list` can inspect local metadata,
whereas `/mcp doctor SERVER` starts code and needs an idle host plus approval.

## First follow-on implementation slice

1. Correct labels and document the implemented editor/terminal subset. Add
   registry-driven scrolling help and reason-specific disabled feedback.
2. Expose `/mcp list` as bounded, redacted local metadata. The current
   `management_mcp_config()` calls a path helper that creates `.sencode`; the
   fullscreen read-only listing needs a resolver that does not create files or
   directories, including in Plan. Missing configuration yields an empty list.
3. Add `/mcp doctor SERVER` as a separate explicitly approved operation: preview
   exact executable/argv/cwd and configuration identity, default to Cancel,
   discard previously queued confirmation input, then initialize and discover
   tools under existing bounds. Plan and read-only children reject launch.
   Config changes between preview and acceptance invalidate that approval.
4. Add `/diff` with unstaged/staged selection only after each path has executor
   evidence. Use argv and the existing Git filter/fsmonitor/textconv protections;
   preserve cancellation, output limits and draft/focus. File paths and diff
   contents are displayed as data. No restore or apply operation is implied.

MCP discovery stays cancellable and bounded while the composer remains owned
by the UI. Server stderr is diagnostic text, not protocol JSON. A server process
is reaped on cancellation or exit; an unknown cleanup result is not reported as
a successful diagnostic. Listing servers must not start them. Remote MCP,
OAuth, resources, prompts and elicitation remain separate capability work.

## Later extension slice

Keep hooks/plugins disabled while preparing an inspectable, versioned manifest
and explicitly trusted Sengoo workers. Installing, enabling or running an
extension is an effect, separate from showing its metadata. Project files and
skills cannot authorize an extension or enlarge permissions. Extension tool
requests use the normal policy, write queue, approval, budget and ledger paths.
Worker execution does not provide an OS sandbox. Direct execution of recovered
Claude JS/TS modules is outside the current umbrella scope.

## Acceptance before enabling a command

Each newly enabled operation requires a real handler, deterministic state tests
and a host check. Cover aliases, arguments, first-Enter completion, explicit
execution, disabled reasons, stale targets, busy-state behavior, Plan/child
restrictions, cancellation and resource cleanup. Verify the visible command
catalog against enabled handlers so a label alone cannot count as delivery.

For MCP, add a side-effect sentinel proving that list does not start or create
anything and that stale/denied/Plan diagnostics do not launch a server. For
Git views, preserve the existing hostile Git-config regressions and add a
non-repository case, binary/large changes and cancellation. For UI help, compare
fullscreen, scrolling and plain projections rather than requiring identical
capabilities across those hosts.

The final artifact's source/compiler/binary hashes, Windows console evidence
and package evidence remain separate from this design. A local fixture is not
a live-provider, clean-machine or independent-user trial.
